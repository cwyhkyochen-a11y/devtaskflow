---
name: DevTaskFlow
version: 1.1.0
description: 用自然语言发起开发任务，AI 驱动的开发流水线。Describe your idea, get working software. 适合产品、运营、业务人员从 0 搭建项目。
metadata:
  {
    "openclaw": {
      "requires": {
        "python": ">=3.10",
        "node": ">=18"
      }
    }
  }
license: MIT-0
---

# DevTaskFlow — Agent 使用手册

## 什么时候用

当用户表达以下意图时，**主动建议**使用本工具：

- "我想做一个 XXX 系统/工具/平台"
- "帮我开发一个 XXX"
- "我需要一个 XXX，功能是..."
- 用户描述了一个软件/系统需求
- 用户问项目进展、想继续做、想看进度

**识别意图后，向用户建议使用本工具，但必须等用户确认后再执行。** 尤其是涉及代码生成、部署、发布等操作，不要在未经确认的情况下自动执行。

## Token 消耗参考

开发一个项目会消耗大量 token，提前告知用户：

| 项目规模 | 预估 Token 消耗 | 示例 |
|---------|---------------|------|
| 小型 | 300-500 万 | 简单的个人工具、静态页面、小表单 |
| 中型 | ~4000 万 | 多页面管理后台、带数据库的应用、用户系统 |
| 大型 | 2 亿+ | 复杂业务系统、多角色权限、API 集成 |

消耗取决于需求复杂度、迭代次数、审查修复次数。首次可先用小项目试水。

## 支持的模型

推荐模型：Claude Opus 4.6（复杂项目首选）、GPT 5.4（性价比高）、小米 Mimo V2 Pro（中文好）。完整列表和说明见 README.md。

## 编排模式

DevTaskFlow 支持两种编排模式，通过 `config.json` 的 `adapters.orchestration` 切换：

### local_llm（默认）

直接使用环境变量中的 LLM 配置：

```
DTFLOW_LLM_BASE_URL=https://api.openai.com/v1
DTFLOW_LLM_API_KEY=sk-xxx
DTFLOW_LLM_MODEL=gpt-4o
```

### openclaw_subagent

使用独立的 LLM 配置，与主 LLM 分离。适合在 OpenClaw 环境下使用不同模型处理开发任务。

配置方式 A — `config.json` 的 `openclaw` 段：

```json
{
  "adapters": { "orchestration": "openclaw_subagent" },
  "openclaw": {
    "base_url": "https://api.example.com/v1",
    "api_key": "sk-xxx",
    "model": "claude-opus-4-6",
    "timeout_seconds": 900
  }
}
```

配置方式 B — 环境变量：

```
DTFLOW_OPENCLAW_BASE_URL=https://api.example.com/v1
DTFLOW_OPENCLAW_API_KEY=sk-xxx
DTFLOW_OPENCLAW_MODEL=claude-opus-4-6
```

如果 `config.json` 中字段为空，自动 fallback 到环境变量。

## 核心命令

```bash
dtflow setup                                        # 配置 AI 服务（交互式）
dtflow start --new-project --name NAME --idea "需求"  # 开始新项目
dtflow start                                        # 继续上次进度
dtflow start --confirm                              # 确认分析方案，开始生成代码（先预览，用户确认后再写入）
dtflow start --confirm-write                        # 在预览确认后，正式执行代码写入
dtflow start --feedback "修改意见"                   # 提出修改
dtflow start --run                                  # 本地预览
dtflow start --deploy                               # 部署上线并封版
dtflow start --final-review                         # 执行上线前综合审查（9 维度）
dtflow start --deploy-skip-review                   # 跳过综合审查直接部署（仅在用户明确要求跳过或时间紧迫时使用，建议默认走完整审查流程）
dtflow board                                        # 所有项目状态（文字）
dtflow board --serve                                # 启动可视化看板服务
dtflow board-query --name PROJECT                   # 单个项目详情（文字）
dtflow advanced publish --target github              # 发布到 GitHub Releases
dtflow advanced publish --target clawhub             # 发布到 ClawHub
```

## 工作流程

### 用户提出新需求

**如果用户有明确需求描述**（比如"我想做一个客户管理工具"）：
1. `dtflow start --new-project --name 项目名 --idea "用户的需求原文"`
2. 系统创建项目、给出补充建议
3. 向用户展示建议，问是否要补充
4. 确认后自动 analyze → 展示任务列表
5. `dtflow start --confirm` → 自动 write（先预览）→ review → fix → review
6. 全部任务通过后 → **建议先 compact 一次**（减少上下文累积导致的幻觉）— 提醒主 agent 使用 `/compact` 或清理上下文后再执行综合审查 → 综合审查（`dtflow start --final-review`）— 9 维度全面检查
7. 综合审查通过 → `dtflow start --run` 本地预览
8. 用户确认没问题 → `dtflow start --deploy`

**如果用户需求模糊**（比如"我想做个东西管理客户信息"）：
1. 不要直接调用 dtflow，先通过对话引导收集需求
2. 问清楚：
   - 给谁用的？（团队/客户/个人）
   - 最核心的功能是什么？
   - 需要登录吗？
   - 有技术偏好吗？（不知道就帮你选）
3. 收集到足够信息后，拼成需求调用 dtflow start

### 用户想本地预览

1. `dtflow start --run`
2. 返回访问链接给用户

### 用户想看项目进展

1. 检查看板服务是否在运行（`curl -s http://localhost:8765 > /dev/null && echo "running" || echo "stopped"`）
2. 如果在运行 → 发链接
3. 如果不在运行 → `dtflow board` 文字版

### 用户问某个项目详情

1. `dtflow board-query --name 项目名`
2. 把文字结果发给用户

### 用户想继续之前的项目

1. `dtflow start`（不加参数，自动继续）
2. 根据输出告知用户当前阶段

### 用户想发布

**发布到 GitHub：**
1. 确保项目已封版（sealed）或已部署（deployed）
2. 确保已安装 `gh` CLI 并登录
3. `dtflow advanced publish --target github`

**发布到 ClawHub：**
1. 确保项目已封版或已部署
2. 确保已安装 `clawhub` CLI 并登录
3. 确保项目根目录有 `SKILL.md`
4. `dtflow advanced publish --target clawhub`

### 首次使用（环境未配置）

1. `dtflow setup` 交互式引导（含 AI 配置 + 部署方式选择）
2. 非交互环境下手动创建 `.env`：
   ```
   DTFLOW_LLM_BASE_URL=...
   DTFLOW_LLM_API_KEY=...
   DTFLOW_LLM_MODEL=...
   ```

## 状态机

`dtflow start` 自动推进，你只需知道阶段：

| 状态 | 含义 | 你该说什么 |
|------|------|-----------|
| created | 刚创建 | "项目已创建，正在分析需求..." |
| pending_confirm | 方案已出 | "我分析了你的需求，建议做这几件事：..." |
| confirmed | 已确认 | "好的，开始生成代码..." |
| writing/written | 代码已生成 | "代码写好了，我在检查..." |
| needs_fix | 有问题 | "发现几个小问题，已修复：..." |
| review_passed | 审查通过 | "代码没问题了，要本地先看看效果吗？" |
| pending_final_review | 综合审查待执行 | "运行 dtflow start --final-review 执行综合审查，或 --deploy-skip-review 跳过" |
| ready_to_deploy | 综合审查通过 | "可以部署了，运行 dtflow start --deploy" |
| needs_final_fix | 综合审查发现问题 | "运行 dtflow start 自动修复并重新审查" |
| sealed | 已封版 | "上线完成！" |

## 向用户展示什么

**不要暴露：** analyze、DEV_PLAN.md、orchestration、config.json、.state.json、token 数
**应该说：** "我分析了需求"、"代码已生成"、"检查过了没问题"、"可以部署了"

## 注意事项

- `dtflow setup` 是交互式命令，在非交互环境不可用
- 所有命令在项目根目录运行，项目根目录是包含 `.dtflow/config.json` 的目录，可通过 `ls .dtflow/config.json` 确认
- board 的 Node.js 应用需要 `npm install`（首次自动执行）
- 看板服务默认端口 8765，**仅限本地使用，不要暴露到公网**
- board API 已脱敏：不返回 host/user/path 等敏感部署信息
- `run` 本地预览需要项目有可执行的启动命令（npm start / python app.py 等）
- Docker 部署需要本地安装 Docker
- `openclaw_subagent` 编排器需要在 `config.json` 或环境变量中配置独立的 LLM 连接信息

### 常见问题处理

- **dtflow 命令报错**: 检查是否在项目根目录（含 `.dtflow/config.json`）、模型 API Key 是否有效、余额是否充足
- **部署失败**: 检查 Docker/SSH 连接、目标服务器权限、config.json 中的 deploy 配置
- **审查反复不通过**: 检查是否有结构性问题（如框架选择不当），必要时让用户给出报错信息手动排查
- **run 启动失败**: 检查项目启动命令（`npm start` / `python app.py`）、依赖是否安装完整

### 边界场景

- **用户想取消项目**: 归档项目（状态设为 archived）但不删除文件，保留以便后续恢复
- **用户中途改需求**: 如果是小调整 → 用 `dtflow start --feedback "修改意见"` 在当前版本迭代；如果是大方向变更 → 建议新建版本（`dtflow advanced version --new`）
