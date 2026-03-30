# Changelog

## v1.1.0 (2026-03-30) 🔒

**修复: 全面代码审查 — 安全加固 + Bug 修复 + 架构改进**

- **Critical Bug 修复（3 项）**
  - `scaffold.py`: 补充缺失的 `from git_utils import ensure_git_repo` import，修复运行时 NameError
  - `write_flow.py`: 补充缺失的 `from git_utils import auto_commit` import，修复 write 完成后崩溃
  - `fix_flow.py`: 补充缺失的 `from git_utils import auto_commit` import，扩展状态检查支持 `failed` 状态
- **安全加固（6 项）**
  - `serve.py`: HTTPServer 默认绑定 `127.0.0.1`，新增 host 参数可配置，防止公网暴露
  - `board/server.js`: Express 默认绑定 `127.0.0.1`，支持 `DTFLOW_BOARD_HOST` 环境变量覆盖
  - `llm.py`: 新增 `__repr__` 方法对 API Key 脱敏显示；`chat()` 添加 choices 防御性检查
  - `prompt_loader.py`: `load_prompt()` 添加路径遍历防护，防止读取任意文件
  - `setup_flow.py`: `.env` 文件写入后执行 `chmod 0600`，防止多用户系统泄露 API Key
  - `deploy_adapter.py`: SSH 参数正则校验（host/user/path），拒绝 shell 元字符注入
- **架构改进（7 项）**
  - `board/server.js`: 数据源改为优先读取 PROJECTS.md JSON 注释，解决 Python/Node 数据不一致
  - `auto_advance.py`: fix→review 循环添加最大 3 轮限制，超限后提示手动介入
  - `review_flow.py`: 评分解析不再伪造默认分数，无法解析时返回 None
  - `state.py`: save() 改为原子写入（先写 tmp 再 os.replace），防止进程崩溃导致状态文件损坏
  - `orchestrator.py`: 顶层 import 改为 lazy import，支持降级
  - `run_flow.py`: 启动命令改用 `shlex.split()`，修复文件描述符泄漏
  - `deploy_adapter.py`: `run_shell/run_proc` 新增 timeout 参数（默认 300 秒）
- **代码质量改进（7 项）**
  - `cli.py`: 修复 `cmd_adv_recover` 缺少 f 前缀的 bug，删除 `cmd_start` 重复代码块
  - `dashboard.py`: bare except 改为保留异常信息
  - `error_handling.py`: 静默吞异常改为打印警告
  - `human_summary.py`: 委托 `ux.py` 消除重复代码
  - `result_schema.py`: `validate_analyze_result` 添加 deepcopy 防止副作用
  - `requirement_guidance.py`: 答案匹配添加 strip 容错
  - `project.py`: 版本目录排序改为优先按语义版本号

## v1.0.0 (2026-03-28) 🎉

**里程碑: DevTaskFlow 1.0 正式版 — 架构回归 OpenClaw 原生能力**

- **架构重构: 彻底移除冗余 LLM 配置**
  - 新建 `lib/openclaw_config.py` — 自动从 `~/.openclaw/openclaw.json` + `credentials/` 读取 model / base_url / api_key
  - `lib/llm.py` — env var 读不到时自动 fallback 到 OpenClaw 配置
  - `lib/orchestrators/openclaw_subagent.py` — 同上
  - 用户零配置：运行在 OpenClaw 环境内自动获取 LLM 设置
- **安全清理: 消除 ClawHub 安全扫描 Note**
  - SKILL.md metadata 删除全部 9 个 env var 声明（`requires: {}`）
  - 3 个未使用的 credential 声明（DTFLOW_DEPLOY_SSH_KEY / DTFLOW_GITHUB_TOKEN / DTFLOW_DOCKER_REGISTRY）→ 删除
  - 6 个冗余 LLM 配置变量 → 删除（OpenClaw 原生管理模型，skill 无需重复配置）
- **配置简化**
  - `lib/doctor.py` — 诊断项从检查 env var 改为 OpenClaw 自动检测
  - `lib/setup_flow.py` — auto 模式优先用 OpenClaw 配置，零输入
  - `templates/config.json` — 精简配置模板，移除 llm 段

## v0.10.0 (2026-03-27)

**Feature: Git 自动化 — 每次新建/迭代项目自动使用 Git**

- **`lib/git_utils.py`** — 新增 git 工具模块
  - `check_git_installed()` — 检测 git 是否已安装，未安装时提示安装命令
  - `is_git_repo()` — 检测目录是否已是 git 仓库
  - `ensure_git_repo()` — 自动 `git init` + `git branch -M main` + 首次 commit
  - `auto_commit(message)` — 自动 `git add .` + `git commit`（有变更才提交，无变更跳过）
- **项目初始化自动 git** — `scaffold.py` 创建目录结构后自动 `ensure_git_repo`
- **Write 阶段自动 commit** — `write_flow.py` 代码生成完成后自动提交
- **Fix 阶段自动 commit** — `fix_flow.py` 修复完成后自动提交
- **Seal 前自动确保 git 仓库** — `release_flow.py` 封版前检查/初始化 git
- **Doctor 新增 git 检查** — `doctor.py` 诊断时检测 git 是否可用
- **所有 git 操作 best-effort** — 失败只打印 ⚠️ 警告，不阻塞主流程

## v0.9.0 (2026-03-25)

**Feature: 错误恢复 + 配置简化 + 封版自动化**

- **错误恢复机制** — 三层保障
  - `retry_with_backoff` 装饰器：指数退避自动重试（默认 3 次），集成到所有 LLM 调用
  - 检查点机制：StateManager 新增 `checkpoint` / `list_checkpoints` / `restore_checkpoint`，关键操作前自动快照
  - `dtflow advanced rollback --list/--to` — 回滚到任意检查点
  - `dtflow advanced recover` — 自动检测 6 类状态异常并修复（方案缺失、src 为空、无部署记录、failed 无详情、状态异常、检查点信息）
  - 友好错误提示从 5 种扩展到 14 种，每种含操作建议，通用兜底提示运行 recover
- **配置简化（setup 三档模式）**
  - 极简模式（auto）：自动检测环境变量 / .env / OpenClaw 配置，零输入直接复用
  - 引导模式（guided）：3 步完成 — 选模型 → 填 API Key → 选部署方式
  - 高级模式（advanced）：保留完整手动配置流程
  - `dtflow setup --mode auto|guided|advanced` 跳过交互选择
  - PRESETS 每个模型增加 base_url，引导模式自动填入
- **封版三件套**
  - 封版时自动生成 CHANGELOG.md — 从 state tasks 分已完成/未完成列表
  - 封版后自动创建下一版本目录 — patch 递增 + docs/src + 初始 .state.json
  - DEPLOYMENT.md 自动填充 — 从 config.deploy 读取 host/user/path/命令，缺失字段显示"待配置"

## v0.8.0 (2026-03-24)

**Feature: OpenClaw 编排器 + ClawHub 发布**

- `openclaw_subagent.py` 完全重写：从纯占位变为完整实现
  - 新增 `_OpenClawLLM` 类，独立于 `local_llm`，从 `config.openclaw` 读取 base_url / api_key / model
  - 支持全部 5 个 action：analyze / write / review / fix / comprehensive_review
  - 支持环境变量 fallback（`DTFLOW_OPENCLAW_*`）
  - prompt 加载、JSON 解析、FILE block fallback 与 local_llm 一致
- `publish_flow.py` 新增 `ClawHubPublishAdapter`
  - 检查 clawhub CLI 可用性 + 登录状态
  - 验证 SKILL.md 存在
  - 调用 `clawhub publish` 发布
  - 结果记录到 state
- `cli.py`：publish 命令 `--target` 新增 `clawhub` 选项
- `templates/config.json`：
  - `openclaw` 段新增 `base_url` / `api_key` / `model` 字段
  - `adapters.publish` 默认值改为 `clawhub`
- `docs/B2_IMPLEMENTATION_PLAN.md` 更新为全部 Phase 已完成

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
