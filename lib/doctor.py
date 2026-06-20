from pathlib import Path
from git_utils import check_git_installed
from config import find_project_root


def run_doctor(start: Path | None = None):
    root = find_project_root(start)
    checks = []

    if root:
        checks.append(('project_root', True, str(root)))
        checks.append(('config', (root / '.dtflow' / 'config.json').exists(), '.dtflow/config.json'))
        checks.append(('versions_dir', (root / 'versions').exists(), 'versions/'))
    else:
        checks.append(('project_root', False, '未找到 .dtflow/config.json'))

    checks.append(('codex_mode', True, '使用当前 Codex 会话；不需要单独模型配置'))

    return checks
