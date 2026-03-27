import os
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

    checks.append(('env:DTFLOW_LLM_BASE_URL', bool(os.getenv('DTFLOW_LLM_BASE_URL')), 'LLM base url'))
    checks.append(('env:DTFLOW_LLM_API_KEY', bool(os.getenv('DTFLOW_LLM_API_KEY')), 'LLM api key'))
    checks.append(('env:DTFLOW_LLM_MODEL', bool(os.getenv('DTFLOW_LLM_MODEL')), 'LLM model'))

    return checks
��制'))

    return checks
