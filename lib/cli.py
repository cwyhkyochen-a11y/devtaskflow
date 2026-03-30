import argparse
import os
from pathlib import Path

from config import find_project_root, load_config, validate_config, ConfigError
from doctor import run_doctor
from scaffold import init_project_structure
from analyze import run_analyze
from project import get_current_version_dir
from state import StateManager
from write_flow import run_write
from review_flow import run_review
from fix_flow import run_fix
from release_flow import run_deploy, run_seal, bump_version
from publish_flow import run_publish
from version_flow import create_version
from dashboard import build_dashboard
from serve import run_serve
from llm_risk import estimate_llm_risk, print_llm_risk
from workspace_layout import resolve_project_init_path, guess_workspace_root_for_init
from project_board import find_workspace_root, load_projects, DEFAULT_PROJECTS_FILE
from error_handling import mark_command_failed
from ux import build_status_explanation, build_next_step_hint
from requirement_guidance import render_requirement_guidance
from human_summary import (
    render_analyze_summary,
    render_review_summary,
    render_write_summary,
    render_fix_summary,
    render_next_step,
)
from setup_flow import run_setup
from auto_advance import auto_advance


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / 'templates'


def _mask_host(host: str) -> str:
    """对主机地址进行脱敏，保留前缀和后缀，中间用 * 替代。"""
    if not host:
        return ''
    # IP 地址：保留第一段
    parts = host.split('.')
    if len(parts) == 4:
        return f'{parts[0]}.*.*.{parts[3]}'
    # 域名：保留首尾字符
    if len(host) <= 4:
        return host[0] + '***'
    return host[:2] + '***' + host[-2:]


def list_projects(start: Path):
    workspace_root = find_workspace_root(start)
    return load_projects(workspace_root / DEFAULT_PROJECTS_FILE)


def get_project_by_name(name: str, start: Path):
    projects = list_projects(start)
    for project in projects:
        if project.get('name') == name:
            return project
    raise RuntimeError(f'项目不存在: {name}')


def find_next_version(project_root: Path, config: dict, new_project: bool = False) -> str:
    versions_dir = project_root / config['pipeline'].get('versions_dir', 'versions')
    if new_project or not versions_dir.exists():
        return 'v0.1.0'
    versions = sorted([p.name for p in versions_dir.iterdir() if p.is_dir() and p.name.startswith('v')])
    if not versions:
        return 'v0.1.0'
    return bump_version(versions[-1], 'patch')


# ============================================================
# 核心命令 1: setup — 依赖初始化
# ============================================================

def cmd_setup(args):
    root = find_project_root()
    mode = getattr(args, 'mode', None)
    return run_setup(project_root=root, mode=mode)


# ============================================================
# 核心命令 2: start — 开始/继续项目
# ============================================================

def cmd_start(args):
    # 找到或创建项目
    workspace_root = guess_workspace_root_for_init(Path.cwd())
    project_name = args.name or 'my-project'
    project_root = resolve_project_init_path(workspace_root, args.path, project_name)

    # 如果项目不存在，先初始化
    if not (project_root / '.dtflow' / 'config.json').exists():
        init_project_structure(project_root, TEMPLATES_DIR, project_name=project_name, workspace_root=workspace_root)
        print(f'✅ 已为你创建项目 {project_name}')

    try:
        config = load_config(project_root)
        validate_config(config)
    except ConfigError as e:
        print(f'\n⚠️ 配置有问题：{e}')
        print('   建议先运行 dtflow setup 配置 AI 服务。')
        return 1

    # 检查是否有进行中的版本
    version_dir = get_current_version_dir(project_root, config)
    has_version = version_dir and (version_dir / '.state.json').exists()

    if not has_version:
        # 全新项目：需要 --idea
        if not args.idea:
            print('\n📋 这是一个新项目，先告诉我你想做什么吧。')
            print('   运行 dtflow start --idea "用自然语言描述你的需求"')
            return 0

        # 创建版本 + 写入需求
        version = args.version or find_next_version(project_root, config, new_project=args.new_project)
        try:
            result = create_version(
                project_root, config, version,
                mode='new' if args.new_project else 'iterate',
                requirements_text=args.idea,
            )
        except Exception as e:
            print(f'\n⚠️ 创建项目时出了问题：{e}')
            return 1

        print(f'\n✅ 已为你启动项目 {project_name}（版本 {version}）')
        print(f'   需求文档：{result["requirements_file"]}')

        # 给出需求建议
        print('\n💡 需求建议：')
        print(render_requirement_guidance(args.idea))
        print('\n   如果你觉得有帮助，把补充内容直接追加到需求里就行。')

    # 根据参数决定行为
    try:
        if args.confirm:
            return 0 if auto_advance(project_root, action='confirm')['status'] != 'failed' else 1
        if args.confirm_write:
            return 0 if auto_advance(project_root, action='confirm_write')['status'] != 'failed' else 1
        if args.feedback:
            return 0 if auto_advance(project_root, action='revise', feedback=args.feedback)['status'] != 'failed' else 1
        if args.run:
            from run_flow import run_flow
            result = run_flow(project_root, config)
            url = result.get('url', '')
            status = result.get('status', '')
            if status == 'already_running':
                print(f'✅ 服务已在运行：{url}')
            elif status == 'running':
                print(f'✅ 预览已启动：{url}')
            else:
                print(f'⏳ 服务正在启动：{url}')
                print(f'   {result.get("message", "")}')
            return 0
        if args.stop:
            from run_flow import stop_run
            result = stop_run(project_root, config)
            print(f'✅ {result.get("message", "")}')
            return 0
        if args.deploy:
            return 0 if auto_advance(project_root, action='deploy')['status'] != 'failed' else 1
        if args.final_review:
            return 0 if auto_advance(project_root, action='final_review')['status'] != 'failed' else 1
        if args.deploy_skip_review:
            return 0 if auto_advance(project_root, action='deploy-skip-review')['status'] != 'failed' else 1
        if args.final_review:
            return 0 if auto_advance(project_root, action='final_review')['status'] != 'failed' else 1
        if args.deploy_skip_review:
            return 0 if auto_advance(project_root, action='deploy-skip-review')['status'] != 'failed' else 1

        # 默认：自动推进
        result = auto_advance(project_root, action='continue')
        return 0 if result.get('status') != 'failed' else 1

    except Exception as e:
        print(f'\n⚠️ 出了点问题：{e}')
        return 1


# ============================================================
# 核心命令 3: board — 项目看板
# ============================================================

def cmd_board(args):
    import subprocess
    import json as _json

    board_dir = BASE_DIR / 'board'

    if args.serve:
        # 启动 Node.js 看板服务
        if not (board_dir / 'node_modules').exists():
            print('⏳ 首次使用，正在安装看板依赖...')
            subprocess.run(['npm', 'install'], cwd=board_dir, check=True)

        # 确定工作区路径
        try:
            workspace_root = find_workspace_root(Path.cwd())
        except Exception:
            workspace_root = Path.cwd()

        port = args.port
        env = {**os.environ, 'DTFLOW_WORKSPACE': str(workspace_root), 'DTFLOW_BOARD_PORT': str(port)}

        # 检查端口是否已被占用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        in_use = sock.connect_ex(('127.0.0.1', port)) == 0
        sock.close()
        if in_use:
            print(f'✅ 看板已在运行：http://localhost:{port}')
            print('   如需重启，请先停止现有服务。')
            return 0

        print(f'🚀 正在启动看板服务...')
        print(f'   地址：http://localhost:{port}')
        print('   按 Ctrl+C 停止')
        try:
            subprocess.run(['node', 'server.js'], cwd=board_dir, env=env)
        except KeyboardInterrupt:
            print('\n已停止')
        return 0

    # 文字版看板 — 给 agent 在对话中使用
    try:
        workspace_root = find_workspace_root(Path.cwd())
    except Exception:
        workspace_root = Path.cwd()

    projects_file = workspace_root / DEFAULT_PROJECTS_FILE
    if not projects_file.exists():
        print('暂无项目。运行 dtflow start --idea "你的需求" 创建第一个项目。')
        return 0

    projects = load_projects(projects_file)
    if not projects:
        print('暂无项目。运行 dtflow start --idea "你的需求" 创建第一个项目。')
        return 0

    print()
    print('📊 项目看板')
    print('=' * 40)

    for idx, project in enumerate(projects, start=1):
        name = project.get('name', '未命名')
        status = project.get('status', '-')
        version = project.get('current_version', '-')
        updated = project.get('updated_at', '-')

        status_icon = {
            'active': '🟢', 'sealed': '📦', 'paused': '⏸️', 'failed': '🔴',
        }.get(status, '⚪')

        print(f'\n{idx}. {status_icon} {name}  [{version}]')
        print(f'   状态：{status}  |  更新：{updated}')

        # 读取详细状态
        try:
            proj_path = Path(project.get('path', ''))
            if (proj_path / '.dtflow' / 'config.json').exists():
                config = load_config(proj_path)
                vd = get_current_version_dir(proj_path, config)
                if vd and (vd / '.state.json').exists():
                    sm = StateManager(vd)
                    explanation = build_status_explanation(sm.data)
                    next_step = build_next_step_hint(sm.data)
                    print(f'   进度：{explanation}')
                    print(f'   下一步：{next_step}')

                    # 部署信息（脱敏显示）
                    deploy = config.get('deploy', {})
                    host = deploy.get('host', '')
                    deploy_path = deploy.get('path', '')
                    if host or deploy_path:
                        masked_host = _mask_host(host)
                        print(f'   部署：{masked_host}（已配置）' if host else f'   部署：已配置')
        except Exception:
            pass

        if project.get('note'):
            print(f'   备注：{project["note"]}')

    print(f'\n共 {len(projects)} 个项目。')
    return 0


# ============================================================
# 核心命令 board 的详细查询（agent 用）
# ============================================================

def cmd_board_query(args):
    """查询单个项目详情，文字输出（agent 向用户回复用）。"""
    try:
        workspace_root = find_workspace_root(Path.cwd())
    except Exception:
        workspace_root = Path.cwd()

    projects = load_projects(workspace_root / DEFAULT_PROJECTS_FILE)
    name = args.name

    project = None
    for p in projects:
        if p.get('name') == name:
            project = p
            break

    if not project:
        # 模糊匹配
        matches = [p for p in projects if name.lower() in p.get('name', '').lower()]
        if len(matches) == 1:
            project = matches[0]
        elif matches:
            print(f'找到多个匹配项目：')
            for m in matches:
                print(f'  - {m["name"]}')
            return 1
        else:
            print(f'未找到项目「{name}」。')
            return 1

    proj_path = Path(project.get('path', ''))
    status = project.get('status', '-')
    version = project.get('current_version', '-')

    status_icon = {
        'active': '🟢', 'sealed': '📦', 'paused': '⏸️', 'failed': '🔴',
    }.get(status, '⚪')

    print(f'{status_icon} {project["name"]}')
    print(f'版本：{version}  |  状态：{status}')
    print(f'更新时间：{project.get("updated_at", "-")}')

    # 详细状态
    try:
        config = load_config(proj_path)
        vd = get_current_version_dir(proj_path, config)
        if vd and (vd / '.state.json').exists():
            sm = StateManager(vd)
            print(f'流程进度：{build_status_explanation(sm.data)}')
            print(f'下一步：{build_next_step_hint(sm.data)}')

            # 任务列表
            tasks = sm.data.get('tasks', [])
            if tasks:
                done = sum(1 for t in tasks if t.get('status') == 'done')
                print(f'\n任务进度：{done}/{len(tasks)}')
                for t in tasks:
                    icon = '✅' if t.get('status') == 'done' else '⏳'
                    print(f'  {icon} [{t["id"]}] {t["name"]} ({t.get("priority", "")})')

            # 最近错误
            last_error = sm.data.get('last_error')
            if last_error:
                print(f'\n⚠️ 最近错误：{last_error}')

        # 部署信息（脱敏显示）
        deploy = config.get('deploy', {})
        host = deploy.get('host', '')
        if host:
            masked_host = _mask_host(host)
            print(f'\n📦 部署信息')
            print(f'  服务器：{masked_host}')
            build_cmd = deploy.get('build_command', '')
            print(f'  构建：{"已配置" if build_cmd else "未配置"}')
            deploy_cmd = deploy.get('deploy_command', '')
            print(f'  部署：{"已配置" if deploy_cmd else "未配置"}')

        # 需求摘要
        req_path = vd / 'docs' / 'REQUIREMENTS.md'
        if req_path.exists():
            req = req_path.read_text(encoding='utf-8')[:300]
            print(f'\n📝 需求摘要')
            print(f'  {req}{"..." if len(req_path.read_text(encoding="utf-8")) > 300 else ""}')

    except Exception as e:
        print(f'\n⚠️ 读取详情时出错：{e}')

    return 0


# ============================================================
# 高级命令（保留给高级用户）
# ============================================================

def cmd_advanced(args):
    """高级命令入口，打印帮助。"""
    print('DevTaskFlow 高级命令')
    print('=' * 40)
    print()
    print('以下命令供高级用户使用，普通用户使用 setup / start / board 即可。')
    print()
    print('可用命令：')
    print('  dtflow advanced status          查看项目详细状态')
    print('  dtflow advanced doctor          检查环境')
    print('  dtflow advanced analyze         手动执行需求分析')
    print('  dtflow advanced confirm         手动确认方案')
    print('  dtflow advanced write           手动生成代码')
    print('  dtflow advanced review          手动审查代码')
    print('  dtflow advanced fix             手动修复问题')
    print('  dtflow advanced deploy          手动部署')
    print('  dtflow advanced seal            手动封版')
    print('  dtflow advanced publish         发布到 GitHub / ClawHub')
    print('  dtflow advanced rollback        回滚到检查点')
    print('  dtflow advanced recover         自动检测修复状态异常')
    print('  dtflow advanced next-version    计算下一个版本号')
    print('  dtflow advanced project-list    项目列表（原始格式）')
    print('  dtflow advanced project-status  单项目状态')
    print('  dtflow advanced dashboard       生成 HTML 看板文件')
    print('  dtflow advanced demo            查看示例项目')
    return 0


def cmd_adv_status(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。先运行 dtflow setup 或 dtflow start --idea "需求"。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
    except ConfigError as e:
        print(f'⚠️ 配置有问题：{e}')
        return 1
    print('DevTaskFlow 详细状态')
    print('=' * 40)
    print(f'项目目录：{root}')
    print(f'项目名称：{config["project"].get("name")}')
    print(f'开发语言：{config["project"].get("language")}')
    print(f'编排模式：{config["adapters"].get("orchestration")}')
    version_dir = get_current_version_dir(root, config)
    if version_dir and (version_dir / '.state.json').exists():
        state = StateManager(version_dir)
        print(f'当前版本：{version_dir.name}')
        print(f'流程状态：{state.data.get("status")}')
        print(f'当前任务：{state.data.get("current_task") or "-"}')
        print(f'最近操作：{state.data.get("last_action") or "-"}')
        print(f'结果格式：{state.data.get("last_result_format") or "-"}')
        print(f'最近摘要：{state.data.get("last_summary") or "-"}')
        print(f'最近错误：{state.data.get("last_error") or "-"}')
        print(f'状态说明：{build_status_explanation(state.data)}')
        print(f'下一步建议：{build_next_step_hint(state.data)}')
    try:
        project = get_project_by_name(config['project']['name'], root)
        print(f'看板状态：{project.get("status")}')
        print(f'看板版本：{project.get("current_version")}')
    except Exception:
        pass
    return 0


def cmd_adv_doctor(args):
    checks = run_doctor()
    ok = True
    print('环境检查')
    print('=' * 40)
    for name, passed, detail in checks:
        mark = '✅' if passed else '❌'
        print(f'{mark} {name}: {detail}')
        if not passed:
            ok = False
    if not ok:
        print('\n有检查项未通过，建议运行 dtflow setup 重新配置。')
    return 0 if ok else 1


def cmd_adv_analyze(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        print_llm_risk(estimate_llm_risk(root, config, 'analyze'))
        result = run_analyze(root, config)
    except Exception as e:
        mark_command_failed(root, 'analyze', e)
        print(f'⚠️ 分析失败：{e}')
        return 1
    print('✅ analyze 完成')
    print(f"- 方案文件：{result['plan_file']}")
    print(f"- 任务数：{result['task_count']}")
    for task in result['tasks'][:10]:
        print(f"  - [{task['id']}] {task['name']} ({task['priority']})")
    print('\n下一步：dtflow start --confirm')
    return 0


def cmd_adv_confirm(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        version_dir = get_current_version_dir(root, config)
        if not version_dir:
            raise RuntimeError('没有找到当前版本目录')
        state = StateManager(version_dir)
        if state.data.get('status') != 'pending_confirm':
            raise RuntimeError(f'当前状态不是待确认，而是 {state.data.get("status")}')
        state.data['architecture_confirmed'] = True
        state.data['status'] = 'confirmed'
        state.data['last_action'] = 'confirm'
        tasks = state.data.get('tasks', [])
        state.data['current_task'] = tasks[0]['id'] if tasks else None
        state.save()
    except Exception as e:
        print(f'⚠️ 确认失败：{e}')
        return 1
    print('✅ 方案已确认')
    print('下一步：dtflow advanced write --dry-run')
    return 0


def cmd_adv_write(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        print_llm_risk(estimate_llm_risk(root, config, 'write'))
        result = run_write(root, config, task_id=args.task_id, dry_run=args.dry_run)
    except Exception as e:
        mark_command_failed(root, 'write', e)
        print(f'⚠️ 生成失败：{e}')
        return 1
    print('✅ write 完成')
    print(f"- 任务：[{result['task_id']}] {result['task_name']}")
    print(f"- 文件数：{result['count']}")
    for item in result['files'][:20]:
        print(f"  - {item['action']}: {item['path']}")
    print('\n下一步：' + ('确认预览后再次执行 dtflow advanced write' if result.get('dry_run') else 'dtflow advanced review'))
    return 0


def cmd_adv_review(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        print_llm_risk(estimate_llm_risk(root, config, 'review'))
        result = run_review(root, config)
    except Exception as e:
        mark_command_failed(root, 'review', e)
        print(f'⚠️ 审查失败：{e}')
        return 1
    print('✅ review 完成')
    print(f"- 通过：{result['passed']}")
    print('\n下一步：' + ('dtflow start --deploy 或继续下一个任务' if result['passed'] else 'dtflow advanced fix'))
    return 0


def cmd_adv_fix(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        print_llm_risk(estimate_llm_risk(root, config, 'fix'))
        result = run_fix(root, config)
    except Exception as e:
        mark_command_failed(root, 'fix', e)
        print(f'⚠️ 修复失败：{e}')
        return 1
    print('✅ fix 完成')
    print(f"- 文件数：{result['count']}")
    print('\n下一步：dtflow advanced review')
    return 0


def cmd_adv_deploy(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        version_dir = get_current_version_dir(root, config)
        if version_dir and (version_dir / '.state.json').exists():
            state = StateManager(version_dir)
            state.data['status'] = 'deploying'
            state.data['last_action'] = 'deploy'
            state.data['last_error'] = None
            state.save()
        result = run_deploy(root, config)
    except Exception as e:
        print(f'⚠️ 部署失败：{e}')
        return 1
    print('✅ deploy 完成')
    print(f"- 版本：{result['version']}")
    print('\n下一步：dtflow advanced seal')
    return 0


def cmd_adv_seal(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        result = run_seal(root, config)
        version_dir = get_current_version_dir(root, config)
        if version_dir and (version_dir / '.state.json').exists():
            state = StateManager(version_dir)
            state.data['status'] = 'sealed'
            state.data['last_action'] = 'seal'
            state.data['last_error'] = None
            state.save()
    except Exception as e:
        print(f'⚠️ 封版失败：{e}')
        return 1
    print('✅ seal 完成')
    print(f"- 版本：{result['version']}")
    if result.get('next_version'):
        print(f"\n🚀 下一个版本 {result['next_version']} 已就绪")
        print(f"   运行 dtflow start --idea \"新需求\" 开始新版本开发")
    return 0


def cmd_adv_publish(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        validate_config(config)
        result = run_publish(
            root, config, args.target,
            allow_dirty=args.allow_dirty,
            force_tag=args.force_tag,
            replace_release=args.replace_release,
        )
    except Exception as e:
        print(f'⚠️ 发布失败：{e}')
        return 1
    print('✅ publish 完成')
    print(f"- 目标：{result['target']}")
    print(f"- 版本：{result['version']}")
    return 0


def cmd_adv_next_version(args):
    if not args.version:
        print('请通过 --version 指定当前版本号')
        return 1
    try:
        next_version = bump_version(args.version, args.bump)
    except Exception as e:
        print(f'⚠️ 计算失败：{e}')
        return 1
    print(next_version)
    return 0


def cmd_adv_project_list(args):
    projects = list_projects(Path.cwd())
    print('项目列表')
    print('=' * 40)
    if not projects:
        print('暂无项目')
        return 0
    for idx, project in enumerate(projects, start=1):
        print(f"{idx}. {project['name']}")
        print(f"   - status: {project.get('status', '-')}")
        print(f"   - version: {project.get('current_version', '-')}")
        print(f"   - path: {project.get('path', '-')}")
    return 0


def cmd_adv_project_status(args):
    if not args.name:
        print('请通过 --name 指定项目名')
        return 1
    try:
        project = get_project_by_name(args.name, Path.cwd())
    except Exception as e:
        print(f'⚠️ 查询失败：{e}')
        return 1
    for key in ['name', 'status', 'current_version', 'path', 'updated_at', 'note']:
        print(f'{key}: {project.get(key, "-")}')
    return 0


def cmd_adv_dashboard(args):
    try:
        result = build_dashboard(Path.cwd())
    except Exception as e:
        print(f'⚠️ 生成失败：{e}')
        return 1
    print('✅ HTML 看板已生成')
    print(f"- 文件：{result['dashboard_path']}")
    return 0


def cmd_adv_demo(args):
    demo_root = BASE_DIR / 'example-project'
    print('示例项目')
    print('=' * 40)
    print(f'位置：{demo_root}')
    print()
    print('体验步骤：')
    print('1. cd 到 example-project')
    print('2. 运行 dtflow board 查看状态')
    print('3. 查看 versions/v0.1.0/docs/REQUIREMENTS.md 了解需求格式')
    print('4. 配好 AI 后运行 dtflow start 体验完整流程')
    return 0


# ============================================================
# 高级命令: rollback — 回滚到检查点
# ============================================================

def cmd_adv_rollback(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        version_dir = get_current_version_dir(root, config)
        if not version_dir:
            raise RuntimeError('没有找到当前版本目录')
        state = StateManager(version_dir)
    except Exception as e:
        print(f'⚠️ 加载失败：{e}')
        return 1

    if args.list:
        checkpoints = state.list_checkpoints()
        if not checkpoints:
            print('当前没有任何检查点。')
            print('检查点会在关键操作前自动创建（write、deploy、seal）。')
            return 0
        print('📸 可用检查点')
        print('=' * 40)
        for label, ts in checkpoints:
            print(f'  {label}  ({ts})')
        print(f'\n共 {len(checkpoints)} 个检查点。')
        print('使用 dtflow advanced rollback --to <label> 回滚到指定检查点。')
        return 0

    if not args.to:
        print('请指定要回滚到的检查点：')
        print('  dtflow advanced rollback --list        查看可用检查点')
        print('  dtflow advanced rollback --to <label>  回滚到指定检查点')
        return 1

    try:
        state.restore_checkpoint(args.to)
    except FileNotFoundError as e:
        print(f'⚠️ {e}')
        return 1
    except Exception as e:
        print(f'⚠️ 回滚失败：{e}')
        return 1

    print(f'当前状态：{state.data.get("status", "-")}')
    print(f'当前任务：{state.data.get("current_task") or "-"}')
    print('\n👉 运行 dtflow advanced status 查看详细状态')
    print('   运行 dtflow start 继续执行')
    return 0


# ============================================================
# 高级命令: recover — 自动检测修复状态异常
# ============================================================

def cmd_adv_recover(args):
    root = find_project_root()
    if not root:
        print('⚠️ 当前目录不是 DevTaskFlow 项目。')
        return 1
    try:
        config = load_config(root)
        version_dir = get_current_version_dir(root, config)
        if not version_dir:
            raise RuntimeError('没有找到当前版本目录')
        state = StateManager(version_dir)
    except Exception as e:
        print(f'⚠️ 加载失败：{e}')
        return 1

    status = state.data.get('status', 'unknown')
    fixes_applied = []

    print('🔍 正在检测状态异常...')
    print('=' * 40)

    # 检查 1: state 存在但 plan_markdown 不存在
    if status in ('pending_confirm', 'confirmed', 'writing', 'written'):
        plan_file = version_dir / 'docs' / 'PLAN.md'
        if not plan_file.exists():
            print(f'⚠️ 状态为「{status}」但方案文件不存在')
            print('   → 重置状态为 created，需要重新分析')
            state.data['status'] = 'created'
            state.data['architecture_confirmed'] = False
            state.save()
            fixes_applied.append('重置状态为 created（方案文件缺失）')

    # 检查 2: state 为 written 但 src 目录为空
    if status in ('written', 'review_passed'):
        src_dir = version_dir / 'src'
        if not src_dir.exists() or not any(src_dir.iterdir()):
            print(f'⚠️ 状态为「{status}」但 src 目录为空')
            print('   → 需要重新 write')
            state.data['status'] = 'confirmed'
            state.save()
            fixes_applied.append(f'状态从 {status} 回退为 confirmed（src 目录为空）')

    # 检查 3: state 为 deployed 但没有部署记录
    if status == 'deployed':
        deploy_log = version_dir / '.deploy.log'
        deploy_dir = version_dir / 'deploy'
        has_deploy_record = deploy_log.exists() or (deploy_dir.exists() and any(deploy_dir.iterdir()))
        if not has_deploy_record:
            print('⚠️ 状态为 deployed 但没有部署记录')
            print('   → 状态回退为 review_passed')
            state.data['status'] = 'review_passed'
            state.save()
            fixes_applied.append('状态从 deployed 回退为 review_passed（无部署记录）')

    # 检查 4: state 为 failed 但 last_error 为空
    if status == 'failed':
        last_error = state.data.get('last_error')
        if not last_error:
            print('⚠️ 状态为 failed 但没有错误信息')
            print('   → 清除 failed 状态')
            state.data['status'] = state.data.get('last_status', 'created')
            state.data['last_error'] = None
            state.save()
            fixes_applied.append('清除 failed 状态（无错误详情）')

    # 检查 5: 状态异常值
    valid_statuses = {
        'created', 'pending_confirm', 'confirmed', 'writing', 'written',
        'needs_fix', 'failed', 'review_passed', 'pending_final_review',
        'ready_to_deploy', 'deploying', 'deployed', 'sealed',
        'needs_final_fix', 'initialized',
    }
    if status not in valid_statuses:
        print(f'⚠️ 状态值异常：「{status}」')
        print('   → 重置为 created')
        state.data['status'] = 'created'
        state.save()
        fixes_applied.append(f'重置异常状态「{status}」为 created')

    # 检查 6: 检查点目录是否存在
    cp_dir = version_dir / '.checkpoints'
    if cp_dir.exists():
        cp_count = len(list(cp_dir.glob('*.json')))
        print(f'📸 检查点：{cp_count} 个可用')
        if cp_count > 0:
            print('   如需回滚：dtflow advanced rollback --list')

    # 总结
    print()
    if fixes_applied:
        print(f'✅ 已修复 {len(fixes_applied)} 个问题：')
        for fix in fixes_applied:
            print(f'   ✓ {fix}')
        print(f'\n当前状态：{state.data.get("status")}')
        print('👉 运行 dtflow start 继续执行')
    else:
        print('✅ 未发现异常。')
        print(f'   当前状态：{status}')
        print('   如果仍有问题，可以尝试：')
        print('   - dtflow advanced rollback --list  查看检查点并回滚')
        print('   - dtflow advanced status  查看详细状态')

    return 0


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog='dtflow',
        description='DevTaskFlow — 用自然语言描述需求，AI 帮你做开发',
    )
    subparsers = parser.add_subparsers(dest='command')

    # --- 核心命令 ---

    p_setup = subparsers.add_parser('setup', help='配置 AI 服务（首次使用必做）')
    p_setup.add_argument('--mode', choices=['auto', 'guided', 'advanced'],
                          help='配置模式：auto=自动检测, guided=引导式, advanced=高级')
    p_setup.set_defaults(func=cmd_setup)

    p_start = subparsers.add_parser('start', help='开始或继续一个项目')
    p_start.add_argument('--name', help='项目名称')
    p_start.add_argument('--path', help='项目路径')
    p_start.add_argument('--version', help='版本号')
    p_start.add_argument('--new-project', action='store_true', help='新项目首版')
    p_start.add_argument('--idea', help='用自然语言描述你的需求')
    p_start.add_argument('--confirm', action='store_true', help='确认分析方案')
    p_start.add_argument('--confirm-write', action='store_true', help='确认预览后正式生成代码')
    p_start.add_argument('--feedback', help='对分析方案提出修改意见')
    p_start.add_argument('--run', action='store_true', help='本地预览')
    p_start.add_argument('--stop', action='store_true', help='停止本地预览')
    p_start.add_argument('--deploy', action='store_true', help='部署上线并封版')
    p_start.add_argument('--final-review', action='store_true', help='执行上线前综合审查')
    p_start.add_argument('--deploy-skip-review', action='store_true', help='跳过综合审查直接部署')
    p_start.set_defaults(func=cmd_start)

    p_board = subparsers.add_parser('board', help='查看所有项目状态')
    p_board.add_argument('--serve', action='store_true', help='启动可视化看板')
    p_board.add_argument('--port', type=int, default=8765, help='看板端口')
    p_board.set_defaults(func=cmd_board)

    p_bq = subparsers.add_parser('board-query', help='查看单个项目详情')
    p_bq.add_argument('--name', required=True, help='项目名称（支持模糊匹配）')
    p_bq.set_defaults(func=cmd_board_query)

    # --- 高级命令 ---

    p_advanced = subparsers.add_parser('advanced', help='高级命令（给需要精细控制的用户）')
    advanced_sub = p_advanced.add_subparsers(dest='adv_command')

    p_adv_status = advanced_sub.add_parser('status', help='查看详细状态')
    p_adv_status.set_defaults(func=cmd_adv_status)

    p_adv_doctor = advanced_sub.add_parser('doctor', help='检查环境')
    p_adv_doctor.set_defaults(func=cmd_adv_doctor)

    p_adv_analyze = advanced_sub.add_parser('analyze', help='手动执行需求分析')
    p_adv_analyze.set_defaults(func=cmd_adv_analyze)

    p_adv_confirm = advanced_sub.add_parser('confirm', help='手动确认方案')
    p_adv_confirm.set_defaults(func=cmd_adv_confirm)

    p_adv_write = advanced_sub.add_parser('write', help='手动生成代码')
    p_adv_write.add_argument('--task-id', help='指定任务 ID')
    p_adv_write.add_argument('--dry-run', action='store_true', help='仅预览')
    p_adv_write.set_defaults(func=cmd_adv_write)

    p_adv_review = advanced_sub.add_parser('review', help='手动审查代码')
    p_adv_review.set_defaults(func=cmd_adv_review)

    p_adv_fix = advanced_sub.add_parser('fix', help='手动修复问题')
    p_adv_fix.set_defaults(func=cmd_adv_fix)

    p_adv_deploy = advanced_sub.add_parser('deploy', help='手动部署')
    p_adv_deploy.set_defaults(func=cmd_adv_deploy)

    p_adv_seal = advanced_sub.add_parser('seal', help='手动封版')
    p_adv_seal.set_defaults(func=cmd_adv_seal)

    p_adv_publish = advanced_sub.add_parser('publish', help='发布到 GitHub / ClawHub')
    p_adv_publish.add_argument('--target', default='github', choices=['github', 'clawhub'])
    p_adv_publish.add_argument('--allow-dirty', action='store_true')
    p_adv_publish.add_argument('--force-tag', action='store_true')
    p_adv_publish.add_argument('--replace-release', action='store_true')
    p_adv_publish.set_defaults(func=cmd_adv_publish)

    p_adv_nv = advanced_sub.add_parser('next-version', help='计算下一个版本号')
    p_adv_nv.add_argument('--version', required=True)
    p_adv_nv.add_argument('--bump', choices=['major', 'minor', 'patch'], default='patch')
    p_adv_nv.set_defaults(func=cmd_adv_next_version)

    p_adv_pl = advanced_sub.add_parser('project-list', help='项目列表')
    p_adv_pl.set_defaults(func=cmd_adv_project_list)

    p_adv_ps = advanced_sub.add_parser('project-status', help='单项目状态')
    p_adv_ps.add_argument('--name', required=True)
    p_adv_ps.set_defaults(func=cmd_adv_project_status)

    p_adv_dash = advanced_sub.add_parser('dashboard', help='生成 HTML 看板文件')
    p_adv_dash.set_defaults(func=cmd_adv_dashboard)

    p_adv_demo = advanced_sub.add_parser('demo', help='查看示例项目')
    p_adv_demo.set_defaults(func=cmd_adv_demo)

    p_adv_rb = advanced_sub.add_parser('rollback', help='回滚到检查点')
    p_adv_rb.add_argument('--to', help='检查点标签')
    p_adv_rb.add_argument('--list', action='store_true', help='列出所有检查点')
    p_adv_rb.set_defaults(func=cmd_adv_rollback)

    p_adv_rc = advanced_sub.add_parser('recover', help='自动检测修复状态异常')
    p_adv_rc.set_defaults(func=cmd_adv_recover)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    return args.func(args)
