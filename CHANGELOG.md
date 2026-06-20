# Changelog

## v1.2.0-codex (2026-06-20)

**Migration: Codex skill edition**

- `SKILL.md` 迁移为 Codex skill frontmatter：`name: devtaskflow` + Codex 触发描述
- 新增 `agents/openai.yaml`，提供 Codex UI 展示元数据
- 新增 Codex 版项目索引文案，`PROJECTS.md` 明确作为 DevTaskFlow 项目索引使用
- `lib/codex_config.py` 使用显式环境变量和项目 `.env` 探测 LLM 配置
- `lib/orchestrators/codex_subagent.py` 提供 Codex 版 OpenAI-compatible 编排器
- 新项目模板改用 `codex` 配置段，并默认发布到 GitHub Releases
- 移除当前 CLI 的非 Codex 发布入口，Codex 版保留 GitHub 发布能力
- 移除历史平台预设，只保留通用 OpenAI-compatible 配置说明
