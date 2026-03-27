from pathlib import Path

from orchestrator import get_orchestrator
from project import scan_project_files, get_current_version_dir
from state import StateManager
from contracts_write import build_write_payload


ALLOWED_FILE_OPERATIONS = {'create', 'overwrite', 'append'}


def resolve_safe_path(project_root: Path, relative_path: str) -> Path:
    candidate = (project_root / relative_path).resolve()
    project_root_resolved = project_root.resolve()
    if candidate == project_root_resolved or project_root_resolved in candidate.parents:
        return candidate
    raise RuntimeError(f'非法写入路径，已超出项目目录: {relative_path}')


def apply_file_blocks(project_root: Path, file_blocks: list, dry_run: bool = False):
    written = []
    for block in file_blocks:
        operation = block['operation']
        if operation not in ALLOWED_FILE_OPERATIONS:
            raise RuntimeError(f'不支持的文件操作类型: {operation}')
        full_path = resolve_safe_path(project_root, block['path'])
        action = operation
        if not dry_run:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if operation == 'append':
                existing = full_path.read_text(encoding='utf-8') if full_path.exists() else ''
                full_path.write_text(existing + ('\n' if existing else '') + block['content'], encoding='utf-8')
            elif operation == 'overwrite':
                full_path.write_text(block['content'], encoding='utf-8')
            else:
                if full_path.exists():
                    full_path.write_text(block['content'], encoding='utf-8')
                    action = 'overwrite'
                else:
                    full_path.write_text(block['content'], encoding='utf-8')
                    action = 'create'
        else:
            if operation == 'create' and full_path.exists():
                action = 'overwrite'
        written.append({'path': block['path'], 'action': action})
    return written


def run_write(project_root: Path, config: dict, task_id: str | None = None, dry_run: bool = False):
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录')

    state = StateManager(version_dir)
    if state.data.get('status') not in {'confirmed', 'review_passed', 'needs_fix'}:
        raise RuntimeError(f"当前状态不允许 write: {state.data.get('status')}")

    tasks = state.data.get('tasks', [])
    task_id = task_id or state.data.get('current_task')
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task:
        raise RuntimeError(f'找不到任务: {task_id}')

    dev_plan_file = version_dir / 'docs' / 'DEV_PLAN.md'
    if not dev_plan_file.exists():
        raise RuntimeError('找不到 DEV_PLAN.md，请先执行 analyze')

    dev_plan = dev_plan_file.read_text(encoding='utf-8')
    project_files = scan_project_files(project_root)
    context = '\n\n'.join([
        f"=== 文件: {f['path']} ===\n{f['content'][:2000]}" for f in project_files[:8]
    ])

    state.data['status'] = 'writing'
    state.data['last_action'] = 'write'
    state.data['last_error'] = None
    state.save()

    orchestrator = get_orchestrator(config)
    result = orchestrator.run('write', build_write_payload(project_root, version_dir, task, dev_plan, context))

    if result.get('status') == 'not_implemented':
        raise RuntimeError(result.get('message', 'write 编排器未实现'))

    file_blocks = result.get('file_operations', [])
    if not file_blocks:
        raise RuntimeError('write 未返回任何 file_operations')

    written = apply_file_blocks(project_root, file_blocks, dry_run=dry_run)
    state.data['status'] = 'confirmed' if dry_run else 'written'
    state.data['last_orchestration'] = config.get('adapters', {}).get('orchestration', 'local_llm') or 'local_llm'
    state.data['last_result_format'] = result.get('result_format', 'unknown')
    state.data['last_summary'] = result.get('summary', '')
    state.save()

    # 自动 commit write 阶段的改动
    git_result = auto_commit(project_root, f'feat: 实现代码')
    if git_result.get('error'):
        print(f"⚠️ Git commit 警告: {git_result['error']}")

    return {
        'task_id': task['id'],
        'task_name': task['name'],
        'files': written,
        'count': len(written),
        'orchestration': state.data['last_orchestration'],
        'result_format': state.data['last_result_format'],
        'dry_run': dry_run,
        'summary': state.data['last_summary'],
        'git': git_result,
    }
