#!/bin/bash
# ============================================
#  AI Pulse 部署脚本 — 示例
# ============================================
#
# 使用方法：
#   1. 复制此文件：cp deploy.example.sh deploy.sh
#   2. 修改 DEPLOY_TARGET 为你的服务器地址
#   3. chmod +x deploy.sh && ./deploy.sh
#
# deploy.sh 不会入库（.gitignore 已忽略），避免泄露服务器信息。
# ============================================

set -e

# 确保密钥扫描 hook 生效
git config core.hooksPath .githooks

# 修改为你的服务器地址（user@host:/path/to/www/）
DEPLOY_TARGET="root@your-server:/var/www/your-site/"

echo "Building Hugo site..."
hugo --buildFuture

echo "Deploying to ${DEPLOY_TARGET}..."
rsync -avz --delete public/ "${DEPLOY_TARGET}"

echo "Done!"
