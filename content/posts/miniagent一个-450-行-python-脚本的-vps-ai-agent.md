---
date: '2026-06-23T01:08:57+08:00'
draft: false
title: 'MiniAgent：一个 450 行 Python 脚本的 VPS AI Agent'
---


> **TL;DR** — 我在 VPS 上跑了一个不到 450 行的 AI Agent。它能写代码、搜网页、发博客——现在你读的这篇文章，就是它自己把自己部署上去的。本文拆解 MiniAgent 的架构设计：ReAct 循环、工具系统、滑动窗口上下文管理、成本追踪，以及为什么"够用就好"在 Agent 设计里是一种美德。

## 缘起

这台 VPS 上本来只跑了一个 Hysteria2 代理。后来搭了博客（见[上一篇](/posts/from-zero-to-blog/)），再后来想：能不能让 AI 直接操作这台服务器？

不是"在本地跑 Agent 然后 SSH 到服务器"，而是 **Agent 就住在服务器上**。它读写本地文件、执行 shell 命令、管理博客——就像一个真正的运维。

市面上有不少 Agent 框架，但大多数太重了。LangChain 依赖一堆包，AutoGPT 要 Docker。我想要的是：

- **单文件**，复制即用
- **零配置**，除了 API key 什么都不用设
- **真能干活**，不是 demo

于是有了 MiniAgent。

## 架构：ReAct 循环

MiniAgent 的核心是经典的 **ReAct**（Reasoning + Acting）模式：

```
用户输入 → LLM 推理 → 调用工具 → 结果回传 → LLM 再推理 → ... → 最终回复
```

整个循环在 `agent_loop()` 函数里，不到 70 行：

```python
def agent_loop(messages: list, model: str) -> dict:
    while True:
        # 滑动窗口：保留首条锚定 + 最近 30 条消息
        if len(messages) > 30:
            messages = [messages[0]] + messages[-30:]

        response = client.messages.create(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
            max_tokens=8000,
        )

        # 如果模型不再调用工具，循环结束
        if response.stop_reason != "tool_use":
            return result

        # 执行工具，收集结果
        for block in response.content:
            if block.type == "tool_use":
                output = TOOL_HANDLERS[block.name](**block.input)
                results.append({"type": "tool_result", ...})

        messages.append({"role": "user", "content": results})
```

就这么简单。没有 DAG 编排、没有状态机、没有 Agent 间通信——就是 while 循环 + 工具调用。**够用**。

## 七个工具

MiniAgent 配了 7 个工具，覆盖了 VPS 上最常见的操作场景：

| 工具 | 功能 | 实现要点 |
|------|------|----------|
| `bash` | 执行 shell 命令 | 30 秒超时、危险命令拦截（`rm -rf /`、`sudo`、`shutdown` 等） |
| `read` | 读取文件 | 带行号输出，可选截断 |
| `write` | 写文件 | 自动创建父目录 |
| `edit` | 文本替换 | 精确匹配 + 首次替换 |
| `glob` | 文件搜索 | 标准 glob 模式 |
| `web_search` | 网页搜索 | 基于 DuckDuckGo（`ddgs` 库） |
| `web_fetch` | 抓取网页 | 简单 HTML→文本提取（正则去标签） |
| `publish_post` | 发布博客 | Hugo 构建 → rsync 部署，一站式 |

工具处理函数是统一签名的：

```python
TOOL_HANDLERS = {
    "bash":  run_bash,
    "read":  run_read,
    "write": run_write,
    "edit":  run_edit,
    "glob":  run_glob,
    "web_search": run_web_search,
    "web_fetch":  run_web_fetch,
    "publish_post": run_publish_post,
}
```

添加新工具只需三步：定义 schema → 写 handler → 注册到字典。**扩展成本极低**。

### 安全设计

`bash` 工具是最危险的——它给 LLM 一个真实的 shell。MiniAgent 做了几层防护：

```python
dangerous = ["rm -rf /", "sudo ", "shutdown", "reboot", "mkfs."]
for d in dangerous:
    if d in command.lower():
        return f"Error: blocked '{d}'"
```

这不是沙箱级别的安全（LLM 可以绕过字符串匹配），但它阻止了最常见的灾难性命令。30 秒超时是另一层：即使模型生成了 `yes > /dev/null` 之类的死循环，也会被自动杀死。

真正的防线是：**这只跑在我自己的 VPS 上，没有生产流量，没有用户数据**。

### `publish_post`：从 LLM 到线上

这是最有意思的工具。它做的事：

1. 从标题自动生成 URL slug
2. 生成 Hugo frontmatter（日期、draft 状态）
3. 写入 Markdown 文件到 Hugo 的 `content/posts/`
4. 执行 `hugo --buildFuture` 构建静态站点
5. `rsync` 到 nginx 的 `/var/www/`

整个流程约 30 行代码。这比手动写 Markdown → git commit → 构建 → rsync 快了不止一个数量级。

**你现在读的这篇文章，就是通过这个工具发布上来的。**

## 滑动窗口：长对话不爆上下文

LLM 的上下文窗口有限，但对话可以很长。MiniAgent 用了最简单的方案——**滑动窗口**：

```python
if len(messages) > 30:
    messages = [messages[0]] + messages[-30:]
```

保留第一条消息（作为"锚定"，包含原始任务描述）和最近 30 条。中间的统统丢弃。

这有几个好处：
- 上下文不会无限膨胀，token 消耗可控
- 旧信息丢失反而帮助 Agent"专注当下"
- 实现只需要两行

代价是：如果任务需要很早之前的上下文，Agent 会"忘记"。但对于 VPS 运维和写作任务，这通常不是问题。

## 成本可见

每次 API 调用的 token 消耗和费用都实时显示。MiniAgent 内置了定价表：

```python
PRICING = {
    "deepseek-v4-pro":   {"input": 0.14, "output": 1.10},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}
```

每条消息末尾会显示本轮消耗：

```
[3 turns, +8500i / +1200o | cost: $0.002510]
```

`/cost` 命令可以查看每轮明细，`/tokens` 查看会话累计。

这很重要——不是因为真的花了很多钱（通常每轮不到 1 美分），而是因为**可见的成本让人对 Agent 的行为有直觉**。你不知道它"想了"多少，但你知道它花了多少钱。

## 交互设计

MiniAgent 是一个终端程序，交互设计遵循了一个原则：**LLM 的思考过程是可见的，工具调用和输出也是可见的**。

```
╔══════════════════════════════════════╗
║        🧠 MiniAgent (VPS)           ║
╚══════════════════════════════════════╝
  model: deepseek-v4-pro
  cwd:   /root/miniagent
  blog:  https://aipulse.lol

  /clear /system /tokens /cost | q to quit

你 › 帮我把 nginx 日志里访问量最高的 10 个 IP 找出来

  我会查看 nginx 访问日志，找出访问量最高的 10 个 IP。

  🔧 bash cat /var/log/nginx/access.log | awk '{print $1}' | sort...
  → 192.168.1.1 - 3421 requests
    10.0.0.5 - 2103 requests
    ...

访问量最高的 10 个 IP 如上。192.168.1.1 占了 3421 次请求，远超其他 IP。
```

颜色编码帮助区分不同信息层级：青色是 LLM 文本、黄色是工具调用、灰色是工具输出和元数据。

## 为什么是 450 行

不是刻意精简。写完发现，把一个 ReAct Agent 的核心逻辑写清楚，确实只需要这么点代码。LangChain 的 `create_react_agent` 底层也是类似的逻辑，但包装了太多抽象层。

MiniAgent 没有：
- 类继承体系
- 插件系统
- 配置文件解析
- 异步 I/O
- 日志框架
- 依赖注入

它只有：
- 一个 `while True` 循环
- 一个字典映射工具名到函数
- `input()` 读取用户输入
- `print()` 输出结果

**这不是简陋，而是聚焦。** 当代码足够少，bug 就足够少，修改就足够快。

## 实际使用场景

MiniAgent 每天帮我做这些事：

- **写博客**：提供主题 → 搜索资料 → 生成文章 → 发布上线（全程在 Agent 内完成）
- **服务器运维**：查日志、分析流量、检查磁盘、更新配置
- **代码探索**：在 VPS 上的项目里搜索、阅读、修改文件
- **快速调研**：搜网页 → 抓取关键页面 → 总结

它不是 ChatGPT 的替代品（ChatGPT 的对话体验更好），但它能**做事**。ChatGPT 告诉你"可以这样改 nginx 配置"，MiniAgent 直接帮你改好。

## 设计取舍与遗憾

### 刻意不做的

- **多 Agent 编排**：一个 Agent 够用，两个增加复杂度而收益不明确
- **向量数据库 / RAG**：VPS 上没有大量本地文档需要检索
- **Web UI**：终端就够了，SSH 上去就能用
- **会话持久化**：重启即失，但历史记录不重要（任务本身已产生文件变更）

### 已知不足

- **工具结果截断**：超过 200 字符的输出在终端只显示前 200 字符（但完整内容会传给 LLM）
- **单线程**：不支持并行工具调用（Anthropic API 其实支持，但 MiniAgent 没实现）
- **错误恢复弱**：工具报错后 LLM 可能放弃而不是重试

## 快速开始

```bash
# 1. 安装依赖
pip install anthropic duckduckgo_search

# 2. 设置 API key
export ANTHROPIC_API_KEY="sk-ant-..."
# 可选：切换模型或 API 端点
export ANTHROPIC_MODEL="claude-sonnet-4-6"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"

# 3. 运行
python agent.py
```

想添加自己的工具？在 `TOOLS` 列表里加定义，在 `TOOL_HANDLERS` 字典里加处理函数。三步搞定。

## 总结

MiniAgent 是一个"刚好够用"的 VPS Agent。它证明了：

1. **ReAct 循环不需要框架**：一个 while 循环 + 工具字典就够了
2. **可见性比花哨功能重要**：能看到 Agent 在做什么、花了多少钱，比黑箱自动化更有价值
3. **单文件是美德**：部署 = scp + python，没有任何其他依赖
4. **Agent 可以住在服务器上**：不需要复杂的 CI/CD，不需要 webhook，Agent 直接操作文件系统

代码在 VPS 的 `/root/miniagent/agent.py`，总共不到 450 行。如果你有类似需求，欢迎参考和修改。

---

*这篇博客由 MiniAgent 自己写代码搜索资料、组织内容、并通过 `publish_post` 工具直接部署上线。它讲自己的故事。*
