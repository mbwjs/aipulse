# AI Pulse — AI Agent 驱动的知识商店平台

> 说一句话 → AI 自动生成知识付费网站 → 一键部署上线

## 这是什么

一个 AI Agent 项目。输入主题（如"Java 面试题库"），Agent 自动：

- 生成结构化知识内容（章节 + 面试题 + 练习题 + 答案解析）
- 搭建 Hugo 静态网站（含付费墙）
- 一键部署到 Vercel / Netlify / GitHub Pages（全免费）

**买家什么代码都不用写，注册个 Vercel 账号就行。**

## 产品页

👉 **[aipulse.lol/product/](https://aipulse.lol/product/)**

## 技术栈

| 层 | 技术 |
|------|------|
| AI Agent | Python 3 + DeepSeek API（JSON mode） |
| Prompt 系统 | Strategy YAML 配置 + Structured Output |
| 静态站点 | Hugo 0.163 (Go) |
| 部署 | Vercel / Netlify / GitHub Pages |
| 博客前端 | HTML + CSS（暗色模式 + 响应式） |
| 安全 | fail2ban + SSH 密钥 + Let's Encrypt |

## 项目文档

| 文档 | 内容 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构图 + 技术决策 |
| [INTERVIEW.md](INTERVIEW.md) | 面试高频 Q&A（防问倒） |

## 快速开始

```bash
git clone git@github.com:mbwjs/aipulse.git
cd aipulse
cp deploy.example.sh deploy.sh   # 编辑部署目标
git config core.hooksPath .githooks   # 启用密钥扫描 hook
```

### 写博客

```bash
hugo new posts/my-post.md
hugo server -D   # 预览
./deploy.sh      # 发布
```

### 生成知识商店

```bash
# 需要 DEEPSEEK_API_KEY 环境变量
python3 scripts/knowledge-shop/agent.py "Java 面试题库" --chapters 5
# 输出: /tmp/knowledge-mvp/java面试题库/
# 把 public/ 拖到 netlify.com 即可上线
```

### 生成博客文章

```bash
python3 scripts/generate.py "MCP 协议深度解析" --deploy
# 自动保存为 Hugo post + 部署上线
```

## 目录结构

```
aipulse/
├── content/                  # 博客文章（Markdown）
│   ├── posts/                # 技术文章
│   ├── product/              # 产品落地页
│   └── strategies/           # 策略市场
├── layouts/                  # Hugo 模板
├── static/                   # CSS / JS
├── scripts/
│   ├── generate.py           # 博客文章生成 Agent
│   ├── strategy.yaml         # 策略配置
│   └── knowledge-shop/
│       └── agent.py           # 知识商店生成 Agent（389 行）
├── .githooks/                # pre-commit 密钥扫描
├── .github/workflows/        # GitHub Pages 自动部署
├── ARCHITECTURE.md           # 架构文档
├── INTERVIEW.md              # 面试说辞
└── hugo.yaml                 # Hugo 配置
```
