# AI 知识工厂 — 开发计划

> 上一次更新：2026-06-22

## 产品定位

AI 原生知识生产引擎 + 交易市场。品类不限（面试题、考证、技能培训……），AI 帮生产者把资料变成知识产品，消费者付费解锁，平台抽成。

## 已有资产

| 模块 | 状态 | 说明 |
|------|------|------|
| `scripts/generate.py` | ✅ | 博客文章生成 Agent |
| `scripts/strategy.yaml` | ✅ | 策略配置（风格模板） |
| `scripts/knowledge-shop/agent.py` | ✅ | 知识商店搭建 Agent（389 行） |
| `scripts/knowledge-shop/quiz-agent.py` | ✅ | 题库生成 Agent（文件+URL 输入） |
| Hugo 博客 + 产品页 | ✅ | aipulse.lol（已加登录保护） |
| GitHub Pages | ✅ | mbwjs.github.io/aipulse（公开） |
| 安全 | ✅ | fail2ban + SSH 密钥 + Let's Encrypt |
| 仓库 | ✅ | GitHub 私有仓库 |

## 明日计划

### 第一优先级：Web 化 Agent

> 目标：用户在浏览器里填主题 + 上传文件 → 点生成 → 拿到题库

| 任务 | 说明 | 预计 |
|------|------|------|
| FastAPI 后端 | Python，复用 `quiz-agent.py` 的核心逻辑 | 1h |
| 题库生成 API | `POST /api/quiz/generate` 接受 topic + file | 30min |
| 题库列表 API | `GET /api/quizzes` 返回已生成的题库 | 30min |
| 简单前端页面 | Hugo 静态页 + 一个动态表单（fetch API） | 1h |

### 第二优先级：登录 + 限流

| 任务 | 说明 | 预计 |
|------|------|------|
| GitHub OAuth | 最快，你已有 GitHub 账号体系 | 30min |
| JWT session | 登录后发 token，前端存 localStorage | 30min |
| 免费额度 | 未登录 1 次预览，登录 3 次/月 | 30min |
| 额度检查中间件 | FastAPI middleware，读数据库计数 | 30min |

### 第三优先级：付费

| 任务 | 说明 | 预计 |
|------|------|------|
| Stripe Checkout | 创建 ¥29/月 订阅 | 1h |
| Webhook | 付款成功 → 升级用户额度 | 30min |
| 会员标记 | 前端显示"免费版"/"会员" | 20min |

## 定价设计

```
免费层：
  → 每月 3 次生成
  → 每套最多 20 题
  → 不能上架卖

会员 ¥29/月：
  → 每月 50 次生成
  → 每套最多 100 题
  → 资料上传 + 联网搜索
  → 可上架售卖
  → 卖题收入 70% 归卖家

专业版 ¥99/月：
  → 无限生成
  → PDF/Word 批量导入
  → 自定义题目模板
  → 销售数据面板
```

## 技术栈确定

| 层 | 选型 | 理由 |
|------|------|------|
| 后端 | FastAPI (Python) | 和 Agent 同语言，零切换成本 |
| 数据库 | SQLite | 先不要 PostgreSQL，单文件搞定 |
| 前端 | Hugo + Alpine.js | 复用现有博客，轻量动态增强 |
| 支付 | Stripe | 支持支付宝 |
| 登录 | GitHub OAuth | 你已有 GitHub，10 行接入 |
| 部署 | 同一台 VPS + nginx 反代 |

## 不做的事（明确砍掉）

- ❌ 不做买家自己部署代码（改为平台内使用）
- ❌ 不做 NFT / 链上（MVP 阶段不需要）
- ❌ 不做社会化功能（评论、关注，v2 再考虑）
- ❌ 不做 AI 模拟面试（先卖题库，再加其他形态）

## 目录结构（明天搭完后的样子）

```
aipulse-hugo/
├── app/                    # FastAPI 后端
│   ├── main.py             # 入口
│   ├── auth.py             # GitHub OAuth
│   ├── quiz.py             # 题库 API
│   ├── models.py           # SQLite 模型
│   └── middleware.py       # 限流/鉴权
├── scripts/                # Agent 脚本（复用）
├── content/                # Hugo 博客（不变）
├── static/                 # 前端静态文件
└── templates/              # Hugo 模板
```

## 成功标准

- [ ] 浏览器打开 aipulse.lol → 看到一个表单：主题 + 上传文件
- [ ] 输入"Java 面试" → 等待 30 秒 → 看到 20 道题
- [ ] 生成第 4 次时弹窗"本月免费额度已用完，升级会员 ¥29/月"
- [ ] GitHub 登录 → 生成成功
- [ ] 付费 → 额度刷新
