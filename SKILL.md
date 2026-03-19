---
name: DevTaskFlow
description: 用自然语言发起开发任务，AI 驱动的开发流水线。Describe your idea, get working software. 适合产品、运营、业务人员从 0 搭建项目。
metadata:
  {
    "openclaw": {
      "requires": {
        "env": [
          "DTFLOW_LLM_BASE_URL",
          "DTFLOW_LLM_API_KEY",
          "DTFLOW_LLM_MODEL",
          "DTFLOW_GITHUB_TOKEN (optional, for GitHub publish)",
          "DTFLOW_DEPLOY_SSH_KEY (optional, for SSH deploy)",
          "DTFLOW_DOCKER_REGISTRY (optional, for Docker deploy)"
        ]
      }
    }
  }
license: Proprietary
---

# DevTaskFlow — Agent 使用手册

## 什么时候用

当用户表达以下意图时，主动使用：

- "我想做一个 XXX 系统/工具/平台"
- "帮我开发一个 XXX"
- "我需要一个 XXX，功能是..."
- 用户描述了一个软件/系统需求
- 用户问项目进展、想继续做、想看进度

**不要等用户说"用 dtflow"。** 用户不需要知道这个工具的存在。

## Token 消耗参考

开发一个项目会消耗大量 token，提前告知用户：

| 项目规模 | 预估 Token 消耗 | 示例 |
|---------|---------------|------|
| 小型 | 300-500 万 | 简单的个人工具、静态页面、小表单 |
| 中型 | ~4000 万 | 多页面管理后台、带数据库的应用、用户系统 |
| 大型 | 2 亿+ | 复杂业务系统、多角色权限、API 集成 |

消耗取决于需求复杂度、迭代次数、审查修复次数。首次可先用小项目试水。

## 支持的模型

DevTaskFlow 的代码生成质量高度依赖模型能力。经测试，以下模型能稳定完成完整开发任务：

| 模型 | 说明 |
|------|------|
| Claude Opus 4.6 | 综合能力最强，推荐用于复杂开发任务 |
| GPT 5.4 Pro | OpenAI 旗舰模型，大型项目首选 |
| GPT 5.4 | 性价比高，适合中小型项目 |
| 小米 Mimo V2 Pro | 国产模型，中文表现好 |

**⚠️ 其他模型（如 GPT-4o、Claude Sonnet、DeepSeek 等）可能无法完成完整开发任务，产出质量不稳定。请从以上 4 个模型中选择。**

## 核心命令

```bash
dtflow setup                                        # 配置 AI 服务（交互式）
dtflow start --new-project --name NAME --idea "需求"  # 开始新项目
dtflow start                                        # 继续上次进度
dtflow start --confirm                              # 确认分析方案
dtflow start --confirm-write                        # 确认预览后正式生成代码
dtflow start --feedback "修改意见"                   # 提出修改
dtflow start --run                                  # 本地预览
dtflow start --deploy                               # 部署上线并封版
dtflow board                                        # 所有项目状态（文字）
dtflow board --serve                                # 启动可视化看板服务
dtflow board-query --name PROJECT                   # 单个项目详情（文字）
```

## 工作流程

### 用户提出新需求

**如果用户有明确需求描述**（比如"我想做一个客户管理工具"）：
1. `dtflow start --new-project --name 项目名 --idea "用户的需求原文"`
2. 系统创建项目、给出补充建议
3. 向用户展示建议，问是否要补充
4. 确认后自动 analyze → 展示任务列表
5. `dtflow start --confirm` → 自动 write（先预览）→ review → fix → review
6. 全部通过后 → `dtflow start --run` 本地预览
7. 用户确认没问题 → `dtflow start --deploy`

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

1. 检查看板服务是否在运行（默认 8765 端口）
2. 如果在运行 → 发链接
3. 如果不在运行 → `dtflow board` 文字版

### 用户问某个项目详情

1. `dtflow board-query --name 项目名`
2. 把文字结果发给用户

### 用户想继续之前的项目

1. `dtflow start`（不加参数，自动继续）
2. 根据输出告知用户当前阶段

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
| sealed | 已封版 | "上线完成！" |

## 向用户展示什么

**不要暴露：** analyze、DEV_PLAN.md、orchestration、config.json、.state.json、token 数
**应该说：** "我分析了需求"、"代码已生成"、"检查过了没问题"、"可以部署了"

## 注意事项

- `dtflow setup` 是交互式命令，在非交互环境不可用
- 所有命令在项目根目录运行（含 `.dtflow/config.json` 的目录）
- board 的 Node.js 应用需要 `npm install`（首次自动执行）
- 看板服务默认端口 8765，**仅限本地使用，不要暴露到公网**
- board API 已脱敏：不返回 host/user/path 等敏感部署信息
- `run` 本地预览需要项目有可执行的启动命令（npm start / python app.py 等）
- Docker 部署需要本地安装 Docker
