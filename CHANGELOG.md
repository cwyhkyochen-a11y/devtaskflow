# Changelog

## v1.2.0-codex (2026-06-20)

**Migration: Codex skill edition**

- `SKILL.md` 迁移为 Codex skill frontmatter：`name: devtaskflow` + Codex 触发描述
- 新增 `agents/openai.yaml`，提供 Codex UI 展示元数据
- 新增 Codex 版项目索引文案，`PROJECTS.md` 明确作为 DevTaskFlow 项目索引使用
- 默认改为 `codex_managed`：当前 Codex 会话负责分析、实现、审查和修复
- `dtflow` 只负责项目结构、状态、看板、预览、部署、封版和 `CODEX_NEXT_ACTION.md` 交接提示
- 新项目模板移除独立模型配置，并默认发布到 GitHub Releases
- 移除当前 CLI 的非 Codex 发布入口，Codex 版保留 GitHub 发布能力
- 移除独立模型编排器配置说明
