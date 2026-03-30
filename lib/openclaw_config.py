"""从 OpenClaw 配置自动读取 LLM 设置"""
import json
import os
from pathlib import Path


def _load_openclaw_config() -> dict:
    config_path = Path.home() / '.openclaw' / 'openclaw.json'
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'⚠️ openclaw_config: 读取配置文件失败: {e}')
        return {}


def _read_api_key(provider: str) -> str:
    """从 ~/.openclaw/credentials/ 读取 API Key"""
    cred_dir = Path.home() / '.openclaw' / 'credentials'
    # 尝试 {provider}:default.api
    for suffix in [f'{provider}:default.api', f'{provider}.api']:
        cred_file = cred_dir / suffix
        if cred_file.exists():
            try:
                return cred_file.read_text(encoding='utf-8').strip()
            except Exception as e:
                print(f'⚠️ 读取凭据文件 {cred_file} 失败: {e}')
                continue
    return ''


def detect_openclaw_llm() -> dict:
    """自动检测 OpenClaw 的 LLM 配置，返回 {base_url, api_key, model}。
    任一字段获取失败则对应值为空字符串。
    """
    cfg = _load_openclaw_config()
    if not cfg:
        return {'base_url': '', 'api_key': '', 'model': ''}

    # 1. 获取主模型 (如 "openrouter/xiaomi/mimo-v2-pro")
    primary = cfg.get('agents', {}).get('defaults', {}).get('model', {}).get('primary', '')
    if not primary:
        return {'base_url': '', 'api_key': '', 'model': ''}

    # 2. 解析 provider 名
    # 格式: "provider/model-id" 或 "provider/sub-provider/model-id"
    parts = primary.split('/')
    providers = cfg.get('models', {}).get('providers', {})

    # 3. 在 providers 中查找匹配的 baseUrl
    base_url = ''
    api_key = ''
    model_id = parts[-1] if parts else primary

    # 尝试从最长到最短的 provider 名匹配
    for i in range(len(parts) - 1, 0, -1):
        provider_name = '/'.join(parts[:i])
        if provider_name in providers:
            base_url = providers[provider_name].get('baseUrl', '').rstrip('/')
            api_key = _read_api_key(provider_name)
            break

    # 如果没找到，尝试第一个部分作为 provider
    if not base_url and parts and parts[0] in providers:
        base_url = providers[parts[0]].get('baseUrl', '').rstrip('/')
        api_key = _read_api_key(parts[0])

    return {
        'base_url': base_url,
        'api_key': api_key,
        'model': model_id or primary,
    }
