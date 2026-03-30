"""交互式 setup 流程 — 帮非技术用户配置 LLM 依赖。

支持三档模式：
- auto: 自动检测已有配置（极简模式）
- guided: 引导模式（只需填 API Key）
- advanced: 高级模式（手动配置所有参数）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


PRESETS = {
    '1': {
        'name': 'Claude Opus 4.6（推荐）',
        'base_url': 'https://api.anthropic.com/v1',
        'model_hint': 'claude-opus-4-6',
        'note': '综合能力最强，推荐用于复杂开发任务',
    },
    '2': {
        'name': 'GPT 5.4 Pro',
        'base_url': 'https://api.openai.com/v1',
        'model_hint': 'gpt-5.4-pro',
        'note': 'OpenAI 旗舰模型，大型项目首选',
    },
    '3': {
        'name': 'GPT 5.4',
        'base_url': 'https://api.openai.com/v1',
        'model_hint': 'gpt-5.4',
        'note': '性价比高，适合中小型项目',
    },
    '4': {
        'name': '小米 Mimo V2 Pro',
        'base_url': 'https://api.xiaomi.com/v1',
        'model_hint': 'mimo-v2-pro',
        'note': '国产模型，中文表现好',
    },
    '5': {
        'name': '其他模型（手动填写）',
        'base_url': '',
        'model_hint': '',
        'note': '⚠️ 其他模型可能无法完成完整开发任务，建议从以上 4 个中选择',
    },
}


# ── 通用工具函数 ──────────────────────────────────────────────

def _prompt(msg: str, default: str = '') -> str:
    """显示提示并读取用户输入。"""
    suffix = f' [{default}]' if default else ''
    try:
        val = input(f'{msg}{suffix}: ').strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return val or default


def _mask_url(url: str) -> str:
    """脱敏显示 URL，如 https://api.***.com/v1"""
    if not url:
        return '(空)'
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ''
        scheme = parsed.scheme or 'https'
        path = parsed.path or ''
        # 域名：保留第一段和顶级域，中间用 *** 替代
        if '.' in host:
            parts = host.split('.')
            if len(parts) == 2:
                # example.com → ***.com
                masked = f'***.{parts[-1]}'
            else:
                # api.openai.com → api.***.com
                first = parts[0]
                last = parts[-1]
                masked = f'{first}.***.{last}'
        else:
            masked = '***'
        return f'{scheme}://{masked}{path}'
    except Exception:
        return url[:8] + '***'


def _test_connection(base_url: str, api_key: str, model: str) -> tuple[bool, str]:
    """尝试发送一个最简请求，验证连通性。"""
    try:
        import requests
        resp = requests.post(
            f'{base_url.rstrip("/")}/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': 'hi'}],
                'max_tokens': 5,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return True, '连接成功！'
        return False, f'连接失败：HTTP {resp.status_code} — {resp.text[:200]}'
    except ImportError:
        return True, '跳过测试（未安装 requests 库，但配置已保存）'
    except Exception as e:
        return False, f'连接失败：{e}'


def _write_env_file(base_url: str, api_key: str, model: str, env_path: Path) -> None:
    """写入 .env 文件。"""
    content = (
        f'DTFLOW_LLM_BASE_URL={base_url}\n'
        f'DTFLOW_LLM_API_KEY={api_key}\n'
        f'DTFLOW_LLM_MODEL={model}\n'
    )
    env_path.write_text(content, encoding='utf-8')
    os.chmod(env_path, 0o600)
    # 同时设置到当前进程环境，方便后续命令直接使用
    os.environ['DTFLOW_LLM_BASE_URL'] = base_url
    os.environ['DTFLOW_LLM_API_KEY'] = api_key
    os.environ['DTFLOW_LLM_MODEL'] = model


def _apply_config(config: dict, project_root: Path | None = None) -> None:
    """将配置写入 .env 文件。"""
    target_dir = project_root or Path.cwd()
    env_path = target_dir / '.env'
    _write_env_file(config['base_url'], config['api_key'], config['model'], env_path)
    print(f'✅ 配置已保存到 {env_path}')


def _run_doctor_check() -> None:
    """运行 doctor 环境检查。"""
    print()
    print('⏳ 检查环境...')
    try:
        from doctor import run_doctor
        checks = run_doctor()
        all_ok = True
        for name, passed, detail in checks:
            mark = '✅' if passed else '❌'
            print(f'  {mark} {name}: {detail}')
            if not passed:
                all_ok = False
        if all_ok:
            print('  🎉 环境检查全部通过！')
        else:
            print('  ⚠️ 部分检查未通过，但基本环境已就绪。')
    except Exception as e:
        print(f'⚠️ doctor 检查出错：{e}，但配置已保存。')


# ── 配置检测（极简模式） ──────────────────────────────────────

def _detect_existing_config(project_root: Path | None = None) -> dict | None:
    """检测已有配置，返回 {base_url, api_key, model} 或 None。

    检测顺序：
    1. 当前环境变量
    2. 项目目录下的 .env 文件
    3. OpenClaw 环境下的 LLM 配置
    """
    base_url = ''
    api_key = ''
    model = ''

    # 1. 检测当前环境变量
    base_url = os.environ.get('DTFLOW_LLM_BASE_URL', '').strip()
    api_key = os.environ.get('DTFLOW_LLM_API_KEY', '').strip()
    model = os.environ.get('DTFLOW_LLM_MODEL', '').strip()

    # 2. 如果环境变量不完整，尝试读取 .env 文件
    if not (base_url and api_key and model):
        target_dir = project_root or Path.cwd()
        env_path = target_dir / '.env'
        if env_path.exists():
            env_config = _parse_env_file(env_path)
            base_url = base_url or env_config.get('DTFLOW_LLM_BASE_URL', '').strip()
            api_key = api_key or env_config.get('DTFLOW_LLM_API_KEY', '').strip()
            model = model or env_config.get('DTFLOW_LLM_MODEL', '').strip()

    # 3. 尝试检测 OpenClaw 环境变量
    if not (base_url and api_key and model):
        oc_base = os.environ.get('OPENAI_BASE_URL', '').strip()
        oc_key = os.environ.get('OPENAI_API_KEY', '').strip()
        oc_model = os.environ.get('OPENAI_MODEL', '').strip()
        base_url = base_url or oc_base
        api_key = api_key or oc_key
        model = model or oc_model

    # 4. 尝试从 OpenClaw 主配置自动检测
    if not (base_url and api_key and model):
        try:
            from openclaw_config import detect_openclaw_llm
            oc = detect_openclaw_llm()
            base_url = base_url or oc.get('base_url', '').strip()
            api_key = api_key or oc.get('api_key', '').strip()
            model = model or oc.get('model', '').strip()
        except Exception:
            pass

    # 5. 再尝试 OpenRouter 等常见变量
    if not base_url:
        base_url = os.environ.get('OPENROUTER_BASE_URL', '').strip()
    if not api_key:
        api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()

    # 验证：至少需要 api_key 和 model
    if api_key and model:
        # 如果没有 base_url，尝试根据 model 推断
        if not base_url:
            base_url = _guess_base_url(model)
        if base_url:
            return {'base_url': base_url, 'api_key': api_key, 'model': model}

    return None


def _parse_env_file(env_path: Path) -> dict:
    """解析 .env 文件为字典。"""
    result = {}
    try:
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                result[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return result


def _guess_base_url(model: str) -> str:
    """根据模型名猜测 base_url。"""
    model_lower = model.lower()
    if 'claude' in model_lower or 'anthropic' in model_lower:
        return 'https://api.anthropic.com/v1'
    if 'gpt' in model_lower or 'o1' in model_lower or 'o3' in model_lower:
        return 'https://api.openai.com/v1'
    if 'mimo' in model_lower or 'xiaomi' in model_lower:
        return 'https://api.xiaomi.com/v1'
    if 'gemini' in model_lower or 'google' in model_lower:
        return 'https://generativelanguage.googleapis.com/v1'
    # 默认用 OpenAI 兼容格式
    return 'https://api.openai.com/v1'


# ── 极简模式：自动检测已有配置 ────────────────────────────────

def _setup_auto(project_root: Path | None = None) -> int:
    """极简模式 — 自动检测已有配置并应用。"""
    # 优先尝试从 OpenClaw 主配置自动读取
    try:
        from openclaw_config import detect_openclaw_llm
        oc = detect_openclaw_llm()
        if oc.get('base_url') and oc.get('api_key') and oc.get('model'):
            os.environ['DTFLOW_LLM_BASE_URL'] = oc['base_url']
            os.environ['DTFLOW_LLM_API_KEY'] = oc['api_key']
            os.environ['DTFLOW_LLM_MODEL'] = oc['model']
            print(f'✅ 自动使用 OpenClaw 配置: {oc["model"]}')
            _apply_config(oc, project_root)
            _run_doctor_check()
            return 0
    except Exception:
        pass

    existing = _detect_existing_config(project_root)
    if existing:
        print()
        print('🔍 检测到已有配置：')
        print(f'   API 地址：{_mask_url(existing["base_url"])}')
        print(f'   模型：{existing["model"]}')
        print()
        use = _prompt('是否使用已有配置？(Y/n)', 'y')
        if use.lower() in ('y', ''):
            _apply_config(existing, project_root)
            _run_doctor_check()
            return 0
        # 用户拒绝已有配置，降级到引导模式
        print()
        print('好的，重新配置。')
        return _setup_guided(project_root)
    else:
        # 没有检测到配置，降级到引导模式
        print()
        print('ℹ️ 未检测到已有配置，进入引导模式。')
        return _setup_guided(project_root)


# ── 引导模式：只需填 API Key ─────────────────────────────────

def _setup_guided(project_root: Path | None = None) -> int:
    """引导模式 — 只需选模型 + 填 API Key，其他自动。"""
    print()
    print('🚀 快速配置（只需 2 步）')
    print('=' * 40)
    print()
    print('选择你想用的 AI 服务：')
    print()

    for k, v in PRESETS.items():
        note = f'  — {v["note"]}' if v.get('note') else ''
        print(f'  {k}. {v["name"]}{note}')

    print()
    choice = _prompt('请选择（输入数字）', '1')
    preset = PRESETS.get(choice, PRESETS['1'])

    # 填 API Key
    print()
    print(f'已选：{preset["name"]}')
    api_key = _prompt('请输入你的 API Key')
    if not api_key:
        print('❌ API Key 不能为空')
        return 1

    # 自动推断 base_url 和 model
    base_url = preset['base_url']
    model = preset['model_hint']

    # 如果是"其他模型"，需要额外输入
    if choice == '5':
        print()
        model = _prompt('请输入模型名称')
        if not model:
            print('❌ 模型名称不能为空')
            return 1
        base_url = _prompt('请输入 API 地址', _guess_base_url(model))
        if not base_url:
            print('❌ API 地址不能为空')
            return 1

    # 测试连接
    print()
    print('⏳ 正在测试连接...')
    ok, msg = _test_connection(base_url, api_key, model)
    if ok:
        print(f'✅ {msg}')
    else:
        print(f'⚠️ {msg}')
        retry = _prompt('连接失败，是否仍然保存配置？(y/n)', 'n')
        if retry.lower() != 'y':
            print('已取消，配置未保存。')
            return 1

    # 保存配置
    _apply_config({'base_url': base_url, 'api_key': api_key, 'model': model}, project_root)

    # 运行 doctor
    _run_doctor_check()

    # 部署方式选择（简化版）
    print()
    print('📦 部署方式（写完代码怎么上线？）：')
    print('  1. 我有服务器 — SSH 上传部署')
    print('  2. 先本地看 — 写完先在浏览器看效果（推荐）')
    print('  3. 以后再说')
    print()
    deploy_choice = _prompt('请选择', '2')

    deploy_hint = {
        '1': '好的，创建项目后需要在 .dtflow/config.json 中填写服务器信息。',
        '2': '好的，代码生成后运行 dtflow start --run 即可在浏览器看效果。',
        '3': '没问题，随时可以再配置。',
    }
    print(f'  {deploy_hint.get(deploy_choice, deploy_hint["3"])}')

    print()
    print('🎉 环境配置完成！你现在可以开始使用了。')
    print('   运行 dtflow start --idea "你的需求" 来启动第一个项目。')

    return 0


# ── 高级模式：完整流程 ────────────────────────────────────────

def _setup_advanced(project_root: Path | None = None) -> int:
    """高级模式 — 手动配置所有参数。"""
    print()
    print('⚙️ 高级配置')
    print('=' * 40)
    print()
    print('选择你想用的 AI 服务：')
    print()

    for k, v in PRESETS.items():
        note = f'  — {v["note"]}' if v.get('note') else ''
        print(f'  {k}. {v["name"]}{note}')

    print()
    choice = _prompt('请选择（输入数字）', '1')
    preset = PRESETS.get(choice, PRESETS['5'])

    print()

    # Base URL
    default_url = preset.get('base_url', '')
    if default_url:
        base_url = _prompt('AI 服务地址（API Endpoint）', default_url)
    else:
        base_url = _prompt('请输入 AI 服务地址（API Endpoint）')
    if not base_url:
        print('❌ 服务地址不能为空')
        return 1

    # API Key
    print()
    api_key = _prompt('请输入你的 API Key')
    if not api_key:
        print('❌ API Key 不能为空')
        return 1

    # Model
    print()
    if preset['model_hint']:
        print(f'推荐模型：{preset["model_hint"]}')
        model = _prompt('直接回车使用推荐模型，否则输入你想用的模型名', preset['model_hint'])
    else:
        model = _prompt('请输入模型名称')
        if not model:
            print('❌ 模型名称不能为空')
            return 1

    # 测试连接
    print()
    print('⏳ 正在测试连接...')
    ok, msg = _test_connection(base_url, api_key, model)
    if ok:
        print(f'✅ {msg}')
    else:
        print(f'⚠️ {msg}')
        retry = _prompt('连接失败，是否仍然保存配置？(y/n)', 'n')
        if retry.lower() != 'y':
            print('已取消，配置未保存。')
            return 1

    # 写入 .env
    _apply_config({'base_url': base_url, 'api_key': api_key, 'model': model}, project_root)

    # 运行 doctor
    _run_doctor_check()

    # 部署方式引导
    print()
    print('📦 部署方式（可以之后再配，先选一个方向）：')
    print('  1. 本地预览 — 写完代码先在本地看效果（推荐新手）')
    print('  2. Docker 容器 — 打包成镜像，方便分享和部署')
    print('  3. 远程服务器 — 通过 SSH 上传到服务器（需要有服务器）')
    print('  4. 先跳过 — 之后再说')
    deploy_choice = _prompt('请选择', '1')

    deploy_hint = {
        '1': '好的，代码生成后可以本地预览。运行 dtflow start --run 即可。',
        '2': '好的，会在项目中自动生成 Dockerfile。需要本地安装了 Docker。',
        '3': '好的，创建项目后需要在 .dtflow/config.json 中填写服务器信息（host、user、path）。',
        '4': '没问题，随时可以通过修改配置来设置。',
    }
    print(f'  {deploy_hint.get(deploy_choice, deploy_hint["4"])}')

    print()
    print('🎉 环境配置完成！你现在可以开始使用了。')
    print('   运行 dtflow start --idea "你的需求" 来启动第一个项目。')

    return 0


# ── 主入口 ────────────────────────────────────────────────────

def run_setup(project_root: Path | None = None, mode: str | None = None) -> int:
    """
    交互式 setup 主流程。

    Args:
        project_root: 项目根目录（用于定位 .env 文件）
        mode: 配置模式 — 'auto' | 'guided' | 'advanced' | None（交互选择）

    Returns:
        0=成功, 1=失败
    """
    print()
    print('🔧 DevTaskFlow 环境配置')
    print('=' * 40)

    # 如果指定了模式，直接进入对应流程
    if mode == 'auto':
        return _setup_auto(project_root)
    if mode == 'guided':
        return _setup_guided(project_root)
    if mode == 'advanced':
        return _setup_advanced(project_root)

    # 没有指定模式 → 先尝试自动检测
    existing = _detect_existing_config(project_root)
    if existing:
        print()
        print('🔍 检测到已有配置：')
        print(f'   API 地址：{_mask_url(existing["base_url"])}')
        print(f'   模型：{existing["model"]}')
        print()
        use = _prompt('是否使用已有配置？(Y/n)', 'y')
        if use.lower() in ('y', ''):
            _apply_config(existing, project_root)
            _run_doctor_check()
            return 0
        # 用户拒绝已有配置，继续选择模式
        print()

    # 选择配置模式
    print()
    print('选择配置方式：')
    print('  1. 极简模式 — 只需填 API Key，其他自动（推荐）')
    print('  2. 高级模式 — 手动配置所有参数')
    print()
    choice = _prompt('请选择', '1')

    if choice == '1':
        return _setup_guided(project_root)
    else:
        return _setup_advanced(project_root)
