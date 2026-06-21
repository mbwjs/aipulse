---
title: "从零到上线：一台 VPS 搭建个人技术博客全记录"
slug: "from-zero-to-blog"
date: 2026-06-22
description: "用 AlmaLinux + Hugo + Nginx 在 $5/月的 VPS 上搭建一个带 HTTPS、自动部署、SEO 优化的技术博客。全过程记录，含安全加固和域名配置。"
aliases:
  - /posts/from-zero-to-blog.html
featured: true
---

## 缘起

我有一台闲置的 VPS（1 核 1G 内存，19G 硬盘），上面跑着 Hysteria2 代理。某天突发奇想——我能不能在这台机器上搭一个个人技术博客？

答案是能。而且做完之后发现整套流程踩了不少坑，值得记录。

## 起点：一台"看不见"的服务器

服务器上跑了什么？先 SSH 上去看看：

```
AlmaLinux 9.7（RHEL 9 兼容）
CPU: 2 vCPU AMD EPYC
内存: 1 GB（可用 750 MB）
磁盘: 19 GB（剩余 17 GB）
开放的 TCP 端口: 仅 22（SSH）
```

Hysteria2 只占用了 UDP 443，TCP 80 和 TCP 443 都是空闲的——足够跑一个 Web 服务了。

## 第一版：手写 HTML

装好 Nginx 后，我手写了三件事：

1. **一个响应式首页**：暗色模式自动切换、中文排版优化
2. **一篇技术文章**：《Loop Engineering：AI Agent 时代的控制流设计》
3. **CSS**：无外部依赖，CSS 变量驱动主题

这一版很快就上线了，`http://104.194.92.198/` 已经可以访问。但问题随之而来。

## 域名与 HTTPS

### 选域名

在 Porkbun 买了 `aipulse.lol`（¥40/年），A 记录指向服务器 IP。Porkbun 的 DNS 管理界面有点坑——添加 TXT 记录时 Host 留空而不是填 `@`。

### Let's Encrypt

```bash
dnf install -y epel-release certbot python3-certbot-nginx
certbot --nginx -d aipulse.lol -d www.aipulse.lol --non-interactive --agree-tos --email admin@aipulse.lol
```

Certbot 自动修改了 nginx 配置，加上 SSL 证书和 HTTP→HTTPS 重定向。但有一个坑：**certbot 会覆盖你之前写的安全头和限流配置**，后面还得补回来。

证书有效期 90 天，自动续期：

```bash
systemctl enable certbot-renew.timer
```

## 安全加固

裸奔的服务器太危险。实际上 `fail2ban` 刚装上就发现 `186.13.24.118` 在暴力破解我的 SSH。

### 做了什么

| 措施 | 配置 |
|------|------|
| **fail2ban** | SSH 10 分钟内失败 5 次封 1 小时 |
| **SSH 加固** | root 仅允许密钥登录，最多尝试 3 次，空闲 10 分钟断开 |
| **nginx 限流** | 每 IP 10 req/s，突发 20 |
| **安全响应头** | `X-Frame-Options: DENY`、`X-Content-Type-Options: nosniff`、`Referrer-Policy`、`Permissions-Policy` |
| **TLS** | 仅 TLS 1.2/1.3，现代加密套件 |

关键 nginx 配置片段：

```nginx
# 限流区域
limit_req_zone $binary_remote_addr zone=web:10m rate=10r/s;

server {
    # 限流
    limit_req zone=web burst=20 nodelay;

    # 安全响应头
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # 去除 .html 后缀
    if ($request_uri ~ ^/(.*)\.html$) {
        return 301 /$1;
    }

    # 自定义 404
    error_page 404 /404.html;

    location / {
        try_files $uri $uri/ $uri.html =404;
    }
}
```

SSH 配置：

```bash
PermitRootLogin prohibit-password   # 仅密钥
MaxAuthTries 3                      # 最多试 3 次
ClientAliveInterval 300             # 空闲 5 分钟发心跳
ClientAliveCountMax 2               # 2 次无响应即断开
```

## SEO：让 Google 找到你

### 页面级

- **Open Graph 标签**：分享到 Twitter/Discord 有预览卡片
- **JSON-LD 结构化数据**：Article 和 WebSite schema
- **Canonical URL**：防止重复索引
- **`robots.txt` + `sitemap.xml`**

### Google Search Console

流程：添加资源 → 选"网址前缀"（不是"网域"）→ HTML 文件验证（比 DNS TXT 快）→ 提交 sitemap。

> DNS TXT 验证在 Porkbun 上容易失败，HTML 文件验证只要把文件丢到 `/var/www/` 就行，秒过。

## 重构：从 HTML 到 Hugo

手写 HTML 在文章只有一篇时还行，但当你想：

- 发新文章时不用复制 HTML
- URL 自动生成 `/posts/slug/` 格式
- 自动生成 sitemap 和 RSS
- Markdown 写作

就该上静态站点生成器了。选了 Hugo（Go 实现，单二进制，极快）。

### 项目结构

```
aipulse-hugo/
├── content/
│   ├── _index.md                 # 首页
│   └── posts/
│       ├── loop-engineering.md   # 文章（Markdown）
│       └── from-zero-to-blog.md  # 本文
├── layouts/
│   ├── _default/
│   │   ├── baseof.html           # 基础 HTML 框架
│   │   ├── single.html           # 文章页模板
│   │   └── list.html             # 列表页模板
│   ├── partials/
│   │   ├── header.html
│   │   └── footer.html
│   └── 404.html
├── static/css/style.css
├── hugo.yaml                     # Hugo 配置
├── deploy.example.sh             # 部署脚本模板（入库）
└── deploy.sh                     # 你的部署脚本（不入库）
```

### Hugo 配置关键点

```yaml
# hugo.yaml
baseURL: "https://aipulse.lol/"
permalinks:
  posts: "/posts/:slug/"          # 干净 URL

# 自动生成 sitemap + RSS
sitemap:
  changefreq: weekly
outputs:
  home: ["HTML", "RSS"]
  section: ["HTML", "RSS"]
```

### 文章 Front Matter

```yaml
---
title: "文章标题"
date: 2026-06-22
slug: "my-post"                  # 显式指定 slug 避免中文乱码
description: "文章摘要，用于 SEO 和列表展示"
aliases:
  - /posts/old-url.html          # 旧 URL 自动 301 到新 URL
featured: true
---
```

### 模板自动处理的事

- 所有页面的 SEO 标签（OG、Twitter Card、JSON-LD）
- Canonical URL
- 阅读时间估算
- RSS feed
- sitemap.xml
- 404 页面

## 部署自动化

```bash
#!/bin/bash
# deploy.sh
set -e
echo "Building Hugo site..."
hugo --minify
echo "Deploying..."
rsync -avz --delete public/ root@your-server:/var/www/your-site/
echo "Done!"
```

`deploy.sh` 不入库（`.gitignore`），仓库放 `deploy.example.sh` 模板供他人参考。这个模式对标 `.env.example`。

## Git 与 GitHub

```bash
cd ~/dev/aipulse-hugo
git init
git remote add origin git@github.com:mbwjs/aipulse.git
git push -u origin main
```

写完文章三步：

```bash
hugo new posts/new-post.md   # 1. 新建
# ...编辑 Markdown...
./deploy.sh                  # 2. 发布到服务器
git add -A && git commit -m "new post" && git push  # 3. 备份到 GitHub
```

## 踩过的坑

1. **Porkbun DNS TXT 记录**：Host 栏留空，不是填 `@`
2. **Certbot 覆盖 nginx 配置**：证书签发后得手动恢复安全响应头和限流规则
3. **Hugo `:slug` 与中文标题**：标题含 `：` 时 Hugo 0.163 会生成奇怪 slug，加 `slug` 字段显式指定
4. **`languageCode` 已废弃**：Hugo 0.158+ 改用 `locale`
5. **`.Site.Author` 不存在**：Hugo 中自定义字段放 `params` 下，模板用 `.Site.Params.author`
6. **rsync 域名 vs IP**：`known_hosts` 里 IP 和域名是两条记录，用哪个就坚持用哪个

## 最终效果

| URL | 内容 |
|-----|------|
| `https://aipulse.lol/` | 首页，自动列出最新文章 |
| `https://aipulse.lol/posts/` | 文章存档 |
| `https://aipulse.lol/posts/loop-engineering/` | 文章（干净 URL） |
| `https://aipulse.lol/index.xml` | RSS |
| `https://aipulse.lol/sitemap.xml` | 自动生成 sitemap |
| `https://aipulse.lol/nope` | 自定义 404 |

- HTTPS：Let's Encrypt 自动续期
- 安全：fail2ban + SSH 密钥 + nginx 限流 + 安全头
- SEO：Google Search Console + 结构化数据
- 写作：Markdown → Hugo → rsync → 上线
- 备份：GitHub 私有仓库

## 成本

| 项目 | 费用 |
|------|------|
| VPS | ~$5/月（已有） |
| 域名 aipulse.lol | $5.66/年（Porkbun） |
| SSL 证书 | 免费（Let's Encrypt） |
| Hugo | 免费 |
| Nginx | 免费 |
| **总计** | **$5/月 + $5.66/年** |

---

*这就是从一台只有 SSH 端口的裸机到一个完整技术博客的全过程。如果这篇记录对你有帮助，欢迎通过 [GitHub](https://github.com/mbwjs) 交流。*
