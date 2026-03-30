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

    # LLM 检查：优先检测 OpenClaw 配置
    try:
        from openclaw_config import detect_openclaw_llm
        oc = detect_openclaw_llm()
        has_llm = bool(oc.get('base_url') and oc.get('api_key') and oc.get('model'))
        llm_source = 'OpenClaw 自动配置' if has_llm else os.getenv('DTFLOW_LLM_BASE_URL') and '环境变量' or '未配置'
    except Exception:
        has_llm = bool(os.getenv('DTFLOW_LLM_BASE_URL'))
        llm_source = '环境变量' if has_llm else '未配置（openclaw_config 导入失败）'
    checks.append(('llm', has_llm, f'LLM 服务 ({llm_source})'))

    return checks
