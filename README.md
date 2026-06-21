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
├── hugo.yaml             # Hugo 配置
├── deploy.example.sh     # 部署脚本模板
└── deploy.sh             # 你的部署脚本（不入库）
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

1. 复制模板：`cp deploy.example.sh deploy.sh`
2. 修改 `deploy.sh` 里的 `DEPLOY_TARGET` 为你自己的服务器地址
3. `chmod +x deploy.sh && ./deploy.sh`

脚本通过 Hugo 构建 + rsync 推送到服务器。`deploy.sh` 已加入 `.gitignore`，不会入库。
