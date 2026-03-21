import re

from llm import OpenAICompatibleLLM
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


class LocalLLMOrchestrator(BaseOrchestrator):
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
        raise RuntimeError(f'LocalLLMOrchestrator 暂不支持 action: {action}')

    def _parse_or_fallback(self, action: str, raw_text: str, fallback_builder):
        try:
            return parse_json_result(raw_text, action)
        except ResultParseError:
            return fallback_builder(raw_text)

    def _run_analyze(self, payload: dict) -> dict:
        llm = OpenAICompatibleLLM(self.config)
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
        llm = OpenAICompatibleLLM(self.config)
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
        llm = OpenAICompatibleLLM(self.config)
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
        llm = OpenAICompatibleLLM(self.config)
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
        llm = OpenAICompatibleLLM(self.config)
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
