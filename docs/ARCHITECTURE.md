# DevTaskFlow Architecture

## 产品边界（当前）

- Codex skills：用于分发和触发 DevTaskFlow skill 本身
- GitHub：用于被 DevTaskFlow 管理项目的封版发布
- dashboard：仅作为项目总览页，不承担复杂项目管理能力
- analyze：输出架构与实施方案，不做工时估算/排期管理
- deploy adapter：对接现成部署方式，不自建部署平台

## 目标架构

```text
Codex session
  ├── reads $devtaskflow / SKILL.md
  ├── analyzes requirements
  ├── edits code directly
  ├── reviews and fixes implementation
  └── updates DevTaskFlow docs/state

CLI (dtflow)
  ├── project scaffold
  ├── durable state and version docs
  ├── board/status queries
  ├── CODEX_NEXT_ACTION.md handoff notes
  ├── local preview helpers
  └── deploy / archive / release helpers
```

## 当前实现状态

当前已经落地：

- `SKILL.md` 作为 Codex 运行入口和阶段规则
- `.dtflow/config.json` 默认使用 `codex_managed`
- `dtflow start` 在需要智能工作的阶段写入 `CODEX_NEXT_ACTION.md`，由当前 Codex 会话继续执行
- `analyze / write / review / fix` 不再默认调用外部模型
- `write_flow.py` 已增加路径安全校验，防止写出项目目录
- `status` 可查看 `last_action / last_result_format / last_summary / last_error`
- 状态机已包含部分中间态：`analyzing / writing / reviewing / fixing / deploying / sealed`

当前尚未完成：

- 更完整的人工/模型协作状态恢复提示
- 更完整的版本封存、补丁和 erratum 流程
- 看板对 `CODEX_NEXT_ACTION.md` 的可视化展示

## 设计原则

### 1. Codex-first
- Codex 会话负责推理、代码编辑、审查和修复
- DevTaskFlow 只记录项目状态、文档、版本和发布纪律
- 不要求用户配置模型凭据、外部模型地址或本机凭据

### 2. 安全优先
- 不读取 Codex 账号、session 文件、隐藏凭据或 keychain
- 文件写入必须限制在 project_root 内
- 发布、封版、commit、tag、push 前必须得到用户明确授权

### 3. 项目先于版本
- 每次开发任务必须先绑定到一个 project
- project 需要进入当前工作区的项目索引（PROJECTS.md）
- 然后才能启动具体版本迭代

### 4. 项目自描述
- 每个项目通过 `.dtflow/config.json` 描述自身
- 每个版本通过 `versions/<version>/.state.json` 维护状态

### 5. 可诊断
- doctor 统一检查环境、依赖、配置、目录结构
- status 输出最近动作、错误、结果格式与摘要

## 下一步演进

### v0.2
- deploy / seal / publish 进一步 adapter 化
- renderer 层独立
- 更强的 async / resume 能力
