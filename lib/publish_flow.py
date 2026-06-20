from __future__ import annotations

import subprocess
from pathlib import Path

from project import get_current_version_dir
from state import StateManager


def run_cmd(command: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or '命令执行失败')
    return result.stdout.strip()


def ensure_git_repo(project_root: Path):
    run_cmd(['git', 'rev-parse', '--is-inside-work-tree'], project_root)


def detect_github_repo(project_root: Path) -> str:
    remote = run_cmd(['git', 'remote', 'get-url', 'origin'], project_root)
    remote = remote.strip()
    if remote.startswith('git@github.com:'):
        return remote.split(':', 1)[1].removesuffix('.git')
    if 'github.com/' in remote:
        return remote.split('github.com/', 1)[1].removesuffix('.git')
    return ''


def ensure_gh_auth(project_root: Path):
    run_cmd(['gh', 'auth', 'status'], project_root)


def ensure_clean_or_allow_dirty(project_root: Path, allow_dirty: bool):
    status = run_cmd(['git', 'status', '--porcelain'], project_root, check=False)
    if status and not allow_dirty:
        raise RuntimeError('当前 git 工作区不干净，请先提交或使用 --allow-dirty')


def release_exists(project_root: Path, repo: str, tag: str) -> bool:
    cmd = ['gh', 'release', 'view', tag]
    if repo:
        cmd += ['--repo', repo]
    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
    return result.returncode == 0


def tag_exists(project_root: Path, tag: str) -> bool:
    result = subprocess.run(['git', 'rev-parse', '-q', '--verify', f'refs/tags/{tag}'], cwd=str(project_root), capture_output=True, text=True)
    return result.returncode == 0


class BasePublishAdapter:
    name = 'base'

    def publish(self, project_root: Path, config: dict, **kwargs) -> dict:
        raise NotImplementedError


class GitHubPublishAdapter(BasePublishAdapter):
    name = 'github'

    def publish(self, project_root: Path, config: dict, **kwargs) -> dict:
        version_dir = get_current_version_dir(project_root, config)
        if not version_dir:
            raise RuntimeError('没有找到当前版本目录')

        state = StateManager(version_dir)
        if state.data.get('status') not in {'sealed', 'deployed', 'all_done'}:
            raise RuntimeError(f"当前状态不允许 publish: {state.data.get('status')}")

        ensure_git_repo(project_root)
        ensure_gh_auth(project_root)
        ensure_clean_or_allow_dirty(project_root, kwargs.get('allow_dirty', False))

        publish_cfg = config.get('publish', {})
        repo = publish_cfg.get('github_repo', '') or detect_github_repo(project_root)
        branch = publish_cfg.get('release_branch', 'main')
        tag = version_dir.name
        release_notes = version_dir / 'docs' / 'CHANGELOG.md'
        if not release_notes.exists():
            release_notes = version_dir / 'docs' / 'DEV_PLAN.md'

        if tag_exists(project_root, tag) and not kwargs.get('force_tag', False):
            raise RuntimeError(f'Git tag 已存在: {tag}；如需覆盖请显式使用 force_tag')

        if not tag_exists(project_root, tag):
            run_cmd(['git', 'tag', tag], project_root)
        elif kwargs.get('force_tag', False):
            run_cmd(['git', 'tag', '-f', tag], project_root)

        run_cmd(['git', 'push', 'origin', branch], project_root)
        if kwargs.get('force_tag', False):
            run_cmd(['git', 'push', 'origin', tag, '--force'], project_root)
        else:
            run_cmd(['git', 'push', 'origin', tag], project_root)

        title = f'{tag}'
        if release_exists(project_root, repo, tag):
            if not kwargs.get('replace_release', False):
                raise RuntimeError(f'GitHub release 已存在: {tag}；如需替换请显式使用 replace_release')
            delete_cmd = ['gh', 'release', 'delete', tag, '--yes']
            if repo:
                delete_cmd += ['--repo', repo]
            run_cmd(delete_cmd, project_root)

        cmd = ['gh', 'release', 'create', tag, '--title', title]
        if repo:
            cmd += ['--repo', repo]
        if release_notes.exists():
            cmd += ['--notes-file', str(release_notes)]
        else:
            cmd += ['--generate-notes']
        run_cmd(cmd, project_root)

        state.data['publish'] = {
            'target': 'github',
            'repo': repo,
            'tag': tag,
            'branch': branch,
            'release_notes': str(release_notes),
        }
        state.save()

        return {
            'target': 'github',
            'version': version_dir.name,
            'repo': repo,
            'tag': tag,
            'branch': branch,
            'release_notes': str(release_notes),
            'message': 'GitHub release 已创建。',
        }


ADAPTERS = {
    'github': GitHubPublishAdapter,
}


def run_publish(project_root: Path, config: dict, target: str, **kwargs):
    adapter_cls = ADAPTERS.get(target)
    if not adapter_cls:
        raise RuntimeError(f'不支持的 publish target: {target}')
    return adapter_cls().publish(project_root, config, **kwargs)
