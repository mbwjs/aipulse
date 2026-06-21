---
title: "AI 学习路线图：从会用 Agent 到理解底层原理"
slug: "ai-learning-path"
date: 2026-06-22
description: "一份面向工程师的 AI 学习路径，四层递进：学会用 → 理解原理 → 动手做 → 追踪前沿。含具体资源和实践项目。"
aliases:
  - /posts/ai-learning-path.html
featured: true
---

## 先说结论

如果你是有编程经验的工程师，**不要从数学开始**。那条路适合做研究的人。

工程师学 AI 的正确顺序是：**先用爽 → 再理解 → 再动手 → 再追前沿**。

## 第一层：学会用（第 1-2 周）

这层你已经在了。用 Claude、ChatGPT、Cursor 日常写代码、查文档、debug。

但要更进一步——**从"聊天"到"工程化使用"**。

### 学什么

- **Prompt 结构化**：不是 "帮我写个函数"，而是给角色、给约束、给输出格式
- **System Prompt**：理解 system / user / assistant 三种消息的区别
- **Few-shot prompting**：给 2-3 个例子，效果远超零样本
- **Chain-of-Thought**：让模型 "一步步思考"，复杂推理任务的关键技巧

### 实践

```
任务：用 Claude 的 system prompt 写一个"代码审查员"角色，
要求它审查你的代码时只关注安全漏洞和性能问题，忽略风格问题。
```

### 资源

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — 目前最好的提示工程文档
- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering) — 互补视角

## 第二层：理解原理（第 3-6 周）

不需要手推反向传播，但要搞清楚：

### 2.1 Transformer 怎么工作的

注意力机制是当代 AI 的基石。推荐两个资源：

| 资源 | 类型 | 时间 |
|------|------|------|
| [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) | 图文教程 | 30 min |
| Karpathy [Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY) | 视频（写代码） | 2h |

Karpathy 这个视频**必看**。他带着你从零写一个 GPT，过程中你会理解 tokenization、embedding、self-attention、multi-head attention、生成过程。不需要 GPU，纯 Python 就能跑。

### 2.2 Token 和 Embedding

- **Token**：LLM 看到的不是文字，是数字序列。理解 tokenization 才能理解为什么中文比英文"贵"。
- **Embedding**：把文字映射到高维向量空间，语义相近的词向量也相近。

玩玩 [OpenAI Tokenizer](https://platform.openai.com/tokenizer)，看看同一段话在不同模型下被切成多少 token。

### 2.3 LLM 的训练过程

简化版流程（非研究者够用了）：

```
预训练（海量文本预测下一个 token）
    → SFT（人工标注数据微调，学会遵循指令）
        → RLHF（人类反馈强化学习，对齐价值观）
```

### 2.4 RAG（检索增强生成）

让 LLM 回答它不知道的东西：先检索相关文档，再把文档拼进 prompt 让模型回答。这是目前企业级 LLM 应用最常见的架构。

动手：用 LangChain 或 LlamaIndex 搭一个能回答你代码仓库问题的 RAG。

## 第三层：动手做（第 7-12 周）

这一层是你和纯"用户"拉开差距的地方。

### 3.1 从 Agent 循环开始

一个 AI Agent 的本质是什么？核心循环不超过 50 行代码：

```python
system_prompt = "你是一个编程助手..."
messages = [{"role": "system", "content": system_prompt}]

while True:
    response = llm.chat(messages, tools=[read_file, write_file, run_test])
    
    if response.is_final:
        break  # 任务完成
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call)
            messages.append({"role": "tool", "content": result})
    else:
        messages.append({"role": "user", "content": "继续"})
```

理解了这个循环，你就理解了 GPT-4 到 Devin 的跨度：**不是模型变强了，是循环让它能做事**。

### 3.2 选一个框架

| 框架 | 语言 | 适合 |
|------|------|------|
| [LangChain](https://www.langchain.com/) | Python/JS | 生态最大，组件多 |
| [LlamaIndex](https://www.llamaindex.ai/) | Python | RAG 和数据 pipeline 强 |
| [Vercel AI SDK](https://sdk.vercel.ai/) | TS | 前端/全栈 AI 应用 |
| [trpc-agent-go](https://github.com/trpc-group/trpc-agent-go) | Go | 后端 Agent 系统 |

### 3.3 做一个完整的项目

- **RAG 文档问答**：喂入技术文档，用自然语言提问
- **AI Code Review Bot**：GitHub webhook + LLM，自动 review PR
- **个人知识库**：把自己的笔记向量化，随时检索和对话

## 第四层：追踪前沿（持续）

### 4.1 信息源

| 渠道 | 内容 |
|------|------|
| [Anthropic Research](https://www.anthropic.com/research) | Claude 系列技术报告 |
| [OpenAI Research](https://openai.com/research) | GPT 系列技术报告 |
| [Hugging Face Daily Papers](https://huggingface.co/papers) | 每日精选论文 |
| [arXiv cs.CL](https://arxiv.org/list/cs.CL/recent) | NLP/LLM 新论文 |
| [Simon Willison's Blog](https://simonwillison.net/) | LLM 工程实践 |
| [Lilian Weng's Blog](https://lilianweng.github.io/) | OpenAI 研究员的技术博客 |

### 4.2 X 上关注

- `@karpathy` — Andrej Karpathy，AI 教育家
- `@simonw` — Simon Willison，LLM 工具作者
- `@hwchase17` — Harrison Chase，LangChain 创始人

### 4.3 怎么读论文

1. 不要逐字读，**先读 abstract → conclusion → figures**
2. 重点看：他们解决了什么问题？方法是什么 trick？比之前好多少？
3. 用 Claude/NotebookLM 帮你总结（贴 PDF，让它归纳要点）

## 推荐的时间分配

| 阶段 | 时间 | 核心动作 |
|------|------|---------|
| 会用 | 1-2 周 | 把 AI 工具用到日常中，学 prompt engineering |
| 理解 | 1-2 月 | 看 Transformer 教程，理解 token/embedding/RAG |
| 动手 | 1-3 月 | 抄 Agent 循环，搭一个 RAG，选框架做项目 |
| 追前沿 | 持续 | 每天扫一眼 Hugging Face Papers，每周精读 1 篇 |

## 不要做的事

- ❌ 一上来就啃《深度学习》（花书）——你会放弃
- ❌ 追着每个新模型跑 —— 原理都一样
- ❌ 纠结 "学 PyTorch 还是 TensorFlow" —— 写 Agent 用 API 就够了
- ❌ 试图 "学完再动手" —— 永远学不完，做了才算

## 一个最小可行的开始

今晚花 2 小时：

1. 打开 [Karpathy 的 GPT 从零实现](https://www.youtube.com/watch?v=kCc8FmEb1nY)，跟着写代码
2. 写完后用 300 字总结你学到了什么
3. 发到博客上

这就比 90% 说 "我想学 AI" 的人走得远了。

---

*本文会持续更新。如果你也在学 AI，欢迎通过 [GitHub Issues](https://github.com/mbwjs/mbwjs/issues) 交流你的学习路径。*
