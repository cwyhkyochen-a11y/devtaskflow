from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess

from project import get_current_version_dir
from state import StateManager
from deploy_adapter import run_deploy_adapter


def bump_version(version: str, bump: str = 'patch'):
    if not version.startswith('v'):
        raise ValueError('版本号必须以 v 开头，例如 v1.2.3')
    parts = version[1:].split('.')
    if len(parts) != 3:
        raise ValueError('版本号必须是语义化版本，例如 v1.2.3')
    major, minor, patch = map(int, parts)
    if bump == 'major':
        return f'v{major + 1}.0.0'
    if bump == 'minor':
        return f'v{major}.{minor + 1}.0'
    return f'v{major}.{minor}.{patch + 1}'


def generate_changelog(version_dir: Path, tasks: list, version: str):
    changelog_file = version_dir / 'docs' / 'CHANGELOG.md'
    if changelog_file.exists():
        return changelog_file

    today = datetime.now().strftime('%Y-%m-%d')
    done = [t for t in tasks if t.get('status') == 'done']
    not_done = [t for t in tasks if t.get('status') != 'done']

    lines = [
        '# CHANGELOG',
        '',
        f'## {version} ({today})',
        '',
    ]

    if done:
        lines.append('### ✅ 已完成')
        for t in done:
            lines.append(f"- {t.get('name', t.get('id', '?'))}")
        lines.append('')

    if not_done:
        lines.append('### ⚠️ 未完成')
        for t in not_done:
            priority = t.get('priority', '')
            name = t.get('name', t.get('id', '?'))
            if priority:
                lines.append(f"- {name} ({priority})")
            else:
                lines.append(f"- {name}")
        lines.append('')

    lines.append('---')
    lines.append('')

    changelog_file.parent.mkdir(parents=True, exist_ok=True)
    changelog_file.write_text('\n'.join(lines), encoding='utf-8')
    return changelog_file


def create_next_version_dir(project_root: Path, config: dict, current_version: str):
    next_ver = bump_version(current_version, 'patch')
    versions_dir = project_root / config.get('pipeline', {}).get('versions_dir', 'versions')
    next_dir = versions_dir / next_ver
    next_dir.mkdir(parents=True, exist_ok=True)
    (next_dir / 'docs').mkdir(exist_ok=True)
    (next_dir / 'src').mkdir(exist_ok=True)

    now = datetime.now().isoformat()
    state_data = {
        'version': next_ver,
        'status': 'created',
        'current_task': None,
        'architecture_confirmed': False,
        'tasks': [],
        'created_at': now,
        'updated_at': now,
        'last_error': None,
        'last_action': None,
        'last_result_format': None,
        'last_summary': '',
    }
    (next_dir / '.state.json').write_text(
        json.dumps(state_data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    return next_ver, next_dir


def ensure_deployment_guide(project_root: Path, version_dir: Path, config=None):
    deploy_guide = version_dir / 'docs' / 'DEPLOYMENT.md'
    if deploy_guide.exists():
        return deploy_guide

    if config is None:
        config = {}

    deploy_cfg = config.get('deploy', {})
    project_name = config.get('project', {}).get('name', project_root.name)
    host = deploy_cfg.get('host', '待配置')
    user = deploy_cfg.get('user', '待配置')
    deploy_path = deploy_cfg.get('path', '待配置')
    build_command = deploy_cfg.get('build_command', '待配置')
    deploy_command = deploy_cfg.get('deploy_command', '待配置')
    restart_command = deploy_cfg.get('restart_command', '待配置')

    content = f"""# DEPLOYMENT

## 版本信息
- 版本: {version_dir.name}
- 项目: {project_name}

## 服务器
- 地址: {host}
- 用户: {user}
- 部署目录: {deploy_path}

## 部署命令
- 构建: {build_command}
- 启动: {deploy_command}
- 重启: {restart_command}

## 回滚方式
- 源码备份: versions/{version_dir.name}/archive/src/
- 回滚步骤: 将 archive/src/ 的内容复制回项目根目录，然后重启服务
"""
    deploy_guide.parent.mkdir(parents=True, exist_ok=True)
    deploy_guide.write_text(content, encoding='utf-8')
    return deploy_guide


def archive_docs(version_dir: Path):
    docs_dir = version_dir / 'docs'
    docs_archive = version_dir / 'archive' / 'docs'
    docs_archive.mkdir(parents=True, exist_ok=True)
    copied = []
    for file in docs_dir.iterdir():
        if file.is_file():
            shutil.copy2(file, docs_archive / file.name)
            copied.append(file.name)
    return docs_archive, copied


def archive_source(project_root: Path, version_dir: Path):
    src_dir = version_dir / 'archive' / 'src'
    src_dir.mkdir(parents=True, exist_ok=True)

    exclude = {'versions', '.dtflow', '.git', 'node_modules', '__pycache__', 'PROJECTS.md', 'dtflow-dashboard.html'}
    copied = 0
    for item in project_root.iterdir():
        if item.name in exclude:
            continue
        dest = src_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
            copied += 1
        elif item.is_file():
            shutil.copy2(item, dest)
            copied += 1

    (src_dir / '.version').write_text(version_dir.name, encoding='utf-8')
    return src_dir, copied


def git_commit_release(project_root: Path, version: str):
    """封版时执行 git add + commit + tag"""
    result = {'git_add': None, 'git_commit': None, 'git_tag': None, 'errors': []}

    from git_utils import ensure_git_repo
    repo_result = ensure_git_repo(project_root)
    if repo_result.get('error'):
        result['errors'].append(repo_result['error'])
        return result

    try:
        # git add .
        r = subprocess.run(
            ['git', 'add', '.'],
            cwd=str(project_root), capture_output=True, text=True, timeout=30
        )
        result['git_add'] = r.returncode == 0
        if r.returncode != 0:
            result['errors'].append(f'git add failed: {r.stderr.strip()}')

        # git commit
        commit_msg = f'release: {version} 封版'
        r = subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=str(project_root), capture_output=True, text=True, timeout=30
        )
        result['git_commit'] = r.returncode == 0
        if r.returncode != 0:
            # "nothing to commit" 不算错误
            if 'nothing to commit' in r.stdout or 'nothing to commit' in r.stderr:
                result['git_commit'] = True
            else:
                result['errors'].append(f'git commit failed: {r.stderr.strip()}')

        # git tag
        r = subprocess.run(
            ['git', 'tag', version],
            cwd=str(project_root), capture_output=True, text=True, timeout=30
        )
        result['git_tag'] = r.returncode == 0
        if r.returncode != 0:
            result['errors'].append(f'git tag failed: {r.stderr.strip()}')

    except FileNotFoundError:
        result['errors'].append('git 未安装')
    except subprocess.TimeoutExpired:
        result['errors'].append('git 命令超时')
    except Exception as e:
        result['errors'].append(f'git 操作异常: {str(e)}')

    return result


def run_deploy(project_root: Path, config: dict):
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录')

    state = StateManager(version_dir)
    allowed = {'review_passed', 'all_done', 'deployed'}
    if state.data.get('status') not in allowed:
        raise RuntimeError(f"当前状态不允许 deploy: {state.data.get('status')}")

    adapter_result = run_deploy_adapter(project_root, config)
    state.data['status'] = 'deployed'
    state.data['deploy'] = adapter_result
    state.save()

    return {
        'version': version_dir.name,
        'mode': config.get('adapters', {}).get('deploy', 'shell'),
        'adapter': adapter_result,
        'message': 'deploy 已切到 adapter 模式，当前仍为骨架实现。',
    }


def run_seal(project_root: Path, config: dict):
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('没有找到当前版本目录')

    state = StateManager(version_dir)
    if state.data.get('status') not in {'deployed', 'review_passed', 'all_done'}:
        raise RuntimeError(f"当前状态不允许 seal: {state.data.get('status')}")

    # 生成 CHANGELOG
    tasks = state.data.get('tasks', [])
    changelog_file = generate_changelog(version_dir, tasks, version_dir.name)

    deployment_file = ensure_deployment_guide(project_root, version_dir, config)
    docs_archive, docs_files = archive_docs(version_dir)
    src_dir, src_count = archive_source(project_root, version_dir)

    state.data['status'] = 'sealed'
    state.data['archive'] = {
        'docs_dir': str(docs_archive),
        'src_dir': str(src_dir),
        'deployment_file': str(deployment_file),
        'docs_files': docs_files,
        'src_items': src_count,
    }
    state.save()

    # Git 封版操作
    git_result = git_commit_release(project_root, version_dir.name)

    # 自动创建下一版本目录
    next_version, next_dir = create_next_version_dir(project_root, config, version_dir.name)

    return {
        'version': version_dir.name,
        'docs_dir': str(docs_archive),
        'src_dir': str(src_dir),
        'deployment_file': str(deployment_file),
        'docs_files': docs_files,
        'src_items': src_count,
        'changelog_file': str(changelog_file),
        'next_version': next_version,
        'git': git_result,
    }
