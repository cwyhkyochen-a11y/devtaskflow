# DevTaskFlow

> 用自然语言发起开发任务，让 AI 帮你把 **需求 → 方案 → 代码 → 审查 → 修复 → 部署 → 发布** 串成一条真正可执行的流水线。

<p align="center">
  <strong>不会写代码，也能把想法做成软件。</strong><br/>
  这不是一句口号，是 DevTaskFlow 想认真推进的事情。
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/cwyhkyochen-a11y/devtaskflow/main/assets/cli-demo.png" alt="DevTaskFlow CLI Demo" width="800"/>
  <br/>
  <em>一句自然语言需求 → 自动拆任务 → 生成代码 → 看板追踪</em>
</p>

---

## 看一眼就懂：它怎么工作

你在终端里只需要做一件事：**说清楚你想做什么。**

```
$ dtflow start --new-project --name crm-lite --idea "给销售团队用的客户管理工具"
```

然后 DevTaskFlow 自动帮你完成：

| 步骤 | 做什么 | 你需要做什么 |
|------|--------|-------------|
| 分析需求 | 把你的描述拆成具体任务 | 确认方案 |
| 生成代码 | 调用 AI 写出完整项目代码 | 预览确认 |
| 代码审查 | 自动检查代码质量 | 看结果 |
| 自动修复 | 发现问题立刻修复再复审 | 无 |
| 本地运行 | 启动项目让你实际看看 | 确认上线 |
| 部署上线 | 推到服务器 | 无 |
| 封版归档 | 保存版本快照 | 无 |
| GitHub 发布 | 创建 Release | 无 |

你不需要记步骤顺序，不需要手动切换，系统根据当前状态自动推进。

```text
提需求 → 分析 → 确认 → 生成代码 → 审查 → 修复 → 部署 → 封版 → 发布
```

---

## 为什么做这个

很多人有业务理解、有场景、有产品直觉，甚至比工程师更清楚问题出在哪里。

但现实是：

- 不会写代码，就很难自己把工具做出来
- 找外包、排开发、反复沟通，时间和成本都很高
- 即使有 AI，对普通人来说也常常只是“会聊天”，离真正落地还差很远

**DevTaskFlow 要解决的，不是“再做一个代码生成器”，而是把软件开发变成一条普通人也能走通的流程。**

你不需要先学会 React、数据库、部署、代码审查。
你只需要先把需求说清楚。

这就是我理解的一个方向：**让技术能力不再只属于少数人，让更多有想法的人真正拥有构建能力。**

> 技术不该只服务会写代码的人。  
> 技术应该成为更多人的杠杆。  
> 这就是「技术平权」想落到地上的样子。

---

## DevTaskFlow 是什么

DevTaskFlow 是一个面向真实开发流程的 CLI / Skill 工具。

它不是只吐一段代码，也不是只给你一份 PPT 式方案，而是把一个项目从 0 推到可运行、可检查、可发布的状态。

它做的事情包括：

- 接收自然语言需求
- 自动分析需求并拆任务
- 生成项目版本目录和状态文件
- 调用 LLM 执行代码生成
- 做结构化代码审查
- 发现问题后自动修复再复审
- 支持本地运行、部署、封版、发布
- 提供项目看板，看到所有项目当前进度

一句话说：

**DevTaskFlow 不是帮你“写一点代码”，而是帮你“把开发这件事跑起来”。**

---

## 适合谁

### 1) 不会写代码，但想把想法做出来的人

- 产品经理
- 运营
- 销售团队负责人
- 创业者
- 业务负责人
- 想给自己做小工具的普通用户

### 2) 会写代码，但想提升效率的人

- 想快速验证想法的开发者
- 需要把需求、审查、修复流程标准化的团队
- 想把 AI 接入自己开发流程的人

### 3) 需要“流程可追踪”的场景

不是所有人都接受“AI 一次性写完一坨代码”。
很多时候更需要的是：

- 每一步都知道发生了什么
- 能确认方案
- 能预览写入内容
- 有审查和修复闭环
- 有版本记录和发布记录

DevTaskFlow 就是按这个方向设计的。

---

## 核心价值

### 1. 从“聊天式 AI”升级成“可执行开发流程”

很多 AI 工具的问题，不是不会写代码，而是**没有流程约束**：

- 需求没澄清就开始写
- 代码写完没人审
- 修了一个 bug 又引入另一个 bug
- 没有版本状态，做着做着就乱了

DevTaskFlow 把这些关键环节收进了同一条流水线。

### 2. 对非技术用户更友好

你不需要一上来就讲技术栈。

你可以像这样说：

> 我想做一个客户管理工具，给销售团队用。  
> 需要录入客户资料、搜索、跟进状态、备注，界面尽量简洁，最好手机也能用。

这就够启动一个项目了。

### 3. 把“项目状态”变成清晰资产

每个项目都有：

- 独立配置
- 独立版本目录
- 独立状态文件
- 可视化 / 文字看板
- 发布和封版记录

不是一次性对话产物，而是可持续演进的工程资产。

### 4. 给 AI 加上边界和护栏

DevTaskFlow 不是无脑放权给模型。

它强调：

- 状态机推进
- 写入前预览
- JSON-first 结构化输出
- 审查 / 修复闭环
- 路径安全限制
- 环境与依赖诊断

这能显著降低“看起来很聪明，落地时一团乱”的概率。

---

## 一图看懂整体架构

### 架构图

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
  │    └── openclaw_subagent
  └── adapters
       ├── llm adapter
       ├── deploy adapter
       ├── archive adapter
       └── openclaw adapter
```

### 架构理解

- **CLI 层**：用户入口，负责命令分发
- **project-board / state**：负责项目与版本状态管理
- **pipeline core**：负责开发主流程推进
- **orchestrator**：负责把不同执行后端统一起来
- **adapters**：负责对接 LLM、部署、归档、OpenClaw 等外部能力

这个分层的目的很简单：

> 把“开发流程”从某个具体模型、某个平台、某种部署方式里解耦出来。

这样未来不管底层换 Claude、GPT、Mimo，还是接 OpenClaw 子 agent，核心工作流都能复用。

---

## 工作流长什么样

```text
提需求
  ↓
分析需求（analyze）
  ↓
确认方案（confirm）
  ↓
生成代码（write）
  ↓
代码审查（review）
  ↓
发现问题自动修复（fix）
  ↓
本地运行 / 验证（run）
  ↓
部署上线（deploy）
  ↓
封版归档（seal）
  ↓
发布到 GitHub（publish）
```

这条链路里最关键的不是“步骤多”，而是：

- 每一步都有状态
- 每一步都能继续 / 恢复
- 每一步都能被看见
- 重要节点有确认机制

这才是能拿去做真实项目的基础。

---

## 项目结构

```text
DevTaskFlow/
├── commands/              # CLI 启动入口
├── lib/                   # 核心实现
│   ├── cli.py
│   ├── orchestrator.py
│   ├── analyze.py
│   ├── write_flow.py
│   ├── review_flow.py
│   ├── fix_flow.py
│   ├── release_flow.py
│   ├── publish_flow.py
│   ├── state.py
│   ├── project_board.py
│   └── ...
├── prompts/               # LLM 提示词与结构化输出协议
├── templates/             # 初始化模板
├── board/                 # 可视化项目看板服务
├── docs/                  # 架构与实现文档
├── example-project/       # 示例项目
├── README.md
└── SKILL.md
```

### 关键模块说明

- `lib/cli.py`：命令总入口
- `lib/orchestrator.py`：统一调度 analyze / write / review / fix
- `lib/state.py`：维护版本状态
- `lib/project_board.py`：聚合多项目看板数据
- `lib/publish_flow.py`：GitHub release 发布逻辑
- `prompts/`：结构化提示词协议，约束 LLM 输出稳定性
- `board/`：项目总览页面，可浏览器查看

---

## 快速开始

### 1. 配置模型服务

```bash
dtflow setup
```

按提示配置：

- API Base URL
- API Key
- 模型名

当前更推荐用于完整开发任务的模型：

- Claude Opus 4.6
- GPT 5.4 Pro
- GPT 5.4
- Mimo V2 Pro

---

### 2. 发起一个新项目

```bash
dtflow start --new-project --name crm-lite --idea "我想做一个给销售团队使用的客户管理工具，需要录入客户资料、搜索、跟进状态、备注，界面简洁，手机也能用。"
```

系统会自动：

- 创建项目目录
- 初始化版本结构
- 分析需求
- 生成任务拆分
- 推进后续开发状态

---

### 3. 查看所有项目状态

```bash
dtflow board
```

你会看到每个项目当前在哪个阶段。

如果想看可视化看板：

```bash
dtflow board --serve
```

默认地址：

```text
http://localhost:8765
```

---

## 常用命令

### 面向大多数用户

```bash
dtflow setup
dtflow start --new-project --name NAME --idea "你的需求"
dtflow start
dtflow start --confirm
dtflow start --confirm-write
dtflow start --feedback "你的修改意见"
dtflow start --run
dtflow start --deploy
dtflow board
dtflow board --serve
dtflow board-query --name 项目名
```

### 面向进阶用户

```bash
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

## 一个真实使用方式示例

### 场景

你是运营负责人，想做一个内部小工具：

> 我想做一个内容发布管理台，支持账号管理、发布记录、草稿保存，先做 Web 版，团队内部使用。

### DevTaskFlow 会怎么推进

1. 把你的需求变成结构化开发方案
2. 拆成多个可执行任务
3. 生成项目文件和版本目录
4. 调用模型生成代码
5. 自动进行代码审查
6. 有问题则进入修复流程
7. 通过后支持本地运行和部署
8. 最后封版并发布到 GitHub

这时候你面对的就不是抽象的“AI 对话”，而是一条可以继续推进、可以回看、可以交付的开发链路。

---

## 安全与约束

DevTaskFlow 很重视“别把项目搞乱”。

当前已做的安全设计包括：

- 写入路径限制在项目目录内
- 配置和密钥走环境变量 / 本地配置
- 状态文件记录最近动作、错误、摘要
- `write --dry-run` 支持先预览再写入
- 审查与修复分阶段执行
- 项目与版本分层管理，避免状态混乱

这不代表它绝对不会出错。
但它的目标是：**让错误更可见、可诊断、可恢复。**

---

## 当前边界

DevTaskFlow 现在已经能跑通核心流程，但还不是“全自动万能工程平台”。

当前边界大致是：

- ClawHub：负责分发 DevTaskFlow skill 本身
- GitHub：负责被管理项目的封版发布
- dashboard：负责项目总览，不替代专业项目管理系统
- analyze：给方案和任务拆分，不做复杂排期系统
- deploy adapter：对接现成部署能力，不自建云平台

这个边界我觉得是对的。

**先把最核心的链路做扎实，比把边界无限做大更重要。**

---

## 示例项目

仓库内提供了一个最小示例项目：

```bash
cd example-project
cat versions/v0.1.0/docs/REQUIREMENTS.md
```

推荐体验顺序：

1. 看需求文档
2. 理解项目目录结构
3. 体验 analyze / write / review 的流程感

---

## Roadmap

### v0.4.x

- 继续稳定核心工作流
- 优化 README、示例和上手体验
- 强化 GitHub 发布闭环

### 后续方向

- OpenClaw 子 agent 真实接线
- 更强的 async / resume 能力
- 更清晰的 renderer / protocol 分层
- 更稳定的结构化结果解析
- 更丰富的部署适配器

---

## 适合开源协作的方向

如果你认同这个方向，欢迎一起推进这些事情：

- 改进提示词协议稳定性
- 增强状态机和恢复机制
- 优化看板体验
- 增加更多部署 / 发布适配器
- 补更多示例项目
- 做更友好的中文文档和教程

如果做成，这不会只是一个给开发者玩的工具。

它更可能变成一种能力基础设施：

> 让产品、运营、业务、创作者、独立个体，也能更低门槛地发起软件开发。

---

## 版本

当前目标发布版本：**v0.4.1**

---

## 最后

我不觉得“AI 写代码”最有价值的地方，是让程序员多快 20%。

我更在意的是：

**能不能让本来没有开发能力的人，也第一次拥有把想法变成工具的能力。**

如果能做到这一点，哪怕只前进一步，都值得。

如果你也认同这件事，欢迎试试 DevTaskFlow，提 issue，提建议，或者一起把它打磨得更靠谱。
