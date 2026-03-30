import shutil
from pathlib import Path

from git_utils import ensure_git_repo
from project_board import find_workspace_root, register_project


def init_project_structure(project_root: Path, templates_dir: Path, project_name: str | None = None, workspace_root: Path | None = None):
    dtflow_dir = project_root / '.dtflow'
    versions_dir = project_root / 'versions'
    docs_dir = project_root / 'docs'

    dtflow_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    config_src = templates_dir / 'config.json'
    env_src = templates_dir / 'env.example'

    config_dst = dtflow_dir / 'config.json'
    env_dst = project_root / '.env.dtflow.example'

    if not config_dst.exists():
        shutil.copy2(config_src, config_dst)
    if not env_dst.exists():
        shutil.copy2(env_src, env_dst)

    final_name = project_name or project_root.name
    config_text = config_dst.read_text(encoding='utf-8')
    config_text = config_text.replace('your-project-name', final_name)
    config_dst.write_text(config_text, encoding='utf-8')

    workspace_root = workspace_root or find_workspace_root(project_root)
    project_rel_path = str(project_root.resolve().relative_to(workspace_root.resolve())) if str(project_root.resolve()).startswith(str(workspace_root.resolve())) else str(project_root.resolve())
    board_item = register_project(workspace_root, final_name, project_rel_path)

    # 自动初始化 git 仓库
    git_result = ensure_git_repo(project_root)
    if git_result.get('error'):
        print(f"⚠️ Git 初始化警告: {git_result['error']}")

    return {
        'dtflow_dir': str(dtflow_dir),
        'versions_dir': str(versions_dir),
        'docs_dir': str(docs_dir),
        'config': str(config_dst),
        'env_example': str(env_dst),
        'board_project': board_item['name'],
        'board_file': str(workspace_root / 'PROJECTS.md'),
        'git': git_result,
    }
