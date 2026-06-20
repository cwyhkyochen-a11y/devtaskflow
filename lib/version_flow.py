from __future__ import annotations

from datetime import datetime
from pathlib import Path

from project_board import find_workspace_root, update_project
from state import StateManager


def now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def create_version(project_root: Path, config: dict, version: str, mode: str, requirements_text: str | None = None):
    versions_dir = project_root / config['pipeline'].get('versions_dir', 'versions')
    version_dir = versions_dir / version
    docs_dir = version_dir / 'docs'
    if version_dir.exists():
        raise RuntimeError(f'版本已存在: {version}')

    docs_dir.mkdir(parents=True, exist_ok=False)
    state = StateManager(version_dir)
    state.data.update({
        'version': version,
        'status': 'created',
        'mode': mode,
        'architecture_confirmed': False,
        'current_task': None,
        'tasks': [],
        'created_at': now_iso(),
        'updated_at': now_iso(),
    })
    state.save()

    req_file = docs_dir / 'REQUIREMENTS.md'
    if not req_file.exists():
        content = requirements_text.strip() if requirements_text and requirements_text.strip() else '# REQUIREMENTS\n\n请补充本版本需求。\n'
        if not content.startswith('#'):
            content = '# REQUIREMENTS\n\n' + content + '\n'
        req_file.write_text(content, encoding='utf-8')

    configured_workspace = config.get('project', {}).get('workspace_root')
    workspace_root = Path(configured_workspace).resolve() if configured_workspace else find_workspace_root(project_root)
    project_name = config['project']['name']
    update_project(
        workspace_root,
        project_name,
        status='迭代中' if mode == 'iterate' else '新建中',
        current_version=version,
        note=f"通过 dtflow start-version 启动{version}（{mode}）",
    )

    return {
        'version_dir': str(version_dir),
        'requirements_file': str(req_file),
        'mode': mode,
    }
