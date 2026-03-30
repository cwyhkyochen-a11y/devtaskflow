import json
import time
import functools
from pathlib import Path


from config import load_config
from project import get_current_version_dir
from state import StateManager


def mark_command_failed(project_root: Path, action: str, error: Exception):
    try:
        config = load_config(project_root)
        version_dir = get_current_version_dir(project_root, config)
        if not version_dir or not (version_dir / '.state.json').exists():
            return
        state = StateManager(version_dir)
        state.data['status'] = 'failed'
        state.data['last_action'] = action
        state.data['last_error'] = str(error)
        state.save()
    except Exception as e:
        print(f'⚠️ mark_command_failed 写入状态失败: {type(e).__name__}: {e}')
        return


def retry_with_backoff(func=None, *, max_retries=3, base_delay=1.0):
    """
    带指数退避的自动重试装饰器。

    用法：
      @retry_with_backoff                      # 无参装饰器
      @retry_with_backoff(max_retries=5)       # 带参装饰器
      retry_with_backoff(some_func, max_retries=2)  # 直接调用
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        print(f'⚠️ 第 {attempt + 1}/{max_retries} 次重试失败：{type(e).__name__}: {e}')
                        print(f'   等待 {delay:.1f}s 后重试...')
                        time.sleep(delay)
                    else:
                        print(f'❌ 已重试 {max_retries} 次，仍然失败：{type(e).__name__}: {e}')
            raise last_exc
        return wrapper

    if func is not None:
        # 无参调用: @retry_with_backoff 或 retry_with_backoff(func)
        return decorator(func)
    return decorator


# 面向用户的错误翻译表
_USER_FRIENDLY_ERRORS = {
    'ConfigError': {
        'message': '项目配置有问题。',
        'suggestion': '建议运行 dtflow setup 重新配置。',
    },
    'RuntimeError': {
        'message': '操作过程中出了点问题。',
        'suggestion': '建议运行 dtflow advanced status 查看当前状态，或 dtflow advanced recover 自动检测修复。',
    },
    'LLMError': {
        'message': 'AI 服务连接失败。',
        'suggestion': '请检查网络或运行 dtflow setup 重新配置。',
    },
    'FileNotFoundError': {
        'message': '找不到需要的文件。',
        'suggestion': '确认当前目录是 DevTaskFlow 项目。运行 dtflow advanced doctor 检查环境。',
    },
    'PermissionError': {
        'message': '没有权限操作文件。',
        'suggestion': '请检查文件权限，尝试使用 sudo 或修改文件所有者。',
    },
    'ConnectionError': {
        'message': '网络连接失败。',
        'suggestion': '请检查网络连接后重试。如使用 VPN，请确认 VPN 已连接。',
    },
    'TimeoutError': {
        'message': '网络连接超时。',
        'suggestion': '请检查网络后重试。如果频繁超时，可能是 AI 服务繁忙，请稍后再试。',
    },
    'JSONDecodeError': {
        'message': 'AI 返回的数据格式异常。',
        'suggestion': '正在自动重试... 如果频繁出现，建议运行 dtflow setup 检查 AI 服务配置。',
    },
    'ValueError': {
        'message': '参数值不合法。',
        'suggestion': '请检查输入的参数是否正确。运行 dtflow --help 查看用法。',
    },
    'OSError': {
        'message': '系统操作失败。',
        'suggestion': '请检查磁盘空间和文件系统权限。运行 dtflow advanced doctor 检查环境。',
    },
    'KeyError': {
        'message': '缺少必要的配置项。',
        'suggestion': '请运行 dtflow setup 重新配置，或检查 .dtflow/config.json 文件。',
    },
    'ImportError': {
        'message': '缺少依赖模块。',
        'suggestion': '请运行 pip install 安装所需依赖，或运行 dtflow setup 检查环境。',
    },
    'NotADirectoryError': {
        'message': '路径不是目录。',
        'suggestion': '请确认项目路径正确，运行 dtflow advanced doctor 检查项目结构。',
    },
    'IsADirectoryError': {
        'message': '期望文件但找到目录。',
        'suggestion': '请检查项目结构是否正确，运行 dtflow advanced doctor 检查。',
    },
    'UnicodeDecodeError': {
        'message': '文件编码异常。',
        'suggestion': '请确认文件使用 UTF-8 编码保存。',
    },
}


def friendly_error(error: Exception) -> str:
    """将 Python 异常翻译为面向用户的友好提示。"""
    error_type = type(error).__name__
    entry = _USER_FRIENDLY_ERRORS.get(error_type)
    if entry:
        msg = entry['message']
        suggestion = entry['suggestion']
        return f'⚠️ {msg}\n💡 {suggestion}\n（技术详情：{error}）'
    return f'⚠️ 运行 dtflow advanced recover 自动检测修复，或 dtflow advanced status 查看状态。\n（技术详情：{error}）'
