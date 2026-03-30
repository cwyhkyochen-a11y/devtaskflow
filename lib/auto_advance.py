"""状态机自动推进 — 根据当前状态自动执行下一步。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from state import StateManager
from project import get_current_version_dir
from llm_risk import estimate_llm_risk, print_llm_risk
from error_handling import mark_command_failed, retry_with_backoff


# 状态流转表：每个状态对应 (下一步动作, 执行函数获取器)
# 由 auto_advance 函数按需导入，避免循环引用


def _get_config_and_state(project_root: Path) -> tuple[dict, StateManager, Path]:
    """加载 config 和 state，返回 (config, state_manager, version_dir)。"""
    from config import load_config, validate_config
    config = load_config(project_root)
    validate_config(config)
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir or not (version_dir / '.state.json').exists():
        raise RuntimeError('当前还没有启动版本。请先执行 dtflow start --idea "你的需求"')
    state = StateManager(version_dir)
    return config, state, version_dir


def _do_analyze(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行 analyze 并更新状态。"""
    from analyze import run_analyze
    from human_summary import render_analyze_summary

    print('\n📋 正在分析需求...')
    print_llm_risk(estimate_llm_risk(project_root, config, 'analyze'))

    @retry_with_backoff
    def _call():
        return run_analyze(project_root, config)
    result = _call()

    tasks = result.get('tasks', []) or []
    print(f'\n✅ 分析完成！共发现 {len(tasks)} 个任务：')
    for task in tasks[:10]:
        print(f'   - [{task["id"]}] {task["name"]} ({task.get("priority", "")})')

    summary = render_analyze_summary(result)
    print(f'\n💡 {summary}')
    print('\n👉 下一步：运行 dtflow start --confirm 确认方案，或 dtflow start --feedback "修改意见" 提出调整')

    return result


def _do_write_dry_run(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行 write --dry-run 预览。"""
    from write_flow import run_write
    from human_summary import render_write_summary

    print('\n👀 正在预览即将生成的代码...')
    print_llm_risk(estimate_llm_risk(project_root, config, 'write'))
    result = run_write(project_root, config, dry_run=True)

    files = result.get('files', []) or []
    count = result.get('count', 0)
    print(f'\n📋 预览完成，将处理 {count} 个文件：')
    for item in files[:20]:
        print(f'   - {item.get("action", "")}: {item.get("path", "")}')

    summary = render_write_summary(result)
    print(f'\n💡 {summary}')
    print('\n👉 确认没问题？运行 dtflow start --confirm-write 正式生成代码')

    return result


def _do_write(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行正式 write。"""
    from write_flow import run_write
    from human_summary import render_write_summary

    state.checkpoint('pre_write')
    print('\n🔨 正在生成代码...')
    print_llm_risk(estimate_llm_risk(project_root, config, 'write'))

    @retry_with_backoff
    def _call():
        return run_write(project_root, config, dry_run=False)
    result = _call()

    count = result.get('count', 0)
    files = result.get('files', []) or []
    print(f'\n✅ 代码已生成，共 {count} 个文件：')
    for item in files[:20]:
        print(f'   - {item.get("action", "")}: {item.get("path", "")}')

    return result


def _do_review(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行 review。"""
    from review_flow import run_review
    from human_summary import render_review_summary

    print('\n🔍 正在审查代码...')
    print_llm_risk(estimate_llm_risk(project_root, config, 'review'))

    @retry_with_backoff
    def _call():
        return run_review(project_root, config)
    result = _call()

    passed = result.get('passed', False)
    score = result.get('score')
    score_display = f'{score}' if score is not None else '未解析'
    if passed:
        print(f'\n✅ 审查通过！评分：{score_display}')
    else:
        issues = result.get('issues', [])
        print(f'\n⚠️ 审查发现问题，评分：{score_display}')
        for issue in issues[:5]:
            sev = issue.get('severity', '')
            msg = issue.get('message', '')
            path = issue.get('path', '')
            print(f'   - [{sev}] {path}: {msg}')

    summary = render_review_summary(result)
    print(f'\n💡 {summary}')

    return result


def _do_fix(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行 fix。"""
    from fix_flow import run_fix
    from human_summary import render_fix_summary

    print('\n🔧 正在修复问题...')
    print_llm_risk(estimate_llm_risk(project_root, config, 'fix'))

    @retry_with_backoff
    def _call():
        return run_fix(project_root, config)
    result = _call()

    count = result.get('count', 0)
    print(f'\n✅ 修复完成，更新了 {count} 个文件')
    summary = result.get('summary', '')
    if summary:
        print(f'   修复说明：{summary}')

    summary = render_fix_summary(result)
    print(f'\n💡 {summary}')

    return result


def _do_deploy(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行 deploy。"""
    from release_flow import run_deploy

    state.checkpoint('pre_deploy')
    print('\n🚀 正在部署...')
    state.data['status'] = 'deploying'
    state.data['last_action'] = 'deploy'
    state.data['last_error'] = None
    state.save()

    result = run_deploy(project_root, config)
    print(f'\n✅ 部署完成！版本：{result.get("version", "-")}')
    return result


def _do_comprehensive_review(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行上线前综合审查。"""
    from review_flow import run_comprehensive_review
    from human_summary import render_review_summary

    print('\n🔍 正在执行上线前综合审查（7 维度）...')
    print_llm_risk(estimate_llm_risk(project_root, config, 'review'))
    result = run_comprehensive_review(project_root, config)

    passed = result.get('passed', False)
    score = result.get('score')
    score_display = f'{score}' if score is not None else '未解析'
    issues = result.get('issues', [])

    if passed:
        print(f'\n✅ 综合审查通过！评分：{score_display}/10')
        state.data['status'] = 'ready_to_deploy'
    else:
        print(f'\n⚠️ 综合审查未通过，评分：{score_display}/10')
        critical = [i for i in issues if i.get('severity') == 'Critical']
        important = [i for i in issues if i.get('severity') == 'Important']
        if critical:
            print(f'   Critical: {len(critical)} 个')
            for issue in critical[:5]:
                print(f'   - [{issue.get("category", "")}] {issue.get("path", "")}: {issue.get("message", "")}')
        if important:
            print(f'   Important: {len(important)} 个')
            for issue in important[:3]:
                print(f'   - [{issue.get("category", "")}] {issue.get("path", "")}: {issue.get("message", "")}')
        state.data['status'] = 'needs_final_fix'

    state.data['last_action'] = 'comprehensive_review'
    state.save()

    summary = result.get('summary', '')
    if summary:
        print(f'\n💡 审查报告：{result["review_file"]}')

    return result


def _do_seal(project_root: Path, config: dict, state: StateManager) -> dict:
    """执行 seal。"""
    from release_flow import run_seal

    state.checkpoint('pre_seal')
    print('\n📦 正在封版归档...')
    result = run_seal(project_root, config)

    state.data['status'] = 'sealed'
    state.data['last_action'] = 'seal'
    state.data['last_error'] = None
    state.save()

    version = result.get('version', '-')
    print(f'\n🎉 版本 {version} 已封版归档！')
    print('   如需继续开发，运行 dtflow start 开启新版本。')
    return result


def auto_advance(
    project_root: Path,
    action: str = 'continue',
    feedback: str | None = None,
    confirm_write: bool = False,
) -> dict[str, Any]:
    """
    根据当前状态自动推进流程。

    action:
      - 'continue': 从当前状态自动执行下一步
      - 'confirm': 确认 analyze 方案，进入 write dry-run
      - 'confirm-write': 确认 dry-run 结果，正式 write
      - 'revise': 带 feedback 重新 analyze

    返回最终执行结果。
    """
    config, state, version_dir = _get_config_and_state(project_root)
    status = state.data.get('status', 'unknown')

    # 处理显式动作
    if action == 'confirm':
        if status != 'pending_confirm':
            raise RuntimeError(f'当前状态是「{status}」，不是待确认状态，无法 confirm。')
        state.data['architecture_confirmed'] = True
        state.data['status'] = 'confirmed'
        state.data['last_action'] = 'confirm'
        state.data['fix_review_count'] = 0  # 重置 fix→review 计数
        tasks = state.data.get('tasks', [])
        state.data['current_task'] = tasks[0]['id'] if tasks else None
        state.save()
        print('✅ 方案已确认！')
        # 自动进入 write dry-run
        return _do_write_dry_run(project_root, config, state)

    if action == 'confirm-write':
        if status not in ('confirmed', 'written'):
            raise RuntimeError(f'当前状态是「{status}」，无法确认生成。')
        result = _do_write(project_root, config, state)
        # 自动进入 review
        review_result = _do_review(project_root, config, state)
        if review_result.get('passed'):
            state.data['status'] = 'review_passed'
            state.data['last_action'] = 'review'
            state.save()
            # 检查是否还有下一个 task
            tasks = state.data.get('tasks', [])
            current = state.data.get('current_task')
            remaining = [t for t in tasks if t.get('id') != current and t.get('status') != 'done']
            if remaining:
                next_task = remaining[0]
                print(f'\n👉 下一个任务：[{next_task["id"]}] {next_task["name"]}')
                print('   运行 dtflow start 继续处理，或 dtflow start --deploy 直接部署。')
            else:
                print('\n👉 所有任务已完成！可以本地预览看看效果：')
                print('   dtflow start --run  启动本地预览')
                print('   dtflow start --deploy  直接部署上线')
        else:
            state.data['status'] = 'needs_fix'
            state.data['last_action'] = 'review'
            state.save()
            print('\n👉 审查发现问题，运行 dtflow start 自动修复并重新审查。')
        return result

    if action == 'revise':
        if not feedback:
            raise RuntimeError('请通过 --feedback 提供修改意见。')
        state.data['revision_feedback'] = feedback
        state.data['last_action'] = 'revise'
        state.save()
        print('✅ 已记录你的反馈，正在重新分析...')
        return _do_analyze(project_root, config, state)

    if action == 'run':
        from run_flow import run_flow
        result = run_flow(project_root, config)
        url = result.get('url', '')
        status = result.get('status', '')
        if status == 'already_running':
            print(f'\n✅ 服务已在运行：{url}')
        elif status == 'running':
            print(f'\n🌐 预览地址：{url}')
        else:
            print(f'\n⏳ 服务正在启动：{url}')
            print(f'   {result.get("message", "")}')
        print('   确认没问题后运行 dtflow start --deploy 部署上线。')
        return result

    if action == 'deploy':
        result = _do_deploy(project_root, config, state)
        seal_result = _do_seal(project_root, config, state)
        return seal_result

    if action == 'final_review':
        return _do_comprehensive_review(project_root, config, state)

    if action == 'deploy-skip-review':
        print('\n⏭️ 跳过综合审查，直接部署...')
        result = _do_deploy(project_root, config, state)
        seal_result = _do_seal(project_root, config, state)
        return seal_result

    # action == 'continue': 按状态自动推进
    if status == 'created':
        return _do_analyze(project_root, config, state)

    if status == 'pending_confirm':
        print('\n📋 需求分析已完成，等待你确认方案。')
        tasks = state.data.get('tasks', [])
        print(f'   共发现 {len(tasks)} 个任务：')
        for task in tasks[:10]:
            print(f'   - [{task["id"]}] {task["name"]} ({task.get("priority", "")})')
        print('\n👉 运行 dtflow start --confirm 确认方案，或 dtflow start --feedback "修改意见" 提出调整')
        return {'status': 'pending_confirm', 'action': 'wait_confirm'}

    if status == 'confirmed':
        return _do_write_dry_run(project_root, config, state)

    if status in ('writing', 'written'):
        return _do_review(project_root, config, state)

    if status in ('needs_fix', 'failed'):
        # 自动 fix → review，最多 3 轮
        fix_review_count = state.data.get('fix_review_count', 0)
        max_fix_review = 3
        if fix_review_count >= max_fix_review:
            state.data['status'] = 'fix_exhausted'
            state.save()
            print(f'\n❌ fix→review 已重试 {fix_review_count} 轮（上限 {max_fix_review} 轮），仍无法通过审查。')
            print('   请手动检查代码并修复问题后，运行 dtflow advanced recover 重置状态。')
            return {'status': 'fix_exhausted', 'action': 'manual_intervention', 'retry_count': fix_review_count}

        state.data['fix_review_count'] = fix_review_count + 1
        state.save()
        print(f'\n🔄 fix→review 第 {fix_review_count + 1}/{max_fix_review} 轮...')

        fix_result = _do_fix(project_root, config, state)
        review_result = _do_review(project_root, config, state)
        if review_result.get('passed'):
            state.data['fix_review_count'] = 0  # 通过后重置计数
            state.data['status'] = 'review_passed'
            state.data['last_action'] = 'review'
            state.save()
            # 检查是否还有下一个 task
            tasks = state.data.get('tasks', [])
            current = state.data.get('current_task')
            remaining = [t for t in tasks if t.get('id') != current and t.get('status') != 'done']
            if remaining:
                next_task = remaining[0]
                print(f'\n👉 下一个任务：[{next_task["id"]}] {next_task["name"]}')
                print('   运行 dtflow start 继续处理。')
            else:
                print('\n👉 所有任务已通过审查！进入综合审查阶段...')
                state.data['status'] = 'pending_final_review'
                state.save()
                print('   ⚠️  建议先 compact 一次，减少上下文累积。')
                print('   然后运行 dtflow start --final-review 执行综合审查')
                print('   或 dtflow start --deploy-skip-review 跳过审查直接部署')
        else:
            state.data['status'] = 'needs_fix'
            state.data['last_action'] = 'review'
            state.save()
            remaining_tries = max_fix_review - fix_review_count - 1
            if remaining_tries > 0:
                print(f'\n👉 仍有问题，剩余 {remaining_tries} 轮修复机会，运行 dtflow start 继续修复。')
            else:
                print(f'\n👉 本轮修复后仍有问题，下一轮将放弃自动修复，请手动介入。')
        return review_result

    if status == 'review_passed':
        tasks = state.data.get('tasks', [])
        current = state.data.get('current_task')
        remaining = [t for t in tasks if t.get('id') != current and t.get('status') != 'done']
        if remaining:
            next_task = remaining[0]
            state.data['current_task'] = next_task['id']
            state.data['status'] = 'confirmed'
            state.save()
            print(f'\n📋 进入下一个任务：[{next_task["id"]}] {next_task["name"]}')
            return _do_write_dry_run(project_root, config, state)
        else:
            # 所有任务完成，进入综合审查阶段
            state.data['status'] = 'pending_final_review'
            state.data['last_action'] = 'all_tasks_reviewed'
            state.save()
            print('\n🎉 所有任务都已通过审查！')
            print('   ⚠️  建议先 compact 一次，减少上下文累积后再执行综合审查。')
            print('   进入上线前综合审查阶段：')
            print('   dtflow start --final-review    执行综合审查（推荐）')
            print('   dtflow start --deploy-skip-review  跳过审查直接部署')
            return {'status': 'pending_final_review', 'action': 'wait_final_review'}

    if status == 'pending_final_review':
        print('\n⚠️  建议先 compact 一次，减少上下文累积导致的幻觉。')
        print('   然后再执行综合审查。')
        print('\n🔍 正在执行综合审查...')
        return _do_comprehensive_review(project_root, config, state)

    if status == 'ready_to_deploy':
        print('\n✅ 综合审查已通过，可以部署了！')
        print('   运行 dtflow start --deploy 部署上线')
        return {'status': 'ready_to_deploy', 'action': 'wait_deploy'}

    if status == 'needs_final_fix':
        print('\n🔧 综合审查发现问题，正在自动修复...')
        fix_result = _do_fix(project_root, config, state)
        print('\n🔍 修复完成，重新执行综合审查...')
        review_result = _do_comprehensive_review(project_root, config, state)
        if review_result.get('passed'):
            print('\n👉 修复后综合审查通过！运行 dtflow start --deploy 部署。')
        else:
            print('\n👉 仍有问题，运行 dtflow start 再次修复。')
        return review_result

    if status == 'sealed':
        print('\n📦 当前版本已封版。')
        print('   运行 dtflow start --idea "新的需求" 开始新版本。')
        return {'status': 'sealed', 'action': 'version_sealed'}

    print(f'\n⚠️ 未知状态：{status}，请检查 dtflow advanced status。')
    return {'status': status, 'action': 'unknown'}
