# AI Pulse

⚡ AI 技术追踪博客 — 深度技术文章，聚焦 AI Agent、LLM 工程实践与前沿架构。

**站点：** [https://aipulse.lol](https://aipulse.lol)

## 技术栈

- **静态生成**：Hugo 0.163
- **服务器**：AlmaLinux 9.7 + Nginx
- **HTTPS**：Let's Encrypt 自动续期
- **分析**：Google Search Console

## 目录结构

```
aipulse-hugo/
├── content/          # Markdown 文章
│   ├── _index.md     # 首页
│   └── posts/        # 文章目录
├── layouts/          # Hugo 模板
│   ├── _default/     # 通用模板（列表、单页）
│   ├── partials/     # 头部、底部
│   └── 404.html      # 404 页面
├── static/css/       # 样式
├── hugo.yaml         # Hugo 配置
└── deploy.sh         # 部署脚本
```

## 写作流程

```bash
# 1. 新建文章
hugo new posts/my-post.md

# 2. 编辑 content/posts/my-post.md

# 3. 本地预览
hugo server -D

# 4. 发布
./deploy.sh
```

## 部署

`deploy.sh` 自动构建并通过 rsync 推送到 `104.194.92.198:/var/www/aitracker/`。
