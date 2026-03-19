# DevTaskFlow

**不会写代码，也能把想法做成软件。**

> 用自然语言发起开发任务，AI 驱动的开发流水线 —— 需求 → 方案 → 代码 → 审查 → 修复 → 部署 → 发布，一条链路跑通。

---

## 它怎么工作

你在终端里只需要做一件事：**说清楚你想做什么。**

```
$ dtflow start --new-project --name ppt-maker --idea "帮我做一个PPT制作工具，我提需求，你拆解页面并生成PPT"
```

DevTaskFlow 会自动分析你的需求，输出一份完整的分析报告：

<p align="center">
  <img src="https://raw.githubusercontent.com/cwyhkyochen-a11y/devtaskflow/main/assets/analysis-demo.png" alt="DevTaskFlow Analysis Phase" width="720"/>
  <br/>
  <em>输入需求 → 自动生成功能拆解、任务清单、技术方案、风险评估</em>
</p>

确认方案后，剩下的事情自动推进：

| 步骤 | 做什么 | 你需要做什么 |
|------|--------|-------------|
| 生成代码 | 调用 AI 写出完整项目代码 | 预览确认 |
| 代码审查 | 自动检查代码质量 | 看结果 |
| 自动修复 | 发现问题立刻修复再复审 | 无 |
| 本地运行 | 启动项目让你实际看看 | 确认上线 |
| 部署上线 | 推到服务器 | 无 |
| 封版归档 | 保存版本快照 | 无 |
| GitHub 发布 | 创建 Release | 无 |

你不需要记步骤顺序，不需要手动切换，系统根据当前状态自动推进。

<p align="center">
  <img src="https://raw.githubusercontent.com/cwyhkyochen-a11y/devtaskflow/main/assets/cli-demo.png" alt="DevTaskFlow CLI Demo" width="800"/>
  <br/>
  <em>多项目看板追踪：一句话需求 → 自动拆任务 → 生成代码 → 进度可视化</em>
</p>

---

## 为什么做这个

很多人有业务理解、有场景、有产品直觉，甚至比工程师更清楚问题出在哪里。但现实是：

- 不会写代码，就很难自己把工具做出来
- 找外包、排开发、反复沟通，时间和成本都很高
- 即使有 AI，对普通人来说也常常只是"会聊天"，离真正落地还差很远

DevTaskFlow 要解决的，不是"再做一个代码生成器"，而是**把软件开发变成一条普通人也能走通的流程**。

你不需要先学会 React、数据库、部署、代码审查。你只需要先把需求说清楚。

> 技术不该只服务会写代码的人。技术应该成为更多人的杠杆。

---

## 核心能力

**从自然语言到可运行软件的完整链路：**

- 接收自然语言需求，自动分析并拆任务
- 调用 LLM 生成完整项目代码
- 结构化代码审查，发现问题自动修复
- 支持本地运行、部署、封版、GitHub 发布
- 多项目看板，进度一目了然

**对非技术用户友好：**

不需要讲技术栈，像这样说就够了：

> 我想做一个客户管理工具，给销售团队用。需要录入客户资料、搜索、跟进状态、备注，界面尽量简洁，最好手机也能用。

**给 AI 加上护栏：**

- 状态机推进，每一步都有记录
- 写入前可预览（`--dry-run`）
- 审查 / 修复闭环，避免越修越乱
- 路径安全限制，不会写到项目外面

---

## 适合谁

- **不会写代码但想把想法做出来的人** — 产品经理、运营、创业者、业务负责人
- **会写代码但想提升效率的人** — 快速验证想法、标准化开发流程
- **需要"流程可追踪"的团队** — 每一步都知道发生了什么，有版本记录可回溯

---

## 工作流

```text
提需求 → 分析 → 确认 → 生成代码 → 审查 → 修复 → 本地运行 → 部署 → 封版 → 发布
```

每一步都有状态，每一步都能继续 / 恢复，每一步都能被看见。

---

## 快速开始

### 1. 配置

```bash
dtflow setup
```

按提示配置 API Base URL、API Key、模型名。推荐模型：

- Claude Opus 4.6
- GPT 5.4 Pro / GPT 5.4
- Mimo V2 Pro

### 2. 发起新项目

```bash
dtflow start --new-project --name crm-lite --idea "我想做一个给销售团队使用的客户管理工具，需要录入客户资料、搜索、跟进状态、备注，界面简洁，手机也能用。"
```

系统会自动创建项目目录、分析需求、生成任务拆分，并推进后续开发状态。

### 3. 查看项目状态

```bash
dtflow board          # 文字看板
dtflow board --serve  # 可视化看板 → http://localhost:8765
```

---

## 常用命令

```bash
# 基础流程
dtflow setup                                    # 配置模型
dtflow start --new-project --name NAME --idea "…" # 新建项目
dtflow start                                     # 继续推进
dtflow start --confirm                           # 确认方案
dtflow start --confirm-write                     # 确认写入
dtflow start --feedback "修改意见"                # 反馈
dtflow start --run                               # 本地运行
dtflow start --deploy                            # 部署
dtflow board                                     # 看板
dtflow board --serve                             # 可视化看板
dtflow board-query --name 项目名                  # 查询单项目

# 进阶操作
dtflow advanced analyze
dtflow advanced write --dry-run
dtflow advanced write
dtflow advanced review
dtflow advanced fix
dtflow advanced deploy
dtflow advanced seal
dtflow advanced publish
```

---

## 使用示例

**场景：** 你是运营负责人，想做一个内部小工具。

> 我想做一个内容发布管理台，支持账号管理、发布记录、草稿保存，先做 Web 版，团队内部使用。

**DevTaskFlow 会怎么推进：**

1. 把需求变成结构化开发方案
2. 拆成可执行任务，生成项目文件和版本目录
3. 调用模型生成代码，自动审查
4. 有问题进入修复流程
5. 通过后本地运行验证，部署上线
6. 封版归档，发布到 GitHub

你面对的不是抽象的"AI 对话"，而是一条可以继续推进、可以回看、可以交付的开发链路。

---

## 架构

模块化设计，核心流程与具体模型、部署方式解耦，未来换底层不影响工作流。

```text
CLI (dtflow)
  ├── pipeline core     # 开发主流程（analyze → write → review → fix → deploy → seal）
  ├── orchestrator      # 调度层（本地 LLM / OpenClaw 子 agent）
  ├── state + board     # 项目状态与看板
  └── adapters          # 对接外部能力（LLM、部署、归档、OpenClaw）
```

详细架构说明见 `docs/` 目录。

---

## 安全与约束

- 写入路径限制在项目目录内
- 配置和密钥走环境变量 / 本地配置
- 状态文件记录最近动作、错误、摘要
- `write --dry-run` 支持先预览再写入
- 审查与修复分阶段执行
- 项目与版本分层管理

目标：**让错误更可见、可诊断、可恢复。**

---

## 示例项目

仓库内提供了一个最小示例：

```bash
cd example-project
cat versions/v0.1.0/docs/REQUIREMENTS.md
```

推荐体验顺序：看需求文档 → 理解目录结构 → 体验 analyze / write / review 的流程感。

---

## Roadmap

### 当前

- ✅ 核心流水线跑通（analyze → write → review → fix → deploy → seal → publish）
- ✅ 多项目看板
- ✅ GitHub Release 发布
- ✅ OpenClaw 子 agent 集成

### v0.4.x

- 稳定核心工作流
- 优化上手体验和示例
- 强化 GitHub 发布闭环

### 后续方向

- 更强的 async / resume 能力
- 更丰富的部署适配器
- 更稳定的结构化结果解析
- ClawHub 分发 → GitHub 发布 → 可视化看板 三端联动

当前边界：聚焦核心开发链路，不自建云平台、不做复杂排期系统。先把最核心的链路做扎实。

---

## 参与贡献

欢迎一起推进：

- 改进提示词协议稳定性
- 增强状态机和恢复机制
- 优化看板体验
- 增加更多部署 / 发布适配器
- 补更多示例项目
- 做更友好的中文文档和教程

---

## 版本

当前目标发布版本：**v0.4.1**

---

## 最后

我不觉得"AI 写代码"最有价值的地方，是让程序员快 20%。

我更在意的是：**能不能让本来没有开发能力的人，也第一次拥有把想法变成工具的能力。**

如果能做到这一点，哪怕只前进一步，都值得。

欢迎试试 DevTaskFlow，提 issue、提建议，或者一起把它打磨得更靠谱。
