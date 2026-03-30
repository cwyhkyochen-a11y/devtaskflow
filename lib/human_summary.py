from __future__ import annotations

from typing import List, Dict, Any

from ux import build_next_step_hint


def render_analyze_summary(result: dict) -> str:
    tasks = result.get('tasks', []) or []
    if not tasks:
        return '分析已完成，但还没提取到具体任务。你可以补充更多需求细节后重新分析。'

    top_tasks = tasks[:3]
    names = '；'.join([t.get('name', '未命名任务') for t in top_tasks])
    remaining = len(tasks) - 3
    extra = f'，还有 {remaining} 个任务' if remaining > 0 else ''
    return f'建议先做这几个：{names}{extra}。确认没问题就继续吧。'


def render_review_summary(result: dict) -> str:
    passed = result.get('passed')
    task_name = result.get('task_name', '当前任务')
    if passed:
        return f'{task_name} 审查通过，可以继续了。'
    issues = result.get('issues', [])
    count = len(issues)
    return f'{task_name} 发现 {count} 个问题，已自动进入修复流程。'


def render_write_summary(result: dict) -> str:
    files = result.get('files', []) or []
    dry_run = result.get('dry_run', False)
    count = result.get('count', 0)
    preview = '、'.join([f.get('path', '') for f in files[:3]]) if files else '暂无文件'
    if dry_run:
        return f'预览：将处理 {count} 个文件（{preview} 等）。确认后正式生成。'
    return f'已生成 {count} 个文件（{preview} 等）。接下来会自动审查。'


def render_fix_summary(result: dict) -> str:
    files = result.get('files', []) or []
    count = result.get('count', 0)
    preview = '、'.join([f.get('path', '') for f in files[:3]]) if files else '暂无文件'
    summary = result.get('summary', '')
    parts = [f'已修复 {count} 个文件（{preview} 等）。']
    if summary:
        parts.append(f'修复说明：{summary}')
    parts.append('接下来会自动重新审查。')
    return '\n'.join(parts)


def render_next_step(state: Dict[str, Any]) -> str:
    """委托给 ux.build_next_step_hint，避免维护两份映射。"""
    return build_next_step_hint(state)
