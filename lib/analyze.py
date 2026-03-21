from pathlib import Path
import re

from orchestrator import get_orchestrator
from tasks import parse_tasks_from_plan, normalize_tasks
from project import scan_project_files, get_current_version_dir
from state import StateManager


def _extract_design_system(plan_markdown: str) -> str | None:
    """从 plan_markdown 中提取设计系统章节内容。"""
    # 匹配 ## 设计系统 到下一个 ## 或文件末尾
    pattern = r'(## 设计系统\s*\n)(.*?)(?=\n## |\Z)'
    match = re.search(pattern, plan_markdown, re.DOTALL)
    if match:
        content = match.group(2).strip()
        if content:
            return f'# 设计系统规范\n\n{content}\n'
    return None


def run_analyze(project_root: Path, config: dict):
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录，请先准备版本目录')

    req_file = version_dir / 'docs' / 'REQUIREMENTS.md'
    if not req_file.exists():
        raise RuntimeError(f'找不到需求文档: {req_file}')

    requirements = req_file.read_text(encoding='utf-8')
    project_files = scan_project_files(project_root)
    context = '\n\n'.join([
        f"=== 文件: {f['path']} ===\n{f['content'][:2000]}" for f in project_files[:10]
    ])

    state = StateManager(version_dir)
    if not state.data:
        state.init(version_dir.name)
    state.data['status'] = 'analyzing'
    state.data['last_action'] = 'analyze'
    state.data['last_error'] = None
    state.save()

    orchestrator = get_orchestrator(config)
    result = orchestrator.run('analyze', {
        'requirements': requirements,
        'context': context,
        'project_root': str(project_root),
        'version_dir': str(version_dir),
    })

    plan_markdown = result.get('plan_markdown', '')
    if not plan_markdown:
        raise RuntimeError('analyze 未返回 plan_markdown')

    plan_file = version_dir / 'docs' / 'DEV_PLAN.md'
    plan_file.write_text(plan_markdown, encoding='utf-8')

    # 提取设计系统章节，写入 DESIGN_SYSTEM.md
    design_system_content = _extract_design_system(plan_markdown)
    if design_system_content:
        ds_file = version_dir / 'docs' / 'DESIGN_SYSTEM.md'
        ds_file.write_text(design_system_content, encoding='utf-8')
        print(f'   设计系统规范已写入: {ds_file}')

    tasks = normalize_tasks(result.get('tasks', [])) if result.get('tasks') else parse_tasks_from_plan(plan_markdown)
    if not tasks:
        raise RuntimeError('analyze 未返回可用任务列表')

    state.data['tasks'] = tasks
    state.data['status'] = 'pending_confirm'
    state.data['last_orchestration'] = config.get('adapters', {}).get('orchestration', 'local_llm') or 'local_llm'
    state.data['last_result_format'] = result.get('result_format', 'unknown')
    state.data['last_summary'] = result.get('summary', '')
    state.save()

    return {
        'plan_file': str(plan_file),
        'tasks': tasks,
        'task_count': len(tasks),
        'orchestration': state.data['last_orchestration'],
        'result_format': state.data['last_result_format'],
        'summary': state.data['last_summary'],
    }
