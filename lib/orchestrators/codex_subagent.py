import os
import re

import requests

from orchestrators.base import BaseOrchestrator
from prompt_loader import load_prompt
from result_parser import ResultParseError, parse_json_result

WRITE_SYSTEM_PROMPT = load_prompt('write_system.md')
REVIEW_SYSTEM_PROMPT = load_prompt('review_system.md')
ANALYZE_SYSTEM_PROMPT = load_prompt('analyze_system.md')
COMPREHENSIVE_REVIEW_SYSTEM_PROMPT = load_prompt('comprehensive_review_system.md')


def parse_file_blocks(code_result: str):
    files = []
    file_sections = re.split(r'\n---\s*\n|\n(?=### FILE:)', code_result)
    for section in file_sections:
        section = section.strip()
        if not section:
            continue
        file_match = re.search(r'###\s*FILE:\s*(.+?)(?:\n|$)', section)
        if not file_match:
            continue
        filepath = file_match.group(1).strip()
        op_match = re.search(r'\*\*操作类型\*\*:\s*(\w+)', section)
        operation = op_match.group(1).lower() if op_match else 'create'
        desc_match = re.search(r'\*\*描述\*\*:\s*(.+?)(?:\n|$)', section)
        description = desc_match.group(1).strip() if desc_match else ''
        code_match = re.search(r'```[\w]*\n([\s\S]*?)```', section)
        if not code_match:
            continue
        content = code_match.group(1).strip()
        if not content:
            continue
        files.append({
            'path': filepath,
            'operation': operation,
            'description': description,
            'content': content,
        })
    return files


class _CodexTaskLLM:
    """Codex skill 编排器专用的 LLM 调用器。

    从 config.codex 读取 base_url / api_key / model。
    不依赖环境变量（除非配置中未指定 fallback 时才读 env）。
    """

    def __init__(self, config: dict):
        from codex_config import detect_codex_llm

        ccfg = config.get('codex', {})
        self.base_url = ccfg.get('base_url', '').rstrip('/')
        self.api_key = ccfg.get('api_key', '')
        self.model = ccfg.get('model', '')

        # fallback: 也支持从环境变量读取
        if not self.base_url:
            self.base_url = os.getenv('DTFLOW_CODEX_BASE_URL', '').rstrip('/')
        if not self.api_key:
            self.api_key = os.getenv('DTFLOW_CODEX_API_KEY', '')
        if not self.model:
            self.model = os.getenv('DTFLOW_CODEX_MODEL', '')

        # Fallback: 自动从 Codex/OpenAI-compatible 配置读取
        if not all([self.base_url, self.api_key, self.model]):
            oc = detect_codex_llm()
            if not self.base_url:
                self.base_url = oc.get('base_url', '')
            if not self.api_key:
                self.api_key = oc.get('api_key', '')
            if not self.model:
                self.model = oc.get('model', '')

        self.timeout = ccfg.get('timeout_seconds', 900)

    def validate(self):
        missing = []
        if not self.base_url:
            missing.append('base_url')
        if not self.api_key:
            missing.append('api_key')
        if not self.model:
            missing.append('model')
        if missing:
            raise RuntimeError(
                f'codex 编排器 LLM 配置缺失: {", ".join(missing)}。'
                '请在 config.json 的 codex 字段中配置 base_url / api_key / model，'
                '或设置环境变量 DTFLOW_CODEX_BASE_URL / DTFLOW_CODEX_API_KEY / DTFLOW_CODEX_MODEL。'
            )

    def chat(self, system_prompt: str, user_prompt: str,
             max_tokens: int = 8192, temperature: float = 0.4) -> str:
        self.validate()
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': False,
        }
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=min(self.timeout, 600),
        )
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']


class CodexSubagentOrchestrator(BaseOrchestrator):
    """Codex 子任务编排器。

    与 LocalLLMOrchestrator 结构相同，但使用 config.codex 中的独立
    base_url / api_key / model 配置，允许在 Codex skill 内直接调用
    任意 OpenAI-compatible 模型接口。

    如果 config.codex 中只提供了 model，编排器会在
    validate 阶段提醒补充 base_url 和 api_key。
    """

    def run(self, action: str, payload: dict) -> dict:
        if action == 'analyze':
            return self._run_analyze(payload)
        if action == 'write':
            return self._run_write(payload)
        if action == 'review':
            return self._run_review(payload)
        if action == 'fix':
            return self._run_fix(payload)
        if action == 'comprehensive_review':
            return self._run_comprehensive_review(payload)
        raise RuntimeError(f'CodexSubagentOrchestrator 暂不支持 action: {action}')

    def _parse_or_fallback(self, action: str, raw_text: str, fallback_builder):
        try:
            return parse_json_result(raw_text, action)
        except ResultParseError:
            return fallback_builder(raw_text)

    def _make_llm(self) -> _CodexTaskLLM:
        return _CodexTaskLLM(self.config)

    def _run_analyze(self, payload: dict) -> dict:
        llm = self._make_llm()
        user_prompt = f"""请根据以下需求和项目上下文，输出完整开发方案：

## 需求文档

{payload['requirements']}

## 项目上下文

{payload['context']}
"""
        raw_text = llm.chat(ANALYZE_SYSTEM_PROMPT, user_prompt, max_tokens=16384, temperature=0.4)

        def fallback(text: str):
            return {
                'status': 'success',
                'action': 'analyze',
                'plan_markdown': text,
                'summary': 'fallback: markdown plan',
                'tasks': [],
                'result_format': 'markdown_plan',
                'warnings': ['analyze 使用了 markdown fallback，建议升级为 JSON 输出'],
                'errors': [],
            }

        result = self._parse_or_fallback('analyze', raw_text, fallback)
        result.setdefault('plan_markdown', raw_text)
        return result

    def _run_write(self, payload: dict) -> dict:
        llm = self._make_llm()
        task = payload['task']
        user_prompt = f"""当前任务：[{task['id']}] {task['name']}

输出文件：{task.get('output_files')}
依赖：{task.get('dependencies')}

## 开发计划
{payload['dev_plan'][:6000]}

## 项目上下文
{payload['context']}
"""
        raw_text = llm.chat(WRITE_SYSTEM_PROMPT, user_prompt, max_tokens=16384, temperature=0.3)

        def fallback(text: str):
            ops = parse_file_blocks(text)
            return {
                'status': 'success',
                'action': 'write',
                'summary': 'fallback: file blocks',
                'file_operations': ops,
                'result_format': 'file_blocks',
                'warnings': ['write 使用了 FILE block fallback，建议升级为 JSON 输出'],
                'errors': [],
                'raw_text': text,
            }

        result = self._parse_or_fallback('write', raw_text, fallback)
        result.setdefault('raw_text', raw_text)
        return result

    def _run_review(self, payload: dict) -> dict:
        llm = self._make_llm()
        task = payload['task']
        user_prompt = f"""请审查以下代码：

## 任务
[{task['id']}] {task['name']}

## 开发计划
{payload['dev_plan'][:4000]}

## 代码
{payload['code']}
"""
        raw_text = llm.chat(REVIEW_SYSTEM_PROMPT, user_prompt, max_tokens=12288, temperature=0.2)

        def fallback(text: str):
            passed = '❌ 不通过' not in text
            return {
                'status': 'success',
                'action': 'review',
                'summary': 'fallback: markdown review',
                'passed': passed,
                'score': 7 if passed else 5,
                'issues': [],
                'result_format': 'markdown_review',
                'warnings': ['review 使用了 markdown fallback，建议升级为 JSON 输出'],
                'errors': [],
                'raw_text': text,
            }

        result = self._parse_or_fallback('review', raw_text, fallback)
        result.setdefault('raw_text', raw_text)
        return result

    def _run_fix(self, payload: dict) -> dict:
        llm = self._make_llm()
        task = payload['task']
        user_prompt = f"""请根据以下审查报告修复代码：

## 当前任务
[{task['id']}] {task['name']}

## 开发计划
{payload['dev_plan'][:5000]}

## 项目上下文
{payload['context']}

## 审查报告
{payload['review_feedback']}
"""
        raw_text = llm.chat(WRITE_SYSTEM_PROMPT, user_prompt, max_tokens=16384, temperature=0.2)

        def fallback(text: str):
            ops = parse_file_blocks(text)
            return {
                'status': 'success',
                'action': 'fix',
                'summary': 'fallback: file blocks',
                'file_operations': ops,
                'result_format': 'file_blocks',
                'warnings': ['fix 使用了 FILE block fallback，建议升级为 JSON 输出'],
                'errors': [],
                'raw_text': text,
            }

        result = self._parse_or_fallback('fix', raw_text, fallback)
        result.setdefault('raw_text', raw_text)
        return result

    def _run_comprehensive_review(self, payload: dict) -> dict:
        llm = self._make_llm()
        system_prompt = payload.get('system_prompt', COMPREHENSIVE_REVIEW_SYSTEM_PROMPT)
        user_prompt = f"""请对以下项目进行全面审查：

{payload['user_content']}
"""
        raw_text = llm.chat(system_prompt, user_prompt, max_tokens=16384, temperature=0.2)

        def fallback(text: str):
            passed = '不通过' not in text and '❌' not in text
            return {
                'status': 'success',
                'action': 'comprehensive_review',
                'summary': 'fallback: markdown review',
                'passed': passed,
                'score': 8 if passed else 5,
                'issues': [],
                'result_format': 'markdown_review',
                'warnings': ['comprehensive_review 使用了 markdown fallback，建议升级为 JSON 输出'],
                'errors': [],
                'raw_text': text,
            }

        result = self._parse_or_fallback('comprehensive_review', raw_text, fallback)
        result.setdefault('raw_text', raw_text)
        return result
