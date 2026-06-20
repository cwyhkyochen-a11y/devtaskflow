"""Detect Codex/OpenAI-compatible LLM settings for DevTaskFlow."""
import os
from pathlib import Path


def _parse_env_file(env_path: Path) -> dict:
    result = {}
    try:
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            result[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return result


def _first(*values: str) -> str:
    for value in values:
        if value:
            return value.strip()
    return ''


def _guess_base_url(model: str) -> str:
    return 'https://api.openai.com/v1'


def detect_codex_llm(project_root: Path | None = None) -> dict:
    """Return {base_url, api_key, model, source} for Codex-friendly execution.

    DevTaskFlow intentionally does not read Codex account/session files. Use an
    explicit project .env or process environment variables so credentials remain
    visible to the user and easy to rotate.
    """
    env = os.environ
    file_cfg = {}
    if project_root:
        file_cfg = _parse_env_file(project_root / '.env')
    else:
        cwd_env = Path.cwd() / '.env'
        if cwd_env.exists():
            file_cfg = _parse_env_file(cwd_env)

    base_url = _first(
        env.get('DTFLOW_LLM_BASE_URL', ''),
        env.get('DTFLOW_CODEX_BASE_URL', ''),
        file_cfg.get('DTFLOW_LLM_BASE_URL', ''),
        file_cfg.get('DTFLOW_CODEX_BASE_URL', ''),
        env.get('OPENAI_BASE_URL', ''),
        file_cfg.get('OPENAI_BASE_URL', ''),
    ).rstrip('/')
    api_key = _first(
        env.get('DTFLOW_LLM_API_KEY', ''),
        env.get('DTFLOW_CODEX_API_KEY', ''),
        file_cfg.get('DTFLOW_LLM_API_KEY', ''),
        file_cfg.get('DTFLOW_CODEX_API_KEY', ''),
        env.get('OPENAI_API_KEY', ''),
        file_cfg.get('OPENAI_API_KEY', ''),
    )
    model = _first(
        env.get('DTFLOW_LLM_MODEL', ''),
        env.get('DTFLOW_CODEX_MODEL', ''),
        file_cfg.get('DTFLOW_LLM_MODEL', ''),
        file_cfg.get('DTFLOW_CODEX_MODEL', ''),
        env.get('OPENAI_MODEL', ''),
        file_cfg.get('OPENAI_MODEL', ''),
    )

    source = '未配置'
    if env.get('DTFLOW_LLM_API_KEY') or env.get('DTFLOW_CODEX_API_KEY'):
        source = 'DevTaskFlow 环境变量'
    elif file_cfg.get('DTFLOW_LLM_API_KEY') or file_cfg.get('DTFLOW_CODEX_API_KEY'):
        source = '项目 .env'
    elif env.get('OPENAI_API_KEY') or file_cfg.get('OPENAI_API_KEY'):
        source = 'OpenAI 环境变量'

    if api_key and model and not base_url:
        base_url = _guess_base_url(model)

    return {
        'base_url': base_url,
        'api_key': api_key,
        'model': model,
        'source': source,
    }
