from __future__ import annotations

from pathlib import Path

from project import get_current_version_dir


CODEX_MODE = "codex_managed"


def is_codex_managed(config: dict) -> bool:
    mode = config.get("adapters", {}).get("orchestration", CODEX_MODE)
    return mode in {"", None, CODEX_MODE, "codex", "codex_skill"}


def _current_docs_dir(project_root: Path, config: dict) -> Path:
    version_dir = get_current_version_dir(project_root, config)
    if not version_dir:
        raise RuntimeError('当前还没有启动版本。请先执行 dtflow start --idea "你的需求"')
    docs_dir = version_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


def _stage_instruction(action: str, feedback: str | None = None) -> str:
    feedback_line = f"\n用户反馈：{feedback}\n" if feedback else ""
    instructions = {
        "analyze": "读取 REQUIREMENTS.md 和项目现状，生成 DEV_PLAN.md、任务列表、必要的 DESIGN_SYSTEM.md，并把状态推进到 pending_confirm。",
        "revise": "根据用户反馈修订 REQUIREMENTS.md / DEV_PLAN.md / 任务列表，然后保持或回到 pending_confirm 等用户确认。",
        "write": "读取 DEV_PLAN.md 和 current_task，直接在当前 Codex 会话中实现该任务；完成后更新状态为 written。",
        "review": "审查当前任务实现，写入 REVIEW_TASK_<task>.md；通过则更新为 review_passed，不通过则更新为 needs_fix。",
        "fix": "根据 REVIEW_TASK_<task>.md 修复问题，完成后更新为 written 并重新审查。",
        "final_review": "做上线前综合审查，写入 COMPREHENSIVE_REVIEW.md；通过则更新为 ready_to_deploy，不通过则更新为 needs_final_fix。",
        "status": "读取状态、任务和文档，向用户说明当前阶段、下一步和缺口。",
    }
    return instructions.get(action, instructions["status"]) + feedback_line


def emit_codex_next_action(
    project_root: Path,
    config: dict,
    state_data: dict,
    action: str,
    feedback: str | None = None,
) -> dict:
    """Write a handoff note for the current Codex session instead of calling a model API."""
    docs_dir = _current_docs_dir(project_root, config)
    note_path = docs_dir / "CODEX_NEXT_ACTION.md"
    status = state_data.get("status", "unknown")
    current_task = state_data.get("current_task") or "-"
    tasks = state_data.get("tasks", [])
    task_lines = "\n".join(
        f"- [{task.get('id', '-')}] {task.get('name', '-')}: {task.get('status', 'todo')}"
        for task in tasks[:20]
    ) or "- 暂无任务列表"

    note = f"""# Codex Next Action

DevTaskFlow Codex版不调用外部模型，也不需要模型凭据。当前 Codex 会话应该直接执行下一步。

## Current Stage

- Status: `{status}`
- Current task: `{current_task}`

## Next Action

{_stage_instruction(action, feedback)}

## Task Snapshot

{task_lines}

## Required Checks

- 读取 `AGENTS.md` 和当前版本需求/计划。
- 补齐目标用户、核心流程、non-goals、验收标准和风险。
- 不读取 Codex 账号、session 文件、隐藏凭据或本机 keychain。
- 发布、封版、commit、tag、push 前必须得到用户明确授权。
"""
    note_path.write_text(note.rstrip() + "\n", encoding="utf-8")

    print("\nCodex-managed mode")
    print("DevTaskFlow 不会调用外部模型，也不需要单独模型配置。")
    print(f"下一步已写入：{note_path}")
    print(f"请让当前 Codex 会话执行：{_stage_instruction(action, feedback)}")

    return {
        "status": status,
        "action": f"codex_{action}",
        "codex_managed": True,
        "next_action_file": str(note_path),
    }
