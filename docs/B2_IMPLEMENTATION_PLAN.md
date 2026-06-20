# DevTaskFlow B2 实施方案

## 目标

将旧版 dev-pipeline 重构为可共享、可分发、可适配的 DevTaskFlow。

## Phase 1 ✅ 基础框架

- [x] 新名称定稿：DevTaskFlow
- [x] 新 skill 目录建立
- [x] CLI 入口建立：dtflow
- [x] .dtflow 配置目录设计
- [x] Codex 版环境变量模板（仅保留项目运行/部署配置）
- [x] doctor 命令
- [x] status 命令
- [x] init-project 脚手架

## Phase 2 ✅ 核心流水线

- [x] Codex-managed 阶段交接机制
- [x] analyze / confirm / revise
- [x] 任务计划解析器（JSON + markdown fallback）
- [x] 状态推进机制完善（auto_advance）

## Phase 3 ✅ 代码生成与审查

- [x] write / review / fix
- [x] 文件写入策略增强（安全路径检查、create/overwrite/append）
- [x] 审查报告解析
- [x] 综合审查（9 维度：代码质量/安全性/交互/需求/设计/字段/命名/React性能/Web UI质量）
- [x] dry-run 预览

## Phase 4 ✅ 部署与发布

- [x] deploy adapters（shell / ssh_shell / docker）
- [x] archive adapter（本地归档）
- [x] GitHub publish adapter（tag + release）
- [x] Codex-managed skill 工作流（v1.2.0 迁移）
- [x] GitHub publish adapter（v0.8.0 新增）

## Phase 5 ✅ 文档与示例

- [x] README 完善
- [x] 示例项目骨架
- [x] Codex skill 安装方式文档
- [x] 迁移指南（dev-pipeline → DevTaskFlow）

## 设计决策

1. 项目配置目录采用 `.dtflow/`
2. 命令名采用 `dtflow`
3. 敏感配置全部走环境变量
4. Codex 协作作为 adapter，而不是核心硬依赖
5. 旧版 dev-pipeline 不直接硬改，采用新目录重建
6. 编排器统一走 OpenAI compatible API，不依赖 Codex 运行时内部 API
7. 部署信息脱敏显示，安全合规
