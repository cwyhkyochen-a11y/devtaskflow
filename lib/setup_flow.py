"""Codex-first setup flow.

DevTaskFlow for Codex does not configure a separate model endpoint. Codex is
the agent runtime; this CLI only checks project structure and local tooling.
"""
from __future__ import annotations

from pathlib import Path


def _run_doctor_check(project_root: Path | None = None) -> None:
    print()
    print("Checking local DevTaskFlow support...")
    try:
        from doctor import run_doctor
        checks = run_doctor(project_root)
        for name, passed, detail in checks:
            mark = "ok" if passed else "missing"
            print(f"  {mark}: {name} - {detail}")
    except Exception as e:
        print(f"doctor check failed: {e}")


def run_setup(project_root: Path | None = None, mode: str | None = None) -> int:
    """Report Codex-mode readiness without asking for API keys."""
    if mode in {"guided", "advanced"}:
        print("DevTaskFlow Codex版不再配置独立模型。")
        print("请直接在 Codex 中使用 $devtaskflow；CLI 只负责项目状态、文档、看板、预览和发布辅助。")
    else:
        print("DevTaskFlow Codex mode")
        print("=" * 40)
        print("不需要配置模型凭据或外部模型端点。")
        print("当前 Codex 会话负责分析、实现和审查；dtflow 负责项目结构和状态记录。")

    _run_doctor_check(project_root)
    print()
    print('开始项目：在 Codex 中说「用 $devtaskflow ...」，或运行 dtflow start --idea "你的需求" 创建跟踪骨架。')
    return 0
