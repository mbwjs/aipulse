#!/usr/bin/env python3
"""
AI Pulse 内容生成 Agent
用法：python3 scripts/generate.py "话题" --strategy tech-deep-dive
"""

import os
import sys
import json
import argparse
import re
import subprocess
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
STRATEGY_FILE = os.path.join(SCRIPT_DIR, "strategy.yaml")
CONTENT_DIR = os.path.join(PROJECT_DIR, "content", "posts")


def load_strategies():
    with open(STRATEGY_FILE) as f:
        return yaml.safe_load(f)


def call_deepseek(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """调用 DeepSeek API 生成内容"""
    url = "https://api.deepseek.com/v1/chat/completions"
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 4096,
        "stream": False,
    }).encode()

    req = Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    try:
        resp = urlopen(req, timeout=120)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except URLError as e:
        print(f"❌ API 调用失败: {e}", file=sys.stderr)
        if hasattr(e, "read"):
            print(e.read().decode(), file=sys.stderr)
        sys.exit(1)


def slugify(text: str) -> str:
    """从标题中提取英文词做 slug，纯中文则用日期+hash"""
    text = text.strip()
    # 提取英文单词
    english_words = re.findall(r"[a-zA-Z0-9]{2,}", text)
    if english_words:
        slug = "-".join(english_words[:4])
        return slug.strip("-").lower()[:50] or "untitled"
    # 纯中文：用日期
    return datetime.now().strftime("post-%Y%m%d")


def make_frontmatter(title: str, description: str, slug: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"""---
title: "{title}"
slug: "{slug}"
date: {date_str}
description: "{description}"
aliases:
  - /posts/{slug}.html
---"""


def save_post(slug: str, frontmatter: str, content: str) -> str:
    """保存为 Hugo Markdown 文件"""
    filepath = os.path.join(CONTENT_DIR, f"{slug}.md")
    with open(filepath, "w") as f:
        f.write(frontmatter + "\n\n" + content)
    return filepath


def deploy():
    """部署到 VPS + 推送到 GitHub"""
    deploy_script = os.path.join(PROJECT_DIR, "deploy.sh")
    subprocess.run(["bash", deploy_script], check=True)
    subprocess.run(["git", "add", "-A"], cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "commit", "--no-verify", "-m", f"AI generated post: {datetime.now().strftime('%Y-%m-%d')}"],
                   cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "push"], cwd=PROJECT_DIR, check=True)


def main():
    parser = argparse.ArgumentParser(description="AI Pulse 内容生成 Agent")
    parser.add_argument("topic", help="文章话题，如 'GPT-5 的推理架构'")
    parser.add_argument("--strategy", "-s", default=None,
                        help="内容策略（tech-deep-dive / quick-insight）")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="只生成内容，不保存不部署")
    parser.add_argument("--deploy", "-d", action="store_true",
                        help="生成后自动部署")
    args = parser.parse_args()

    # 加载策略
    data = load_strategies()
    strategies = data["strategies"]
    strategy_name = args.strategy or data["default_strategy"]

    if strategy_name not in strategies:
        print(f"❌ 未知策略: {strategy_name}")
        print(f"   可用策略: {', '.join(strategies.keys())}")
        sys.exit(1)

    strategy = strategies[strategy_name]

    # 获取 API key
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未设置", file=sys.stderr)
        sys.exit(1)

    # 生成
    print(f"🖊️  策略: {strategy['name']}")
    print(f"📝 话题: {args.topic}")
    print(f"⏳ 生成中...")

    user_prompt = strategy["user_prompt_template"].format(topic=args.topic)
    content = call_deepseek(strategy["system_prompt"], user_prompt, api_key)

    if not content.strip():
        print("❌ 生成内容为空", file=sys.stderr)
        sys.exit(1)

    # 提取标题（第一行 # 开头）
    lines = content.strip().split("\n")
    title = args.topic
    description = ""
    body_start = 0

    if lines[0].startswith("# "):
        title = lines[0][2:].strip()
        body_start = 1

    # 提取描述（第一段非空文字）
    for line in lines[body_start:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
            description = stripped[:160]
            break

    slug = slugify(title) or slugify(args.topic)

    frontmatter = make_frontmatter(title, description, slug)
    final_content = "\n".join(lines[body_start:])

    if args.dry_run:
        print("\n" + "=" * 60)
        print(frontmatter)
        print("\n" + final_content[:500] + "...")
        print("=" * 60)
        print(f"\n📄 预览完成（共 {len(final_content)} 字符）")
        return

    # 保存
    filepath = save_post(slug, frontmatter, final_content)
    print(f"✅ 已保存: {filepath}")
    print(f"   标题: {title}")
    print(f"   大小: {len(final_content)} 字符")
    print(f"   路径: /posts/{slug}/")

    # 部署
    if args.deploy:
        print("🚀 部署中...")
        deploy()
        print(f"✅ 已上线: https://aipulse.lol/posts/{slug}/")
        print(f"   GitHub: https://mbwjs.github.io/aipulse/posts/{slug}/")


if __name__ == "__main__":
    main()
