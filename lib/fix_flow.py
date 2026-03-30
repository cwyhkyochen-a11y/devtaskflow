from pathlib import Path

from git_utils import auto_commit
from orchestrator import get_orchestrator
from project import scan_project_files, get_current_version_dir
from state import StateManager
from write_flow import apply_file_blocks
from contracts_fix import build_fix_payload


def run_fix(project_root: Path, config: dict):
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录')

    state = StateManager(version_dir)
    if state.data.get('status') not in {'needs_fix', 'failed'}:
        raise RuntimeError(f"当前状态不允许 fix: {state.data.get('status')}")

    task_id = state.data.get('current_task')
    tasks = state.data.get('tasks', [])
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise RuntimeError('找不到当前任务')

    review_file = version_dir / 'docs' / f'REVIEW_TASK_{task_id}.md'
    dev_plan_file = version_dir / 'docs' / 'DEV_PLAN.md'
    if not review_file.exists():
        raise RuntimeError('找不到审查报告')
    if not dev_plan_file.exists():
        raise RuntimeError('找不到 DEV_PLAN.md')

    review_feedback = review_file.read_text(encoding='utf-8')
    dev_plan = dev_plan_file.read_text(encoding='utf-8')
    project_files = scan_project_files(project_root, limit=20)
    context = '\n\n'.join([
        f"=== 文件: {f['path']} ===\n{f['content'][:2000]}" for f in project_files[:8]
    ])

    state.data['status'] = 'fixing'
    state.data['last_action'] = 'fix'
    state.data['last_error'] = None
    state.save()

    orchestrator = get_orchestrator(config)
    result = orchestrator.run('fix', build_fix_payload(project_root, version_dir, task, dev_plan, context, review_feedback))

    if result.get('status') == 'not_implemented':
        raise RuntimeError(result.get('message', 'fix 编排器未实现'))

    file_blocks = result.get('file_operations', [])
    if not file_blocks:
        raise RuntimeError('fix 未返回任何 file_operations')

    written = apply_file_blocks(project_root, file_blocks)
    state.data['status'] = 'written'
    state.data['last_orchestration'] = config.get('adapters', {}).get('orchestration', 'local_llm') or 'local_llm'
    state.data['last_result_format'] = result.get('result_format', 'unknown')
    state.data['last_summary'] = result.get('summary', '')
    state.save()

    # 自动 commit fix 阶段的改动
    git_result = auto_commit(project_root, 'fix: 修复审查问题')
    if git_result.get('error'):
        print(f"⚠️ Git commit 警告: {git_result['error']}")

    return {
        'task_id': task['id'],
        'task_name': task['name'],
        'files': written,
        'count': len(written),
        'orchestration': state.data['last_orchestration'],
        'result_format': state.data['last_result_format'],
        'summary': state.data['last_summary'],
        'git': git_result,
    }
