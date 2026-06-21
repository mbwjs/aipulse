---
title: "防止密钥泄露：给 Git 加一个 pre-commit 扫描钩子"
slug: "git-secret-scan"
date: 2026-06-22
description: "几行 Shell 脚本实现 Git pre-commit 密钥扫描，防止 API Key、私钥被误提交到仓库。零依赖，macOS/Linux 通用。"
aliases:
  - /posts/git-secret-scan.html
---

## 问题

搭博客的过程中，我一直在担心一件事：不小心把 API key、服务器密码、SSH 私钥提交到 GitHub。

手动检查不靠谱——凌晨三点改完代码、`git add -A && git commit -m "fix" && git push`，脑子根本不在线。

解决方案：**Git pre-commit hook**，在每次提交前自动扫描密钥，匹配就阻止。

## 实现

在项目根目录创建 `.githooks/pre-commit`：

```bash
#!/bin/bash
set -e

STAGED=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$STAGED" ] && exit 0

# 高置信度敏感模式
PATTERNS=(
  "sk-[A-Za-z0-9]{20,}"              # OpenAI/Claude/DeepSeek key
  "gh[pousr]_[A-Za-z0-9]{36,}"       # GitHub token
  "AKIA[0-9A-Z]{16}"                 # AWS access key
  "BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY"  # 私钥
  "(password|passwd|secret)[[:space:]]*[=:][[:space:]]*['\"][^'\"]+['\"]"  # 明文密码
)

# 白名单：不应被扫描的文件
WHITELIST=(".githooks/pre-commit" "deploy.example.sh")

FOUND=0
for file in $STAGED; do
  [ ! -f "$file" ] && continue

  # 跳白名单
  skip=0
  for w in "${WHITELIST[@]}"; do
    [[ "$file" == *"$w"* ]] && skip=1
  done
  [ $skip -eq 1 ] && continue

  # 只扫文本文件
  file "$file" | grep -q 'text' || continue

  while IFS= read -r line; do
    for p in "${PATTERNS[@]}"; do
      if echo "$line" | grep -qE "$p"; then
        echo "✗ $file: ${line:0:80}"
        FOUND=1
        break
      fi
    done
  done < "$file"
done

if [ $FOUND -eq 1 ]; then
  echo "⛔ 提交被阻止：检测到疑似密钥"
  echo "确认安全：git commit --no-verify -m '...'"
  exit 1
fi
echo "✅ 密钥检查通过"
```

启用 hook：

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

## 设计思路

### 只匹配高置信度模式

常见工具如 `gitleaks` 会匹配大量模式，但也带来很多误报（CSS 哈希、HTML 内联数据、长随机字符串）。这个 hook 只匹配**几乎肯定是密钥**的模式，减少误报：

| 模式 | 原因 |
|------|------|
| `sk-...` | OpenAI/Claude 的 API key 固定前缀 |
| `gh[pousr]_...` | GitHub token 固定前缀 |
| `AKIA...` | AWS Access Key 固定前缀 |
| `BEGIN ... PRIVATE KEY` | 私钥 PEM 格式的特征头 |
| `password = "..."` | 明文密码赋值 |

### 故意不管的

- **IP 地址**：技术文章里经常写服务器 IP，不应阻止
- **高熵字符串**：CSS、HTML 里太多误报
- **`.env` 文件**：用 `.gitignore` 解决比 hook 更可靠

### 白名单机制

`deploy.example.sh` 里包含占位符 `your-server`，README 里引用了 hook 代码本身，这些文件跳过扫描。

### 紧急绕过

确认安全但被误拦：

```bash
git commit --no-verify -m "..."
```

## 怎么不忘

hook 配置（`git config core.hooksPath .githooks`）不会随仓库 clone——这是 Git 的安全设计。两个方式保证不忘记：

1. **`deploy.sh` 部署脚本**：每次部署时自动跑一次 `git config core.hooksPath .githooks`
2. **README** 里写了初始化步骤

换机器 clone 后，跑一次 `./deploy.sh`（或者直接复制 `deploy.example.sh`）就自动配好了。

## 效果

```bash
$ echo 'API_KEY=sk-abc123...' > test.txt
$ git add test.txt && git commit -m "test"
🔍 扫描敏感信息...
  ✗ test.txt: API_KEY=sk-abc123...

==============================================
  ⛔ 提交被阻止：检测到疑似密钥/敏感信息
==============================================
```

## 总结

和动辄几千行的安全扫描工具相比，这个 hook 只有 60 行，零依赖，macOS 和 Linux 都能跑。把它放在 `.githooks/` 目录下跟着仓库走，团队所有人都自动受保护。

核心原则：**宁可漏报，不可误报**。一个天天误报的 hook 等于没有，因为你会养成 `--no-verify` 肌肉记忆。

---

*代码在 [aipulse/.githooks/pre-commit](https://github.com/mbwjs/aipulse/blob/main/.githooks/pre-commit)，欢迎直接拿去用。*
