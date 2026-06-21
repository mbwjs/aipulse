---
title: "Loop Engineering：AI Agent 时代的控制流设计"
slug: "loop-engineering"
date: 2026-06-21
description: "从 loop-until-dry 到 budget-aware 自适应循环，探索 AI Agent 编排中的核心工程模式。"
aliases:
  - /posts/loop-engineering.html
  - /posts/loop-engineering
featured: true
---

> **TL;DR** — 当 AI Agent 不再是"一问一答"的推理函数，而是持续运行的自主实体，控制流设计就从软件工程的边角料变成了核心命题。Loop Engineering 是关于如何在 AI Agent 系统中设计、组合和调度循环的一套工程模式。本文梳理了 loop-until-dry、budget-aware loop、pipeline scheduling 等核心模式，以及它们在实际系统（如 Claude Code）中的应用。

## 1. 为什么需要 Loop Engineering？

传统的 LLM 调用是一次性的：用户输入 prompt，模型返回结果，对话结束。但在 AI Agent 系统中，模型不再是回答一个问题就退出的函数，而是一个持续运行的**自主实体**。它需要反复调用工具、评估结果、调整策略，直到任务完成——或者预算耗尽。

这带来了一个根本性的架构挑战：**如何设计控制流，让 Agent 在不确定的环境中高效、可靠地运行？**

具体来说，Agent 循环面临三类核心问题：

- **终止条件**：Agent 什么时候应该停下来？怎么判断任务是否真的完成了，而不是卡在死循环里？
- **资源约束**：每次循环都消耗 tokens（也就是钱和时间），如何在预算内最大化产出？
- **并行调度**：多个 Agent 或子任务如何编排？什么时候该等，什么时候该流水线？

**Loop Engineering** 就是回答这些问题的工程实践。它的核心不是某一种具体算法，而是一套**可组合的控制流原语**。

## 2. 核心模式

### 2.1 Loop-Until-Dry：穷尽式发现

最常见的一个场景：你需要 Agent 找到代码库中"所有的 bug"。但 bug 的数量是未知的——你不知道该让 Agent 跑多少轮。固定轮次太少（漏报）或太多（浪费）。

**Loop-until-dry** 是答案：不断启动新的发现轮次，直到连续 K 轮没有新发现为止。

```js
const seen = new Set()
let dry = 0

while (dry < CONVERGENCE_THRESHOLD) {
  const findings = await agent("Find bugs in the codebase.")
  const fresh = findings.filter(b => !seen.has(key(b)))

  if (fresh.length === 0) {
    dry++
    continue
  }

  dry = 0
  fresh.forEach(b => seen.add(key(b)))
  await verify(fresh)  // 验证新发现
}
```

这个模式的关键细节：

- **去重基准是 `seen`，不是 `confirmed`**。如果只对已确认的 bug 去重，被驳回的发现会每轮重复出现，永远不收敛。
- **收敛阈值**（K）需要根据任务噪声水平调整。代码审计通常设 K=2 或 3，高噪声任务可能需要更大。
- Agent 的**多样性**（不同 prompt、不同角度）往往是打破平台期的关键。

### 2.2 Budget-Aware Loop：在约束内最大化产出

现实系统中，Agent 从来不是免费运行的。每次循环消耗 tokens，每轮工具调用都有延迟。当用户说"用 50 万 tokens 审计这个项目"时，系统需要把预算当作一等公民来设计控制流。

```js
while (budget.remaining() > RESERVE_FOR_FINAL_SYNTHESIS) {
  const batch = await agent("Audit the next batch of files.")
  findings.push(...batch)

  log(`${findings.length} issues found, ${budget.remaining()} tokens left`)
}

// 预算用尽前的最后一步：总结所有发现
const report = await agent(
  `Synthesize a report from ${findings.length} findings.`
)
```

Budget-aware loop 的设计原则：

1. **预留空间给最终合成**：不要把钱花光才发现没 tokens 写报告。
2. **动态调整每轮粒度**：预算充足时 deep-dive，预算紧张时 breadth-first 扫描。
3. **可恢复性**：每轮的结果应该可持久化，预算耗尽后可以从断点继续。

### 2.3 Pipeline：流水线式扇出

当任务可以分解为多个阶段（发现 → 验证 → 修复），最简单的做法是用 barrier 同步每个阶段。但 barrier 意味着等待——慢任务拖累整体吞吐。

**Pipeline 模式**的核心洞察：**Item A 可以在阶段 3（修复）的同时，Item B 还在阶段 1（发现）。不需要等所有发现完成才开始验证。**

```js
pipeline(
  items,
  item => agent("Stage 1: Analyze", {input: item}),
  result => agent("Stage 2: Verify", {input: result}),
  verified => agent("Stage 3: Fix", {input: verified})
)
```

Pipeline 的 wall-clock 时间是**单条最长链路**，而非所有阶段之和。这在多 Agent 场景下带来显著的延迟改善。

什么时候该用 barrier？**只有当阶段 N 真的需要阶段 N-1 的全局上下文时。**比如"去重所有发现"——这确实需要看到所有结果。但"验证单个发现"不需要知道其他发现的内容，用 pipeline 即可。

### 2.4 Adversarial Verification：对抗性验证

LLM 很擅长制造看起来合理但实际上错误的内容。在 Agent 循环中，这意味着每一步的输出都可能包含幻觉。

**对抗性验证**为每个发现启动 N 个独立的"质疑者"，每个都以**反驳**为目标来审视结果。只有被多数质疑者接受的发现才能存活。

```js
const judges = await parallel(
  finding => agent(`Try to REFUTE: "${finding.claim}".
    Default to refuted=true if unsure.`)
)

const survives = judges.filter(j => !j.refuted).length >= MAJORITY
```

为什么这比简单的"再问一次"更有效？因为对抗性 prompt 打破了模型的 confirmation bias。要求模型"反驳"而不是"确认"，迫使它调用不同的推理路径。

### 2.5 Perspective-Diverse Verification：多视角验证

对抗性验证的升级版：不让所有验证者问同一个问题，而是给每个人**不同的审视角度**。

```js
const lenses = ['correctness', 'security', 'performance', 'reproducibility']
const reviews = await parallel(
  lenses.map(lens => agent(
    `Review "${finding.desc}" through the ${lens} lens.`
  ))
)
```

一个代码变更可能"逻辑正确"但"不安全"，或者"安全"但"不可复现"。单维度验证会漏掉多维度的问题。多样化视角捕捉了冗余验证无法触及的失败模式。

## 3. 实际系统中的应用

这些模式并非纯理论。以下是来自真实 AI Agent 系统的实践：

- **Claude Code / Workflow 引擎**：内置了 pipeline、parallel、loop-until-dry 等原语。其 workflow DSL 让开发者声明式地编排多 Agent 流程，引擎自动处理调度和错误恢复。
- **SWE-Agent / Devin**：使用循环结构来迭代式地探索代码库、生成补丁、运行测试、根据测试结果修正——本质上是 loop-until-pass。
- **AutoGPT 类系统**：使用"计划-执行-评估"循环，loop-until-objective-complete，但缺乏严格的终止条件设计导致常见的 runaway 问题。

## 4. 常见陷阱与最佳实践

### 4.1 陷阱一：没有收敛条件

最常见的 Agent 失败模式就是无限循环。永远为每个循环设定**显式的终止条件**：最大轮次、收敛阈值、预算上限——至少有一个，最好三个都有。

### 4.2 陷阱二：Barrier 过度使用

出于直觉，很多人会这样写："先让所有 Agent 分析，收集结果，再让所有 Agent 修复"。但中间的收集步骤是一个 barrier——它让快 Agent 干等着慢 Agent。默认用 pipeline，只在确实需要全局上下文时才用 barrier。

### 4.3 陷阱三：静默截断

当系统因为预算或时间限制而跳过某些检查时，**必须显式记录**。静默的 "top-N" 截断会让用户以为"全部检查完成"，而实际上大部分内容根本没被看。可信的系统要对用户诚实：检查了什么，没检查什么。

### 4.4 最佳实践总结

- **组合，而非嵌套**：loop → pipeline → verify 比在一个巨大循环里手写所有逻辑更可维护。
- **可观测性优先**：每个循环的迭代计数、预算消耗、发现数量都应该可监控。
- **优雅降级**：预算耗尽时返回部分结果 + 状态（可恢复），而不是崩溃。
- **去重是基础设施**：跨轮次去重应该是系统级的，不是每个 Agent 自己实现的。

## 5. 展望

Loop Engineering 还处于早期阶段。随着 Agent 系统的规模化部署，几个方向值得关注：

- **自适应循环策略**：让循环参数（轮次大小、并发度、验证强度）根据实时反馈动态调整，而非硬编码。
- **分层循环**：外层循环做战略规划，内层循环做战术执行，模拟人类"思考-行动"的认知层次。
- **循环安全**：在 Agent 自主运行数小时甚至数天的场景下，如何保证循环不会因为幻觉累积而漂移？
- **跨 Agent 循环**：当循环跨越多个不同的 Agent（而非同一 Agent 的多轮调用），状态传递和错误恢复如何设计？

最终，Loop Engineering 的目标和所有软件工程一样：**在不确定性中建立确定性**。当你无法预测 Agent 下一步会做什么，但你至少可以确保无论它做什么，系统都能收敛、不超预算、产出可验证的结果。

---

*本文是 AI Pulse "AI Engineering" 系列的第一篇。下一篇将探讨 Multi-Agent 编排中的通信协议设计。*
