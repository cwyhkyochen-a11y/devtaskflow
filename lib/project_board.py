from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


DEFAULT_PROJECTS_FILE = 'PROJECTS.md'


def now_date() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def find_workspace_root(start: Path | None = None) -> Path:
    origin = (start or Path.cwd()).resolve()
    current = origin
    last_projects_match = None
    while current != current.parent:
        if (current / 'AGENTS.md').exists():
            return current
        if (current / DEFAULT_PROJECTS_FILE).exists():
            last_projects_match = current
        current = current.parent
    return last_projects_match or origin


def load_projects(board_path: Path) -> list[dict]:
    if not board_path.exists():
        return []
    text = board_path.read_text(encoding='utf-8')
    marker = '<!-- DTFLOW_PROJECTS_JSON\n'
    end_marker = '\nDTFLOW_PROJECTS_JSON_END -->'
    if marker not in text or end_marker not in text:
        return []
    payload = text.split(marker, 1)[1].split(end_marker, 1)[0]
    return json.loads(payload)


def save_projects(board_path: Path, projects: list[dict]):
    board_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '# DevTaskFlow Project Index',
        '',
        'Codex 版 DevTaskFlow 维护的项目索引。',
        '',
        '| 序号 | 项目名 | 状态 | 最新版本 | 项目目录 | 最后更新 | 备注 |',
        '|---|---|---|---|---|---|---|',
    ]
    for idx, project in enumerate(projects, start=1):
        lines.append(
            f"| {idx} | {project['name']} | {project.get('status', '规划中')} | {project.get('current_version', '-')} | `{project['path']}` | {project.get('updated_at', '-')} | {project.get('note', '')} |"
        )
    lines.extend([
        '',
        '<!-- DTFLOW_PROJECTS_JSON',
        json.dumps(projects, ensure_ascii=False, indent=2),
        'DTFLOW_PROJECTS_JSON_END -->',
        '',
    ])
    board_path.write_text('\n'.join(lines), encoding='utf-8')


def register_project(workspace_root: Path, name: str, path: str, note: str = ''):
    board_path = workspace_root / DEFAULT_PROJECTS_FILE
    projects = load_projects(board_path)
    for project in projects:
        if project['name'] == name or project['path'] == path:
            return project
    project = {
        'name': name,
        'path': path,
        'status': '已创建',
        'current_version': '-',
        'updated_at': now_date(),
        'note': note,
    }
    projects.append(project)
    save_projects(board_path, projects)
    return project


def update_project(workspace_root: Path, name: str, **updates):
    board_path = workspace_root / DEFAULT_PROJECTS_FILE
    projects = load_projects(board_path)
    found = None
    for project in projects:
        if project['name'] == name:
            project.update(updates)
            project['updated_at'] = now_date()
            found = project
            break
    if not found:
        raise RuntimeError(f'项目不存在: {name}')
    save_projects(board_path, projects)
    return found
