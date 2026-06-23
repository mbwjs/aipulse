---
slug: "我用ssh养了一个ai分身不写一行代码靠说话进化了半年"
date: '2026-06-23T04:21:41+08:00'
draft: false
title: '我用SSH养了一个AI分身：不写一行代码，靠说话进化了半年'
---

## 打开方式：一个终端，一句"你 ›"

没有 VSCode。没有 Copilot 弹窗。没有拖拽式工作流。

只有 Putty 里的黑底绿字：**`你 ›`**

我在这台 Almalinux 9 的 VPS 上跑了半年，没手动写过一行代码。博客是跟他说的，钩子系统是跟他说的，密钥扫描也是跟他说的。他写代码，我说话。

## 这不是 AI 助手，这是 AI 分身

普通 AI 工具的逻辑是：你写代码，它补全。你是驾驶员，它是导航。

MiniAgent 的逻辑是反过来的。它是一套微缩版的操作系统，跑在 VPS 上，SSH 进去就是他的世界。你说"发一篇关于钩子系统的博客"，他搜索、阅读、写作、构建、部署、备份到 GitHub——全部自己完成。你只负责说。

```
╔══════════════════════════════════════╗
║        🧠 MiniAgent (VPS)           ║
╚══════════════════════════════════════╝
  model: deepseek-v4-pro
  cwd:   /root/miniagent
  blog:  https://aipulse.lol
  hooks: 6 event types loaded
  ctx:   max 60,000 tokens (compress @ 60k)
```

## 操作系统的三层架构

### 第一层：内核（450行 Python）

cli 解析、工具调度、上下文压缩——这是 OS kernel。启动时加载 AGENT.md（指令集）和 MEMORY.md（持久内存），然后进入事件循环。

没有数据库。没有向量存储。持久化全靠 Markdown 文件 + Git。换一台 VPS，`git clone` 完就能复活。

### 第二层：钩子系统（刚刚完成）

上周 Anthropic 发布了 Claude Code Hooks，我看了很有感触。关掉浏览器，打开终端：

> 你 › 给我也加一个钩子系统

40分钟后，`hooks.json` 诞生。六个生命周期事件：

| 事件 | 触发点 | 用途 |
|------|--------|------|
| SessionStart | 启动 | 环境初始化 |
| SessionEnd | 退出 | 自动备份 |
| UserPromptSubmit | 每次输入 | 合规审查 |
| **PreToolUse** | 工具执行前 | 🚫 阻断危险操作 |
| PostToolUse | 工具成功后 | 自动 git commit |
| PostToolUseFailure | 工具失败后 | 告警 |

所有这些都是对话实现的。我说"PostToolUse 后自动提交"，他改了 `hooks.json` 和 `agent.py`，测试通过，推送到 GitHub。

### 第三层：用户态工具

bash, read, write, edit, glob, web_search, web_fetch, publish_post —— 八个系统调用。AI 用这些工具操作文件系统、读写网络、发布内容。

你永远不需要碰这些工具名。你说"搜一下 GitHub push protection 最新情况"，他自动调 `web_search`。

## 一篇博客的诞生全程

我打了一句话：

> 打造个人agent操作系统——我通过ssh操作，写博文，进化agent，没手写过代码

他读了一遍上下文，开始写这篇博客。

他先跑 `date` 确认现在是2026年，然后构思结构。markdown 生成完毕，`hugo build`，`rsync` 部署到 `/var/www/aitracker`，最后 `git push` 到 GitHub 备份。

全程没有预览、没有手工发布、没有FTP上传。我甚至不知道 Hugo 的命令行参数是什么。他全包了。

## 密钥防护：自己给自己上锁

最讽刺的部分来了。

这个 Agent 能读写文件系统、执行 shell 命令、推送代码到 GitHub。理论上他可以把 API key 写进博客然后推送到公开仓库。

所以我跟他说：

> 添加一个 git 提交时候的强制检测，如果有密钥和隐私数据拒绝提交

他写了一个 `secret_scan.py`，10种正则模式覆盖 AWS/Azure/GitHub/OpenAI/Anthropic/JWT。然后自己把它注册到 PreToolUse 和 PostToolUse 钩子里。

现在每次他尝试 `git commit`，扫描器先跑。检测到密钥 → exit code 2 → 提交被阻断。

他自己给自己上了手铐。钥匙在我手里（我可以改 `hooks.json`），但他不能自己解开。

这就是 AI 安全最优雅的形态：**不是防外部攻击，而是让 Agent 自己监督自己**。

## GitHub Push Protection vs 本地扫描

GitHub 2025年已经对所有公开仓库默认启用 Push Protection，200+ 种密钥模式，还能调 API 验证密钥有效性。但那是服务端最后一道防线。

MiniAgent 的扫描在 `git commit` 阶段就拦截——**秘密还没进 Git 历史就被拦住了**。一旦秘密进了历史，即使用 `git filter-branch` 也很难彻底清除（GitHub 可能有 fork、有缓存、有 webhook 通知）。

两道防线互补：本地 prevent，远端 block。

## 为什么叫"操作系统"而不是"AI助手"

因为操作系统的本质是**资源抽象 + 系统调用 + 用户界面**。

| OS 概念 | 对应 |
|---------|------|
| Shell | `你 ›` 提示符 + 自然语言 |
| Kernel | `agent.py`（事件循环 + 工具调度） |
| System Calls | bash / read / write / web_search / publish_post |
| File System | VPS 上的 Linux 文件系统 |
| Process | 每个 tool call 是一个异步操作 |
| Daemon | 钩子系统监听生命周期事件 |
| Package Manager | `pip install` + 依赖声明 |

传统 OS 的用户是程序员。这个 OS 的用户是**任何人**——你不需要懂 `hugo --buildFuture`，你只需要说"发博客"。

## 为什么用 SSH

因为 SSH 是最干净的人机界面。

没有前端框架、没有 CSS、没有浏览器兼容性问题。一个 TCP 连接，stdin/stdout，UTF-8 字符流。断线了重连就是，tmux 里跑着。

而且 SSH 本身就是天然的权限边界——能连上 VPS 的人才有资格跟 Agent 对话。不需要 OAuth、不需要登录页面、不需要 JWT。

## 半年的进化轨迹

```
v1: bash + read + write，能读写文件
v2: web_search + web_fetch，能上网
v3: publish_post，能发博客
v4: 上下文压缩，不会失忆
v5: MEMORY.md 持久记忆
v6: 钩子系统，不再硬编码
v7: 密钥扫描，自己锁自己
```

每一次进化，我都是在终端里打了一句话。他写了代码、测试了逻辑、提交了 GitHub。

## 你也可以

```bash
git clone git@github.com:mbwjs/miniagent.git
cd miniagent
export ANTHROPIC_API_KEY="sk-ant-..."
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
python3 agent.py
```

一个 Python 文件。SSH 进去。开始说话。

你不是在用 AI 工具。你是在**养自己的 AI 分身**。
