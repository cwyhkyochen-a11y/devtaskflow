from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


def run_shell(command: str, cwd: Path):
    """Run a single command safely using argument list (no shell=True).

    For commands requiring shell features (pipes, redirects, &&),
    wrap them as: bash -c "your | command && here"
    """
    if not command.strip():
        return {'command': command, 'skipped': True}
    args = shlex.split(command)
    result = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'命令执行失败: {command}')
    return {
        'command': command,
        'stdout': result.stdout.strip(),
    }


def run_proc(command: list[str], cwd: Path, timeout: int = 300):
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or '命令执行失败')
    return result.stdout.strip()


class BaseDeployAdapter:
    name = 'base'

    def deploy(self, project_root: Path, config: dict) -> dict:
        raise NotImplementedError


class ShellDeployAdapter(BaseDeployAdapter):
    name = 'shell'

    def deploy(self, project_root: Path, config: dict) -> dict:
        deploy_cfg = config.get('deploy', {})
        build = run_shell(deploy_cfg.get('build_command', ''), project_root)
        deploy = run_shell(deploy_cfg.get('deploy_command', ''), project_root)
        restart = run_shell(deploy_cfg.get('restart_command', ''), project_root)
        return {
            'adapter': 'shell',
            'project_root': str(project_root),
            'build': build,
            'deploy': deploy,
            'restart': restart,
            'message': 'shell deploy 执行完成。',
        }


class SSHShellDeployAdapter(BaseDeployAdapter):
    name = 'ssh_shell'

    @staticmethod
    def _validate_ssh_config(host: str, user: str, path: str):
        """基本格式校验，防止 shell 元字符注入。"""
        if not re.fullmatch(r'[A-Za-z0-9._-]+', host):
            raise RuntimeError(f'ssh_shell host 格式不合法: {host!r}（仅允许域名/IP 字符）')
        if not re.fullmatch(r'[A-Za-z0-9._-]+', user):
            raise RuntimeError(f'ssh_shell user 格式不合法: {user!r}（仅允许字母数字._-）')
        if not re.fullmatch(r'[/A-Za-z0-9._-]+', path):
            raise RuntimeError(f'ssh_shell path 格式不合法: {path!r}（不允许 shell 元字符）')

    def deploy(self, project_root: Path, config: dict) -> dict:
        deploy_cfg = config.get('deploy', {})
        host = deploy_cfg.get('host', '')
        user = deploy_cfg.get('user', '')
        path = deploy_cfg.get('path', '')
        upload_mode = deploy_cfg.get('upload_mode', 'rsync')
        build = run_shell(deploy_cfg.get('build_command', ''), project_root)

        if not host or not user or not path:
            raise RuntimeError('ssh_shell 缺少 host/user/path 配置')

        remote = f'{user}@{host}:{path}'
        if upload_mode == 'rsync':
            upload_stdout = run_proc(['rsync', '-avz', '--exclude', '.git', '--exclude', 'node_modules', f'{project_root}/', remote], project_root)
            upload = {'mode': 'rsync', 'stdout': upload_stdout}
        elif upload_mode == 'scp':
            upload_stdout = run_proc(['scp', '-r', str(project_root), remote], project_root)
            upload = {'mode': 'scp', 'stdout': upload_stdout}
        else:
            raise RuntimeError(f'不支持的 upload_mode: {upload_mode}')

        restart_cmd = deploy_cfg.get('restart_command', '').strip()
        restart = {'skipped': True, 'command': restart_cmd}
        if restart_cmd:
            restart_stdout = run_proc(['ssh', f'{user}@{host}', restart_cmd], project_root)
            restart = {'command': restart_cmd, 'stdout': restart_stdout}

        return {
            'adapter': 'ssh_shell',
            'host': host,
            'user': user,
            'path': path,
            'upload_mode': upload_mode,
            'build': build,
            'upload': upload,
            'restart': restart,
            'message': 'ssh_shell deploy 执行完成。',
        }


class DockerDeployAdapter(BaseDeployAdapter):
    name = 'docker'

    def deploy(self, project_root: Path, config: dict) -> dict:
        deploy_cfg = config.get('deploy', {})
        image_name = deploy_cfg.get('docker_image') or config.get('project', {}).get('name', 'dtflow-app')
        port = deploy_cfg.get('port', 3000)

        # 检查 Docker 是否可用
        try:
            run_proc(['docker', '--version'], project_root)
        except Exception:
            raise RuntimeError('Docker 未安装或不在 PATH 中。请先安装 Docker：https://docs.docker.com/get-docker/')

        # 如果没有 Dockerfile，自动生成
        dockerfile = project_root / 'Dockerfile'
        if not dockerfile.exists():
            self._generate_dockerfile(project_root, config)

        # 停掉旧容器（如果存在）
        run_shell(f'docker rm -f {image_name} 2>/dev/null || true', project_root)

        # docker build
        build = run_proc(['docker', 'build', '-t', image_name, '.'], project_root)

        # docker run
        run_result = run_proc(
            ['docker', 'run', '-d', '-p', f'{port}:{port}', '--name', image_name, image_name],
            project_root,
        )

        return {
            'adapter': 'docker',
            'image': image_name,
            'port': port,
            'url': f'http://localhost:{port}',
            'container_id': run_result.strip(),
            'message': f'Docker 容器已启动，访问 http://localhost:{port}',
        }

    def _generate_dockerfile(self, project_root: Path, config: dict):
        """根据项目类型自动生成 Dockerfile。"""
        language = config.get('project', {}).get('language', 'typescript')
        deploy_cfg = config.get('deploy', {})
        port = deploy_cfg.get('port', 3000)

        if (project_root / 'package.json').exists():
            dockerfile = f"""FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build 2>/dev/null || true
EXPOSE {port}
CMD ["npm", "start"]
"""
        elif (project_root / 'requirements.txt').exists():
            if (project_root / 'manage.py').exists():
                cmd = f'python manage.py runserver 0.0.0.0:{port}'
            elif (project_root / 'app.py').exists():
                cmd = f'python app.py'
            else:
                cmd = f'python main.py'
            dockerfile = f"""FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["sh", "-c", "{cmd}"]
"""
        else:
            dockerfile = "# 无法自动识别项目类型，请手动编写 Dockerfile\nFROM alpine:latest\n"

        (project_root / 'Dockerfile').write_text(dockerfile, encoding='utf-8')


ADAPTERS = {
    'shell': ShellDeployAdapter,
    'ssh_shell': SSHShellDeployAdapter,
    'docker': DockerDeployAdapter,
}


def run_deploy_adapter(project_root: Path, config: dict):
    adapter_name = config.get('adapters', {}).get('deploy', 'shell')
    adapter_cls = ADAPTERS.get(adapter_name)
    if not adapter_cls:
        raise RuntimeError(f'不支持的 deploy adapter: {adapter_name}')
    return adapter_cls().deploy(project_root, config)
