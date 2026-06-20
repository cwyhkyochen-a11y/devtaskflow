# DevTaskFlow

**不会写代码，也能把想法做成可运行的软件。**

> 用自然语言发起开发任务，Codex + AI 驱动开发流水线：需求 -> 方案 -> 代码 -> 审查 -> 修复 -> 综合审查 -> 本地预览 -> 部署 -> GitHub 发布。

## 它怎么工作

你只需要用大白话说清楚想做什么。在 Codex 里可以这样说：

> 用 `$devtaskflow` 帮我做一个客户管理工具，给销售团队用，需要录入客户、搜索、跟进状态、备注，界面简洁，手机也能用。

DevTaskFlow 会把这件事拆成可追踪的开发流程：

| 步骤 | 做什么 | 你需要做什么 |
| --- | --- | --- |
| 需求分析 | 拆成功能清单、技术方案、设计规范 | 确认或补充 |
| 代码生成 | 由当前 Codex 会话生成和修改项目代码 | 确认实现方向 |
| 代码审查 | 逐任务检查代码质量和需求符合度 | 看摘要 |
| 自动修复 | 发现问题后修复并复审 | 无 |
| 综合审查 | 9 维度上线前检查 | 看报告 |
| 本地运行 | 启动项目预览 | 确认效果 |
| 部署上线 | 执行配置好的部署命令 | 明确授权 |
| 发布归档 | 打 tag 并发布 GitHub Release | 明确授权 |

## 核心能力

- 从自然语言需求生成可运行项目
- 分析、写代码、审查、修复、最终审查一条链路推进
- 支持本地运行、部署、封版、GitHub Release 发布
- 多项目看板，进度可追踪
- 写入前 dry-run 预览，路径写入限制在项目目录内
- 不需要用户额外配置模型凭据或外部模型端点

## 快速开始

### 前置条件

- Codex CLI/Desktop 或支持 Codex skills 的运行环境
- Python 3.10+
- Node.js 18+（仅看板服务需要）

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

### 安装到 Codex skills

把本目录放到 Codex skills 目录中，目录名保持 `devtaskflow`：

```bash
mkdir -p ~/.codex/skills
cp -R /path/to/devtaskflow ~/.codex/skills/devtaskflow
```

如果你是在这个仓库里开发或审查，可以直接在当前目录运行命令。

### 在 Codex 中使用

在 Codex 里通过 `$devtaskflow` 使用时，直接发起任务即可。Codex 负责当前对话里的分析、实现、审查和工具执行，DevTaskFlow 负责项目结构、阶段状态、检查点、看板、预览和发布纪律。

DevTaskFlow 不读取 Codex 账号、会话文件、隐藏凭据或本机 keychain，也不会要求用户配置另一套模型 API。

### 发起新项目

在 Codex 中说：

> 用 `$devtaskflow` 新建一个项目，叫 crm-lite，我想做一个给销售团队用的客户管理工具。

也可以直接运行：

```bash
dtflow start --new-project --name crm-lite --idea "给销售团队用的客户管理工具，需要录入客户、搜索、跟进状态、备注，界面简洁，手机也能用"
```

## 常用命令

```bash
dtflow setup
dtflow start --new-project --name NAME --idea "需求"
dtflow start
dtflow start --confirm
dtflow start --confirm-write
dtflow start --feedback "修改意见"
dtflow start --run
dtflow start --final-review
dtflow start --deploy
dtflow board
dtflow board --serve
dtflow board-query --name PROJECT
dtflow advanced publish --target github
```

## 工作流

```text
提需求 -> 分析（含设计规范）-> 确认 -> 生成代码 -> 逐任务审查 -> 修复循环 -> 综合审查 -> 本地预览 -> 部署 -> 封版 -> GitHub 发布
```

每一步都有状态，每一步都能继续、恢复和查看。

## 架构

```text
  Codex / 自然语言交互层
            |
  +---------+---------+
  |   pipeline core   |  analyze -> write -> review -> fix -> final_review -> deploy -> seal
  |   codex-managed   |  当前 Codex 会话负责分析 / 写码 / 审查
  |   state + board   |  项目状态与看板
  |   adapters        |  本地预览、部署、归档、GitHub Release
  +-------------------+
```

## 安全与约束

- 写入路径限制在项目目录内
- 部署、发布等项目运行配置走环境变量或项目 `.env`
- 部署信息脱敏显示
- 主动部署和发布前必须确认
- 写入前可预览
- 审查与修复分阶段执行
- 项目与版本分层管理

## 版本

当前版本：**v1.2.0-codex** — Codex skill migration.

## License

MIT-0 — 免费使用、修改、分发，无需署名。
