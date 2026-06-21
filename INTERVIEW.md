# 面试说辞：如何把这个项目讲给面试官

> 以下 Q&A 覆盖了面试中可能被问到的所有角度。
> 会问的不会超过这些。

---

## 一句话介绍

> "我做了一个 AI Agent 驱动的知识商店平台。用户说一句话——比如'Java 面试题库'——Agent 在 3 分钟内自动生成一套完整的知识付费网站，包含章节内容、面试题、练习题和付费墙，一键部署上线。"

---

## 高频问题

### Q1：这个项目解决了什么问题？

传统知识付费有三个痛点：
1. **内容生产慢**：一个人写一套 Java 面试题库要两周
2. **技术门槛高**：搭网站要会前端、后端、部署
3. **分发渠道窄**：个人很难把自己的知识产品挂到市场上

我用 AI Agent 把这三步全自动化了。内容生成 → 网站搭建 → 上线部署，3 分钟全搞定。

### Q2：你怎么保证 AI 生成的内容质量？

三个层次：
- **Prompt 工程**：策略层定义了严格的输出格式和内容标准（system prompt + JSON Schema）
- **人工审核**：生成的是"初稿"，买家可以逐章修改润色
- **数据飞轮**：用户刷题的数据会反哺 Agent，越用越准（规划中）

### Q3：架构是什么样的？

```
用户输入 → Strategy Layer（Prompt 模板）
         → LLM Adapter（DeepSeek API，JSON mode）
         → Content Builder（Python 解析 JSON → Hugo Markdown）
         → Deploy Packer（自动生成 Vercel/Netlify 配置）
         → 一键部署到静态托管平台
```

核心设计：**纯静态 + 零运维**。不需要数据库、不需要服务器、不需要后端。

### Q4：为什么选 Hugo 而不是 Next.js？

- Hugo 构建 <50ms，Next.js 要 30 秒
- 纯静态 HTML，可以部署到任何平台（Vercel、Netlify、GitHub Pages）
- 买家不需要安装 Node.js 或任何运行时

### Q5：策略市场是什么意思？

不只卖内容，卖的是"内容生产策略"。买家买了策略可以：
1. 用自己的 API key 无限生成内容
2. 修改 prompt 优化产出
3. 把改进后的策略重新上架，卖出去拿分成

本质是 **Agent 基因市场**——好的策略会被复制和进化。

### Q6：你是怎么调用 AI 的？

用 DeepSeek API 的 Chat Completions 接口，开启了 JSON mode（`response_format: {type: "json_object"}`），确保输出是可解析的结构化数据。核心代码不到 50 行。

```python
def call_deepseek(system_prompt, user_prompt):
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }
    # ... HTTP 调用 + 解析
```

### Q7：如果 AI 生成的内容跟别人的一样怎么办？

不会。因为每个用户输入的 topic 不同、章节数不同、风格参数不同，加上 LLM 的 temperature 保证了随机性。两个用户输入同样的"Java 面试"，生成的内容也不一样。

### Q8：这个项目技术上有什么难点？

1. **结构化输出约束**：让 LLM 输出严格符合 JSON Schema 的内容（章节、题型的嵌套结构）
2. **Markdown + HTML 混合渲染**：Hugo 默认不渲染行内 HTML（练习题折叠答案），需要配置 Goldmark renderer unsafe
3. **零依赖部署**：买家不需要装任何东西，Vercel 一个按钮就上线
4. **多平台适配**：同一套代码兼容 Vercel、Netlify、GitHub Pages 三种部署方式

### Q9：你怎么赚钱？

三层收入：
1. **一次性卖 Agent**（¥99）
2. **买家站点的付费墙抽成**（30%）
3. **策略市场版税**（买家转卖时自动分账）

### Q10：能讲讲 Prompt 工程在这项目里的作用吗？

整个 Agent 的核心不是代码，是 prompt。300 行 Python 里只有 50 行是 API 调用，剩下全是 prompt 模板和输出处理。

关键设计：
- System prompt 定义 AI 的"人设"（知识付费内容专家）
- User prompt 注入用户参数（topic、chapters、category）
- JSON Schema 约束输出结构（章节数组、题目类型枚举）
- 输出后处理（清理 markdown code block 标记、格式校验）

---

## 技术关键词（往简历上写的）

```
AI Agent · LLM · Prompt Engineering · Structured Output
Python · Hugo · Static Site Generation · Vercel · Netlify
DeepSeek API · JSON Schema · Knowledge Marketplace
Agent Marketplace · Multi-Agent Architecture
```

## 如果面试官追问"你做了什么 vs AI 做了什么"

> "这整个项目的架构设计、策略系统、Hugo 模板、部署管线、Prompt 工程是我做的。
> AI 负责的是内容生成那一层：给它主题和策略，它产出结构化知识数据。
> 我不是在调用一个黑盒 API，我是设计了一套 Agent 系统，让 AI 成为生产线上的一个环节。"
