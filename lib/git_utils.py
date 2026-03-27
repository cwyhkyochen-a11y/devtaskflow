"""Git 工具函数 — 自动初始化仓库、自动提交"""
import subprocess
import shutil
from pathlib import Path


def check_git_installed() -> bool:
    """检查 git 是否已安装"""
    return shutil.which('git') is not None


def is_git_repo(project_root: Path) -> bool:
    """检查目录是否已经是 git 仓库"""
    try:
        r = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            cwd=str(project_root), capture_output=True, text=True, timeout=5
        )
        return r.returncode == 0
    except Exception:
        return False


def ensure_git_repo(project_root: Path) -> dict:
    """确保目录是 git 仓库，不是的话自动 git init + 首次 commit"""
    result = {'initialized': False, 'already_repo': False, 'error': None}

    if not check_git_installed():
        result['error'] = 'git 未安装。请运行: sudo apt install git (Linux) / brew install git (macOS)'
        return result

    if is_git_repo(project_root):
        result['already_repo'] = True
        return result

    try:
        r = subprocess.run(['git', 'init'], cwd=str(project_root), capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            result['error'] = f'git init 失败: {r.stderr.strip()}'
            return result

        subprocess.run(['git', 'branch', '-M', 'main'], cwd=str(project_root), capture_output=True, text=True, timeout=5)

        subprocess.run(['git', 'add', '.'], cwd=str(project_root), capture_output=True, text=True, timeout=10)
        subprocess.run(
            ['git', 'commit', '-m', 'init: 项目初始化'],
            cwd=str(project_root), capture_output=True, text=True, timeout=10
        )

        result['initialized'] = True
    except subprocess.TimeoutExpired:
        result['error'] = 'git 操作超时'
    except Exception as e:
        result['error'] = f'git 操作异常: {str(e)}'

    return result


def auto_commit(project_root: Path, message: str) -> dict:
    """自动 git add + commit（如果有变更）"""
    result = {'committed': False, 'skipped': False, 'error': None}

    if not check_git_installed():
        result['error'] = 'git 未安装'
        return result

    if not is_git_repo(project_root):
        result['error'] = '不是 git 仓库'
        return result

    try:
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=str(project_root), capture_output=True, text=True, timeout=5
        )
        if not status.stdout.strip():
            result['skipped'] = True
            return result

        r = subprocess.run(['git', 'add', '.'], cwd=str(project_root), capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            result['error'] = f'git add 失败: {r.stderr.strip()}'
            return result

        r = subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=str(project_root), capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            if 'nothing to commit' in r.stdout.lower() or 'nothing to commit' in r.stderr.lower():
                result['skipped'] = True
            else:
                result['error'] = f'git commit 失败: {r.stderr.strip()}'
        else:
            result['committed'] = True

    except subprocess.TimeoutExpired:
        result['error'] = 'git 操作超时'
    except Exception as e:
        result['error'] = f'git 操作异常: {str(e)}'

    return result
