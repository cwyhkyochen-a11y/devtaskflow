from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / 'prompts'


def load_prompt(name: str) -> str:
    path = (PROMPTS_DIR / name).resolve()
    if not path.is_relative_to(PROMPTS_DIR):
        raise PermissionError(f'路径遍历攻击: {name} 解析后超出 prompts 目录范围')
    if not path.exists():
        raise FileNotFoundError(f'prompt 文件不存在: {path}')
    return path.read_text(encoding='utf-8')
