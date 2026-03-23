# Changelog

## v0.7.0 (2026-03-23)

**Feature: React Best Practices + Web UI Quality Guidelines**

- 集成 Vercel React 最佳实践（64 条规则）到 write_system.md — 代码生成时自动遵循：并行请求、动态导入、大列表虚拟化、避免 transition:all、hydration 安全、交互状态、文案规范
- 集成 Vercel Web Interface Guidelines 到 review_system.md — review 时自动检查 6 项 React 性能 + 10 项 UI 质量（无障碍、焦点状态、表单、动画、排版、内容处理、深色模式等）
- comprehensive_review_system.md 从 7 维度扩展到 9 维度：新增 React 性能审查和 Web UI 质量审查
- 文案规范：主动语态、Title Case、数字代替文字、按钮标签具体化、错误消息含修复步骤

## v0.6.0 (2026-03-21)

**Feature: Design System + User Guide + Comprehensive Review**

- Analyze 阶段新增设计系统规范输出（色彩/字体/间距/组件/交互/响应式）
- analyze 完成后自动生成 DESIGN_SYSTEM.md
- Write 阶段自动生成 docs/USER_GUIDE.md（面向最终用户的使用说明书）
- Write 阶段 UI 代码强制遵循 DESIGN_SYSTEM.md 规范
- 新增上线前综合审查阶段（7 维度：代码质量/安全性/交互友好度/需求符合度/设计一致性/字段依赖/命名规范）
- 新增 pending_final_review / ready_to_deploy / needs_final_fix 状态
- 新增 --final-review 和 --deploy-skip-review 命令
- 综合审查评分 <7 分自动触发修复循环

**Compliance: Data Exposure Prevention**

- `cli.py`: 部署信息脱敏显示（IP 保留首尾段，域名模糊化），不再直接打印 user/path
- `cli.py`: 新增 `_mask_host()` 脱敏函数
- `SKILL.md`: 主动调用策略改为"识别意图 → 建议用户 → 等待确认后执行"，不再无条件自动触发

## v0.5.1 (2026-03-19)

**Security Fix: Shell Injection Prevention**
- `deploy_adapter.py`: Replace `shell=True` with `shlex.split()` for safe argument parsing
- `run_flow.py`: Use argument lists for npm/pip/python commands, remove `shell=True`
- Eliminates all `shell=True` usage across the codebase

## v0.5.0 (2026-03-19)

**Security Fix: ClawHub Review Response**
- `board/server.js`: Sanitize API responses — remove deploy host/user/path exposure
- `board/server.js`: Filter sensitive fields from `.state.json` (publish details, error internals)
- `landing/serve.py`: Remove hardcoded absolute path `/home/admin/.openclaw/...`, use relative paths
- `SKILL.md`: Declare optional deploy/publish env vars (`DTFLOW_GITHUB_TOKEN`, `DTFLOW_DEPLOY_SSH_KEY`, `DTFLOW_DOCKER_REGISTRY`)
- `SKILL.md`: Add board security notes (local-only, API already sanitized)

## v0.4.9 and earlier

- Initial ClawHub releases
- Core pipeline: analyze → write → review → fix → deploy → seal
- Board dashboard (Node.js + Express)
- Deploy adapters: shell, ssh_shell, docker
- Publish adapters: GitHub releases
- OpenClaw subagent orchestration
- Auto-advance mode for unattended runs
