"""本地预览 — 后台启动项目，让用户在浏览器看到效果。"""
from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import time
from pathlib import Path

from project import get_current_version_dir
from state import StateManager


def _detect_project_type(project_root: Path) -> dict:
    """检测项目类型和启动命令。"""
    if (project_root / 'package.json').exists():
        try:
            pkg = json.loads((project_root / 'package.json').read_text(encoding='utf-8'))
            scripts = pkg.get('scripts', {})
            if 'dev' in scripts:
                return {'type': 'node', 'install': 'npm install', 'start': 'npm run dev', 'framework': pkg.get('name', '')}
            elif 'start' in scripts:
                return {'type': 'node', 'install': 'npm install', 'start': 'npm start', 'framework': pkg.get('name', '')}
        except Exception:
            pass
        return {'type': 'node', 'install': 'npm install', 'start': 'npm start', 'framework': ''}

    if (project_root / 'requirements.txt').exists():
        if (project_root / 'manage.py').exists():
            return {'type': 'python', 'install': 'pip install -r requirements.txt', 'start': 'python manage.py runserver 0.0.0.0:{port}', 'framework': 'django'}
        if (project_root / 'app.py').exists():
            return {'type': 'python', 'install': 'pip install -r requirements.txt', 'start': 'python app.py', 'framework': 'flask'}
        if (project_root / 'main.py').exists():
            return {'type': 'python', 'install': 'pip install -r requirements.txt', 'start': 'python main.py', 'framework': ''}

    if (project_root / 'Dockerfile').exists():
        return {'type': 'docker', 'install': '', 'start': 'docker-compose up', 'framework': 'docker'}

    return {'type': 'unknown', 'install': '', 'start': '', 'framework': ''}


def _wait_for_port(port: int, timeout: int = 30) -> bool:
    """等待端口可访问。"""
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run_flow(project_root: Path, config: dict, port: int = 3000) -> dict:
    """
    本地预览主流程。

    1. 检测项目类型
    2. 执行依赖安装（如需要）
    3. 后台启动服务
    4. 检测端口是否可访问
    5. 返回访问地址
    """
    # 检查已有进程
    version_dir = get_current_version_dir(project_root, config)
    if version_dir and (version_dir / '.state.json').exists():
        state = StateManager(version_dir)
        existing_pid = state.data.get('run_pid')
        if existing_pid:
            try:
                os.kill(existing_pid, 0)  # 检查进程是否存在
                return {
                    'url': f'http://localhost:{port}',
                    'status': 'already_running',
                    'pid': existing_pid,
                    'message': '服务已在运行中。',
                }
            except ProcessLookupError:
                pass  # 进程已退出

    proj_type = _detect_project_type(project_root)
    if proj_type['type'] == 'unknown':
        raise RuntimeError(
            '无法识别项目类型。确保项目根目录有 package.json、requirements.txt 或 Dockerfile。'
        )

    # 安装依赖
    install_cmd = proj_type['install']
    if install_cmd:
        print(f'📦 安装依赖: {install_cmd}')
        install_args = shlex.split(install_cmd)
        result = subprocess.run(
            install_args, cwd=str(project_root),
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f'依赖安装失败: {result.stderr[:500]}')

    # 准备启动命令
    start_cmd = proj_type['start'].format(port=port)
    start_args = shlex.split(start_cmd)
    env = {**os.environ, 'PORT': str(port)}

    print(f'🚀 启动服务: {start_cmd}')

    # 后台启动
    log_file = project_root / '.dtflow' / 'run.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(log_file, 'w')
    proc = subprocess.Popen(
        start_args, cwd=str(project_root),
        stdout=log_f, stderr=log_f, env=env,
    )
    log_f.close()

    # 等待端口就绪
    print(f'⏳ 等待服务启动（最多 30 秒）...')
    ready = _wait_for_port(port, timeout=30)

    if not ready:
        # 可能服务用了不同端口，再给点时间
        time.sleep(3)
        ready = _wait_for_port(port, timeout=5)

    url = f'http://localhost:{port}'

    # 保存 PID
    if version_dir and (version_dir / '.state.json').exists():
        state = StateManager(version_dir)
        state.data['run_pid'] = proc.pid
        state.data['run_port'] = port
        state.data['run_url'] = url
        state.save()

    if ready:
        return {
            'url': url,
            'status': 'running',
            'pid': proc.pid,
            'log_file': str(log_file),
            'message': f'服务已启动，访问 {url}',
        }
    else:
        return {
            'url': url,
            'status': 'starting',
            'pid': proc.pid,
            'log_file': str(log_file),
            'message': f'服务进程已启动（PID {proc.pid}），但端口 {port} 暂未就绪。可能需要更长时间初始化。',
        }


def stop_run(project_root: Path, config: dict) -> dict:
    """停止本地预览服务。"""
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir or not (version_dir / '.state.json').exists():
        return {'status': 'no_version', 'message': '没有找到当前版本。'}

    state = StateManager(version_dir)
    pid = state.data.get('run_pid')
    if not pid:
        return {'status': 'not_running', 'message': '没有正在运行的预览服务。'}

    try:
        os.kill(pid, signal.SIGTERM)
        state.data['run_pid'] = None
        state.data['run_port'] = None
        state.save()
        return {'status': 'stopped', 'pid': pid, 'message': '预览服务已停止。'}
    except ProcessLookupError:
        state.data['run_pid'] = None
        state.save()
        return {'status': 'already_stopped', 'message': '服务已经停止了。'}
