# DevTaskFlow Architecture

## 产品边界（当前）

- Codex skills：用于分发和触发 DevTaskFlow skill 本身
- GitHub：用于被 DevTaskFlow 管理项目的封版发布
- dashboard：仅作为项目总览页，不承担复杂项目管理能力
- analyze：输出架构与实施方案，不做工时估算/排期管理
- deploy adapter：对接现成部署方式，不自建部署平台

## 目标架构

```text
CLI (dtflow)
  ├── config layer
  ├── project-board layer
  ├── state layer
  ├── scaffold layer
  ├── doctor layer
  ├── pipeline core
  │    ├── analyze
  │    ├── write
  │    ├── review
  │    ├── fix
  │    ├── deploy
  │    └── seal
  ├── orchestrator
  │    ├── local_llm
  │    └── codex_subagent
  └── adapters
       ├── llm adapter
       ├── deploy adapter
       ├── archive adapter
       └── codex adapter
```

## 当前实现状态（v0.1）

当前已经落地：

- `orchestrator.py` 作为统一编排入口
- `orchestrators/local_llm.py` 承接 `analyze / write / review / fix`
- `orchestrators/codex_subagent.py` 作为 Codex 子任务统一接口适配器
- `analyze.py / write_flow.py / review_flow.py / fix_flow.py` 已切换为通过 orchestrator 调度
- prompts 已外置到 `prompts/`
- 新增 `codex_bridge.py`，负责构造 Codex 子任务请求描述
- 新增 `result_schema.py / result_parser.py`，提供 JSON-first 协议基础层
- `write_flow.py` 已增加路径安全校验，防止写出项目目录
- `status` 可查看 `last_action / last_result_format / last_summary / last_error`
- `write --dry-run` 已支持预览文件写入计划
- 状态机已包含部分中间态：`analyzing / writing / reviewing / fixing / deploying / sealed`

当前尚未完成：

- Codex 子任务真实调度接线
- 结果渲染层与协议层进一步分离
- FILE block / Markdown fallback 继续退场
- 更完整的 failed / resume / async 恢复体系

## 设计原则

### 1. Core / Adapter / Orchestrator 分离
- 核心流程不直接绑定 Codex 运行时内部 API
- Codex 子任务协作作为可选 orchestrator / adapter 存在
- 本地 LLM 模式与 Codex 子任务模式可切换

### 2. 安全优先
- API Key 禁止硬编码
- 所有敏感信息走环境变量或本地配置
- 文件写入必须限制在 project_root 内

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
- Codex 子任务真实调度
- deploy / seal / publish 进一步 adapter 化
- renderer 层独立
- 更强的 async / resume 能力
