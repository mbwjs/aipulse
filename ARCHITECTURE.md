# AI Pulse 系统架构

## 概述

AI Pulse 是一个 **AI Agent 驱动的知识商店平台**。核心能力：

1. 接收一个主题（如"Java 面试题库"）
2. AI Agent 自动生成结构化知识内容（章节 + 面试题 + 练习题）
3. 自动构建 Hugo 静态网站（含付费墙）
4. 一键部署到 Vercel / Netlify / GitHub Pages

## 架构图

```
用户输入（"Java 面试题库"）
       │
       ▼
┌─────────────────────────────┐
│   Knowledge Shop Agent      │  ← Python 脚本
│   scripts/knowledge-shop/   │
│                             │
│  ┌───────────────────────┐  │
│  │ Strategy Layer        │  │  ← Prompt 模板 + 输出格式约束
│  │ (strategy.yaml)       │  │
│  └──────────┬────────────┘  │
│             ▼               │
│  ┌───────────────────────┐  │
│  │ LLM Adapter           │  │  ← DeepSeek API（可换 OpenAI/Claude）
│  │ (call_deepseek)       │  │
│  └──────────┬────────────┘  │
│             ▼               │
│  ┌───────────────────────┐  │
│  │ Content Builder       │  │  ← JSON → Markdown + Hugo 模板
│  │ (build_hugo_site)     │  │
│  └──────────┬────────────┘  │
│             ▼               │
│  ┌───────────────────────┐  │
│  │ Deploy Packer         │  │  ← README + Vercel/Netlify 配置
│  │ (make_readme)         │  │
│  └───────────────────────┘  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   输出的 Hugo 站点           │
│                             │
│  ├── content/  ← 知识内容    │
│  ├── layouts/  ← 极简主题    │
│  ├── vercel.json             │
│  ├── netlify.toml            │
│  └── .github/workflows/     │
└─────────────┬───────────────┘
              │
              ▼
    ┌─────────────────┐
    │ 一键部署          │
    ├─────────────────┤
    │ Vercel    (免费) │
    │ Netlify   (免费) │
    │ GitHub Pages(免费)│
    └─────────────────┘
              │
              ▼
        🌐 知识付费站点上线
```

## 技术栈

| 层 | 技术 | 选型理由 |
|------|------|------|
| AI Agent | Python 3 + DeepSeek API | DeepSeek 性价比最高，支持 JSON mode |
| 内容生成 | Prompt Engineering + Structured Output | JSON Schema 约束确保输出可解析 |
| 静态站点 | Hugo (Go) | 构建速度 <50ms，零依赖 |
| 部署 | Vercel / Netlify / GitHub Pages | 免费 CDN + HTTPS + 自动构建 |
| 付费墙 | 前端占位（MVP），后续集成 Stripe | 渐进式交付 |

## 策略系统

```
strategy.yaml
├── tech-deep-dive      → 2000 字技术长文
├── quick-insight       → 400 字快评
└── knowledge-shop      → 知识付费内容（章节+题库）
```

每个策略定义了：
- `system_prompt`：AI 的角色和写作风格
- `user_prompt_template`：输入模板（`{topic}` 替换为用户输入）
- 输出格式约束（JSON Schema / Markdown）

## 数据流

1. 用户输入主题和参数 → Agent 拼装 prompt
2. LLM 返回结构化 JSON（章节、知识点、面试题、练习题）
3. Python 解析 JSON → 生成 Hugo Markdown 文件
4. Hugo 构建 → 纯静态 HTML/CSS
5. 用户一键部署到任意静态托管平台

## 关键设计决策

### 为什么不用数据库？

纯静态站点 = 零运维、零成本、永不崩溃。知识内容以 Markdown 文件存储，Git 版本管理。

### 为什么选 Hugo 而不是 Next.js？

- Hugo 构建 <50ms（Next.js 需 30s+）
- 零 Node.js 依赖，买家不需要装任何东西
- 静态 HTML 可部署到任何平台

### 为什么付费墙是前端占位？

MVP 阶段先验证"有人愿意为 AI 生成的知识付费"，再投入真实支付集成。过早做支付 = 过度工程。

## 扩展方向

- [ ] Stripe/支付宝真实支付
- [ ] 策略市场（Agent → NFT → 自动交易）
- [ ] 用户内容贡献反哺 Agent（面经数据增强）
- [ ] Agent 自主运营（自动日更新内容）
- [ ] 多 Agent 协作（出题 Agent + 审核 Agent + 排版 Agent）
