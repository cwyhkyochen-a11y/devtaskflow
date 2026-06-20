import json
from pathlib import Path


class ConfigError(Exception):
    pass


def find_project_root(start: Path | None = None):
    current = (start or Path.cwd()).resolve()
    while current != current.parent:
        if (current / '.dtflow' / 'config.json').exists():
            return current
        current = current.parent
    return None


def load_config(project_root: Path):
    config_path = project_root / '.dtflow' / 'config.json'
    if not config_path.exists():
        raise ConfigError(f'找不到配置文件: {config_path}')
    try:
        return json.loads(config_path.read_text(encoding='utf-8'))
    except Exception as e:
        raise ConfigError(f'配置文件解析失败: {e}')


def validate_config(config: dict):
    required = [
        ('project', dict),
        ('pipeline', dict),
        ('adapters', dict),
    ]
    for key, typ in required:
        if key not in config:
            raise ConfigError(f'缺少配置段: {key}')
        if not isinstance(config[key], typ):
            raise ConfigError(f'配置段类型错误: {key}')
    return True
