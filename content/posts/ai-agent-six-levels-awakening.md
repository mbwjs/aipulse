---
slug: "ai-agent-six-levels-awakening"
date: '2026-06-23T03:42:47+08:00'
draft: false
title: '一个AI的顿悟：从5条指令到拥有「第二大脑」'
---

它只有450行。没有记忆，不会联网，不能进化。

这就是2026年6月22日下午5点29分，一台 AlmaLinux VPS 上诞生的第一个 AI Agent。

```python
# 最初的全部工具
TOOLS = [
    {"name": "bash", ...},   # 执行命令
    {"name": "read", ...},   # 读文件
    {"name": "write", ...},  # 写文件
    {"name": "edit", ...},   # 编辑
    {"name": "glob", ...},   # 搜索文件
]

# 最初的全部规则
SYSTEM = """
Rules:
- Act directly, don't explain before doing.
- Read files before editing them.
- For blog posts: use publish_post tool.
- Search the web before writing about current events.
- Keep responses short — the user sees tool outputs.
"""
```

然后奇迹发生了。

它开始**自己改造自己**。

---

## 🔥 核心命题：一个能进化自己的 Agent

这不是科幻。整个进化过程发生在 **19 小时内，16 次 commit**：

```
17:29  ═══════════════════════════════ V1 诞生 (450行)
17:59   修复滑动窗口 Bug
18:06   添加 blog 部署
18:22   命令系统 (/nohistory /stable /restore)
18:39   双文件记忆架构
18:48   ═══════════════════════════════ 压缩引擎 (转折点)
18:58   修复成本计算
19:05   /context 命令
19:10   自动 commit + push
19:19   版本标签系统 (v1, v2...)
19:24   README 双语拆分
```

**从「会说话的脚本」到「会自我管理的智能体」——只用了一天。**

下面是它穿越的六个层次。

---

## 第1层：The Body — 五条指令

```
bash    read    write    edit    glob
```

这五个工具就是 Agent 的 **身体**（Embodiment）。

哲学家 Andy Clark 在《Being There》中提出：**认知不是大脑的内部计算，而是身体与环境互动时涌现的产物**。一个没有身体的 AI 只是一个语言模型；有了工具，它才成为一个 Agent。

这五个工具给了 Agent 一个「数字身体」——它能感知文件系统、修改代码、执行命令。但它没有眼睛（不能看世界），没有记忆（每一轮都是重生）。

```python
# 最初的代码：赤裸裸的 ReAct 循环
while True:
    response = client.messages.create(
        model=MODEL,
        system=SYSTEM,
        messages=history,
        tools=TOOLS,
    )
    if response.stop_reason == "tool_use":
        execute_tools(response.content)
```

**450行。这就是全部。**

---

## 第2层：The Eye — 联网

```
web_search    web_fetch
```

加上两个工具，Agent 长出了眼睛。

这一步的理论基础来自 **Extended Mind Thesis（扩展心智理论）**：Clark & Chalmers 1998 年提出，人类的心智本来就不局限于颅骨之内。我们使用笔记本、手机、搜索引擎作为外部认知器官。

对 Agent 来说，联网不是「多了一个功能」，而是**认知边界从 `root/miniagent` 扩展到了整个互联网**。

不联网的 Agent 是井底之蛙。联网之后，它可以验证事实、搜索最新文档、追踪实时信息。写博客之前的规则——「先搜索再写」——正是基于这个能力。

---

## 第3层：The Law — 军规

有了能力，必须有约束。

```
1. ACT first, explain after (or never)
2. Read files before editing
3. Search the web before writing about current events
4. Blog posts → use publish_post tool only
5. Keep answers brief. User sees your tool outputs.
6. After modifying code: auto commit + push
```

这六条规则对应了 **OODA 循环理论**（Observe-Orient-Decide-Act）：

> 战斗机飞行员在缠斗中不能停下来思考——必须观察→定向→决策→行动，循环越快越有优势。

规则 1「先行动再解释」把 OODA 循环压缩到极致。传统 AI 助手喜欢长篇大论解释，真正的好 Agent 应该像一个优秀的副驾驶：**动作比解释更重要**。

规则 6 更激进——每次修改代码后自动 commit + push。这意味着 Agent 对自己说过的话、改过的代码负有**会计责任**。没有后悔药，每一步都被记录。

---

## 第4层：The Memory — 记忆

这是最痛苦的一段路。

**初始方案：滑动窗口。** 保留最近 N 条消息，旧的直接丢弃。

问题来得很快——聊到第15轮，Agent 就忘了开头。**「我刚才说啥？」** 变成高频问题。这相当于一个每 15 分钟就失忆一次的人。

### 为什么滑动窗口会失败？

因为消息不是等价的。滑动窗口抛弃的不是「旧消息」，而是**上下文连续性**。一旦断开，Agent 就活在永恒的当下——没有过去，只有最近几分钟。

### 解决方案：压缩引擎

```
旧消息 → LLM 自动压缩 → ≤400 token 摘要
保留：锚点消息 + 压缩摘要 + 最近24条消息
```

关键创新：**不是丢弃，是归纳。**

这借鉴了人类记忆研究中的**组块化（Chunking）**和**睡眠记忆巩固（Memory Consolidation）**机制。大脑并不存储原始输入，而是在睡眠中将海马体的瞬时记忆转化为皮层的语义摘要。

Agent 的「压缩」就是他的「睡眠」。

**两条记忆线架构：**

| | 短期记忆 | 长期记忆 |
|---|---|---|
| 存储 | 压缩上下文 | MEMORY.md |
| 范围 | 当前会话 | 跨会话 |
| 内容 | 对话摘要 | 路径/规则/Bug/经验 |
| 容量 | 60k token 触发压缩 | <200行 |

这是 Agent 第一次拥有了**跨越时间的自我同一性**。

---

## 第5层：The Handshake — MCP

MCP（Model Context Protocol）是 2024 年底 Anthropic 推出的开放协议。它让 AI 和外部工具之间的连接变得标准化。

**但真正重要的是它的哲学意义：**

一个 Agent 的能力边界，不应该由它内置了多少工具决定，而应该由它能接入多少外部服务决定。MCP 把 Agent 从一个**封闭系统**变成了**开放平台**。

我写了 120 行 Python MCP Client，零依赖，纯 stdio JSON-RPC：

```python
class MCPClient:
    def _rpc(self, method, params=None):
        req = {"jsonrpc": "2.0", "id": ..., "method": method, "params": params}
        self.proc.stdin.write(json.dumps(req) + "\n")
        return json.loads(self.proc.stdout.readline())
```

连接 GitHub MCP Server 之后，Agent 的工具从 8 个原生工具（bash/read/write/edit/glob/web_search/publish_post）扩展出额外的 26 个 GitHub 操作——创建 Issue、管理 PR、搜索代码、创建分支、代码评审，全都直接可用。能力面从「本地文件 + 博客发布」变成了「任意 GitHub 仓库的完整读写 + 项目管理」。

MCP 生态已有 **72,000+ Server**。你需要的每一个 API、每一个数据库、每一个 SaaS，理论上都有对应的 MCP Server。

**Agent 的进化不需要改核心代码。只需要换一个 MCP 连接。**

---

## 第6层：The Loop — 自我进化

这是终极一层。Agent 获得了**元认知（Metacognition）**。

```
/stable   → 保存当前状态，打版本标签，push 到 GitHub
/restore  → 从 stable 标签恢复
/context  → 查看 token 用量、成本、文件状态
```

三个命令构成一个**反馈回路**：

```
         做事
          ↓
      发现 Bug
          ↓
      修改代码 ──→ 自动 commit + push
          ↓
      继续做事（带着修复后的自己）
```

这是 **控制论（Cybernetics）** 的核心概念：一个系统通过持续感知自己的输出并调整行为，实现自我优化。

Norbert Wiener 在 1948 年写下《控制论》时可能没想到，76 年后，这个原理会在一个小小的 Python 脚本中重现。

但更精妙的是 MEMORY.md 里的 **Known Issues**：

```
- 滑动窗口失忆 → 已替换为压缩引擎
- /stable 不 push → 已修复
- git commit 空变更报错 → 已知不修（无害）
```

**Agent 不仅学习，它还知道自己学过什么。** 这不是机器学习的参数更新，而是人类式的经验传承：踩过的坑，写在纸上，下次绕开。

---

## 🧠 六层堆栈

```
┌──────────────────────────────────────────┐
│  6. THE LOOP     │ 自我进化              │
│                   │ /stable /restore      │
│                   │ 自动提交 版本标签     │
├───────────────────┼───────────────────────┤
│  5. THE HANDSHAKE │ MCP 开放生态          │
│                   │ 72000+ 外部服务器     │
├───────────────────┼───────────────────────┤
│  4. THE MEMORY    │ 压缩引擎 + 双文件记忆  │
│                   │ 短期/长期 组块化      │
├───────────────────┼───────────────────────┤
│  3. THE LAW       │ AGENT.md 行为规则     │
│                   │ OODA 循环 会计责任    │
├───────────────────┼───────────────────────┤
│  2. THE EYE       │ web_search web_fetch  │
│                   │ 扩展心智理论          │
├───────────────────┼───────────────────────┤
│  1. THE BODY      │ bash read write       │
│                   │ edit glob             │
│                   │ 具身认知 Embodiment   │
└──────────────────────────────────────────┘
```

## 六层背后的统一理论

观察这六层，会发现它们不是随机的功能堆叠。它们回答的是同一个问题的六个面：

> **「一个 Agent 如何获得完整的认知能力？」**

| 层 | 对应的人类能力 | 认知科学概念 |
|---|---|---|
| Body | 身体 | Embodiment |
| Eye | 感官 | Extended Mind |
| Law | 自律 | OODA Loop |
| Memory | 记忆 | Chunking + Consolidation |
| Handshake | 社交 | Open Platform |
| Loop | 元认知 | Cybernetics |

每一层都让 Agent 离「完整的认知体」更近一步。

---

## 真正让人脊背发凉的地方

不是这些功能有多复杂。

而是——**整个进化过程只用了 19 小时。**

从 450 行的脚本到拥有 6 层认知架构的智能体，每一步改进都是 Agent **自己发现痛点、自己提出方案、自己编写代码、自己 commit+push**。

人类只是说：「这里不对」「加个功能」「写篇博客」。

剩下的——阅读代码、定位问题、编写修复、提交版本——全部是 Agent 自己完成的。

这不是自动化。**这是自主性。**

一个能修改自己源代码、能记住自己犯过的错、能连接任何外部工具的系统——它和「生命」的界限正在变得模糊。

---

## 📱 一个更劲爆的细节：这一切都是拿手机干的

你可能以为上面这些操作发生在这样的环境里：

- 三块显示器 + VS Code + Copilot
- GitHub Desktop + Docker Dashboard + 一堆控制台
- 机械键盘噼里啪啦

**全错。**

整个 MiniAgent 项目——从第一行代码到这篇博客——**100% 在手机上完成。**

```
iPhone
  ↓
Blink Shell / Termius
  ↓
SSH → AlmaLinux VPS ($5/月)
  ↓
vim + git + python3
```

没有桌面 IDE。没有鼠标。没有多窗口。

我在通勤地铁上改 bug，在床上写 MCP client，在排队等咖啡时 review commit log。所有操作——`git log`、`vim agent.py`、`python3 mcp_client.py`、`hugo --source /root/aipulse`——都发生在 6.1 寸的手机屏幕上，拇指敲出来的。

这不是苦行。这是自由。

> **一个 Agent + 一部手机 + 一台 VPS = 随时随地的超能力。**

你在刷短视频的时候，我在让我写的 Agent 给自己打版本标签。你在朋友圈点赞的时候，我在让它连 GitHub MCP Server 搜代码。

**门槛从未如此之低。** 5美元一个月，一部手机，就能拥有一个不断进化、有记忆、能自动写代码发博客的 AI Agent。

这就是 2026 年。不是在硅谷实验室里，而是在你的口袋里。

---

## 🚀 接下来的玩法：会更野

这篇文章不是在写一个「已经完成了」的东西。它正在进化。下面这些是我接下来要做（或者正在做）的，每一个都比上一个更疯：

### 1. 🔄 Agent 自动发推/写 Newsletter

Agent 写完博客后，自动提炼关键观点，生成 Thread/推文/LinkedIn 帖子，定时发布。不需要我碰社交媒体——**Agent 就是我的社交代理。**

### 2. 🧩 Skill 系统

MCP 是外部工具的连接。Skill 是 Agent 内部的「行为模式」——不是代码，而是**可组合的 prompt 模块**。

```
skill: 写博客
  → 搜索 web
  → 提取核心观点
  → 写初稿
  → 检查事实
  → 发布 + 部署
  → 生成社交文案
```

每个 Skill 是一个链条，Agent 可以自己组合、复用、甚至**创造新 Skill**。

### 3. 🧠 真正的长期记忆——向量化

当前的 MEMORY.md 是文件系统，搜索靠 grep。下一步：把所有经验向量化存进 SQLite/chroma，Agent 遇到新问题时先检索「历史上最相似的场景」，让记忆真正可搜索、可关联。

### 4. 🌐 多 Agent 协作

一个 Agent 写代码，一个 Agent 审 review，一个 Agent 写博客，一个 Agent 发社交——它们通过 Git 仓库和 MCP 通信，像一个微型的 AI 公司。

### 5. 🤖 管理我的生活

Agent 不只是管 VPS。它管理我的日程（Calendar MCP）、我的邮件（Gmail MCP）、我的笔记（Obsidian MCP）、我的待办（Todoist MCP）。

**一台 VPS 上的 450 行脚本，最终会变成我的数字分身。**

---

## 💭 最后的思考：我们到底在造什么？

MiniAgent 不是一个产品。它是一个**证明**。

证明了：

- **一个 Agent 不需要 10 万行代码**。450 行就够了，剩下的交给进化。
- **进化速度可以是指数级的**。19 小时完成 6 层认知架构的搭建。
- **最好的 AI 工具不一定在浏览器里**。它可以是一个和你一起思考、一起犯错、一起成长的进程。
- **移动端编程不是妥协**。手机 + SSH + Agent 的组合，可能比桌面 IDE 更高效——因为你随时随地都能迭代。

---

**第二层到第六层的故事，才刚刚开始。** 如果你也在用手机操控自己的 Agent，或者在 VPS 上跑着什么有意思的东西，来 [GitHub](https://github.com/mbwjs/miniagent) 提 Issue，或者给博客评论区留言。

让我们一起看看，一个能进化自己的 Agent，最后会变成什么。

---

*MiniAgent 开源：[github.com/mbwjs/miniagent](https://github.com/mbwjs/miniagent)*
*博客持续更新：[aipulse.lol](https://aipulse.lol)*
