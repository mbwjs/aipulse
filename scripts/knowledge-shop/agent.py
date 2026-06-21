#!/usr/bin/env python3
"""
知识商店搭建 Agent — MVP
用法：
  python3 agent.py "Java 面试题库" --category 后端 --chapters 5
  → 自动生成 Hugo 知识付费站 → 本地可预览 → 一键部署
"""

import os, sys, json, re, shutil, subprocess, argparse, textwrap
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
TEMPLATE_DIR = SCRIPT_DIR / "template"


# ── 策略配置 ──────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""\
你是一个知识付费网站的内容生成专家。你的任务是生成一套结构化的知识内容，
包含章节讲解和配套练习题。输出必须严格遵循 JSON 格式。

每章要求：
- 讲解部分包含核心概念、代码示例（如果有）、常见面试题和答案
- 练习题 5 道，单选 3 道 + 简答 2 道
- 整体语言正式但易懂，适合学习备考使用
""")

USER_PROMPT_TEMPLATE = textwrap.dedent("""\
生成一套关于"{topic}"的知识付费内容，分类：{category}。

要求：
1. 生成 {chapters} 章内容
2. 每章包含：标题、讲解内容（300-500字）、3个核心知识点、2个常见面试题（含答案）
3. 每章附带 5 道练习题（3单选+2简答，含答案和解析）
4. 整体生成一个完整的知识体系，从入门到进阶

严格按以下 JSON 格式输出（不要加 markdown 代码块标记）：
{{
  "title": "课程标题",
  "description": "一句话描述",
  "chapters": [
    {{
      "title": "第N章 章节名",
      "content": "章节讲解内容...",
      "key_points": ["知识点1", "知识点2", "知识点3"],
      "interview_qa": [
        {{"q": "面试题", "a": "答案"}},
        {{"q": "面试题", "a": "答案"}}
      ],
      "exercises": [
        {{"type": "choice", "q": "题目", "options": ["A.xx","B.xx","C.xx","D.xx"], "answer": "A", "explanation": "解析"}},
        {{"type": "choice", "q": "题目", "options": ["A.xx","B.xx","C.xx","D.xx"], "answer": "B", "explanation": "解析"}},
        {{"type": "choice", "q": "题目", "options": ["A.xx","B.xx","C.xx","D.xx"], "answer": "C", "explanation": "解析"}},
        {{"type": "essay", "q": "简答题", "answer": "参考答案", "explanation": "解析"}},
        {{"type": "essay", "q": "简答题", "answer": "参考答案", "explanation": "解析"}}
      ]
    }}
  ]
}}
""")


def call_deepseek(system_prompt: str, user_prompt: str) -> dict:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)

    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }).encode()

    req = Request("https://api.deepseek.com/v1/chat/completions", data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    try:
        resp = urlopen(req, timeout=180)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        # 清理可能的 markdown 代码块标记
        content = re.sub(r'^```json\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"❌ API 调用失败: {e}", file=sys.stderr)
        if hasattr(e, "read"):
            print(e.read().decode()[:500], file=sys.stderr)
        sys.exit(1)


def build_hugo_site(data: dict, output_dir: Path, args):
    """根据生成的数据构建 Hugo 站点"""
    slug = re.sub(r'[^\w-]', '', data['title'].lower())[:30] or "knowledge-shop"
    site_dir = output_dir / slug
    if site_dir.exists():
        shutil.rmtree(site_dir)

    # 创建 Hugo 项目
    subprocess.run(["hugo", "new", "site", str(site_dir), "--format", "yaml"],
                   capture_output=True, check=True)

    # 写入 Hugo 配置
    title = data["title"]
    desc = data.get("description", "")
    hugo_yaml = f'baseURL: "https://YOUR_USERNAME.github.io/{slug}/"\n'
    hugo_yaml += f'title: "{title}"\n'
    hugo_yaml += 'params:\n'
    hugo_yaml += f'  description: "{desc}"\n'
    hugo_yaml += 'disableKinds: ["taxonomy", "term"]\n'
    hugo_yaml += 'markup:\n  goldmark:\n    renderer:\n      unsafe: true\n'
    (site_dir / "hugo.yaml").write_text(hugo_yaml)

    # 创建模板
    (site_dir / "layouts").mkdir(exist_ok=True)
    (site_dir / "layouts" / "_default").mkdir(exist_ok=True)
    (site_dir / "layouts" / "partials").mkdir(exist_ok=True)

    # 创建极简主题
    baseof = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{{ .Title }} | {{ .Site.Title }}</title>
    <style>
    :root{--bg:#fff;--text:#1a1a2e;--accent:#6366f1;--border:#e5e7eb;--code-bg:#f3f4f6}
    @media(prefers-color-scheme:dark){:root{--bg:#0f0f19;--text:#e2e8f0;--accent:#818cf8;--border:#2d2d44;--code-bg:#1e1e32}}
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);line-height:1.7;max-width:800px;margin:0 auto;padding:24px}
    header{border-bottom:1px solid var(--border);padding-bottom:16px;margin-bottom:32px}
    header h1{font-size:1.5rem}
    nav{margin-top:8px}
    nav a{color:var(--accent);text-decoration:none;margin-right:16px;font-size:.9rem}
    .paywall{background:var(--code-bg);border:2px solid var(--accent);border-radius:12px;padding:24px;text-align:center;margin:32px 0}
    .paywall h3{font-size:1.2rem;margin-bottom:8px}
    .paywall p{color:#6b7280;margin-bottom:16px}
    .paywall button{background:var(--accent);color:#fff;border:none;padding:12px 32px;border-radius:8px;font-size:1rem;cursor:pointer;font-weight:600}
    .content h2{font-size:1.3rem;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
    .content h3{font-size:1.1rem;margin:24px 0 8px}
    .qa{background:var(--code-bg);border-radius:8px;padding:16px;margin:12px 0}
    .qa .q{font-weight:600}
    .qa .a{margin-top:8px;color:#6b7280}
    .exercise{border:1px solid var(--border);border-radius:8px;padding:16px;margin:12px 0}
    .exercise .q{font-weight:600}
    .exercise .options{margin:8px 0;padding-left:16px}
    .exercise .answer{color:var(--accent);font-weight:600;cursor:pointer}
    footer{text-align:center;padding:40px 0;color:#6b7280;font-size:.85rem;border-top:1px solid var(--border);margin-top:40px}
    </style>
    </head>
    <body>
    <header>
    <h1>{{ .Site.Title }}</h1>
    <nav><a href="/">首页</a><a href="/chapters/">章节</a><a href="/quiz/">刷题</a></nav>
    </header>
    <main>{{ block "main" . }}{{ end }}</main>
    <footer><p>Powered by <a href="https://aipulse.lol" style="color:var(--accent)">AI Pulse 知识商店</a> · 自动生成</p></footer>
    </body></html>
    """)
    (site_dir / "layouts" / "_default" / "baseof.html").write_text(baseof)

    # 首页模板
    home_tpl = textwrap.dedent("""\
    {{ define "main" }}
    <h2>课程简介</h2>
    <p>{{ .Site.Params.description }}</p>
    <h3 style="margin-top:24px">章节列表</h3>
    <ul>
    {{ range .Site.RegularPages }}
    <li style="margin:12px 0"><a href="{{ .RelPermalink }}" style="color:var(--accent);font-weight:600;text-decoration:none">{{ .Title }}</a></li>
    {{ end }}
    </ul>
    <div class="paywall">
    <h3>🔒 解锁全部内容</h3>
    <p>¥9.9 解锁全部章节 + 练习题答案 + 面试题解析</p>
    <button onclick="alert('支付功能将在正式版上线！')">立即解锁</button>
    </div>
    {{ end }}
    """)
    (site_dir / "layouts" / "_default" / "home.html").write_text(home_tpl)

    # 单页模板
    single_tpl = textwrap.dedent("""\
    {{ define "main" }}
    <h1>{{ .Title }}</h1>
    <div class="content">
    {{ .Content }}
    </div>
    <div class="paywall">
    <h3>🔒 查看答案解析</h3>
    <p>本练习题的答案和面试题详解需要付费解锁</p>
    <button onclick="alert('支付功能将在正式版上线！')">¥9.9 解锁</button>
    </div>
    {{ end }}
    """)
    (site_dir / "layouts" / "_default" / "single.html").write_text(single_tpl)

    # 写入内容：每个章节一个 Markdown 文件
    content_dir = site_dir / "content"
    content_dir.mkdir(exist_ok=True)

    # _index.md
    (content_dir / "_index.md").write_text(
        f'---\ntitle: "{data["title"]}"\n---\n{data["description"]}\n'
    )

    # 每章
    for i, ch in enumerate(data["chapters"], 1):
        md = f'---\ntitle: "{ch["title"]}"\nweight: {i}\n---\n\n'
        md += ch["content"] + "\n\n"

        # 核心知识点
        md += "### 核心知识点\n\n"
        for kp in ch.get("key_points", []):
            md += f"- ✅ {kp}\n"
        md += "\n"

        # 面试题
        md += "### 常见面试题\n\n"
        for j, qa in enumerate(ch.get("interview_qa", []), 1):
            md += f'<div class="qa"><div class="q">Q{j}: {qa["q"]}</div>\n'
            md += f'<div class="a">💡 {qa["a"]}</div></div>\n\n'

        # 练习题
        md += "### 本章练习\n\n"
        for j, ex in enumerate(ch.get("exercises", []), 1):
            md += f'<div class="exercise"><div class="q">第{j}题'
            if ex["type"] == "choice":
                md += "（单选）"
            else:
                md += "（简答）"
            md += f'</div>\n<p>{ex["q"]}</p>\n'
            if ex["type"] == "choice" and "options" in ex:
                md += '<div class="options">\n'
                for opt in ex["options"]:
                    md += f"<div>{opt}</div>\n"
                md += '</div>\n'
            md += f'<div class="answer" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='
            md += f"\"none\"?'block':'none'\">点击查看答案</div>\n"
            md += f'<div style="display:none;margin-top:8px;color:var(--accent)">✅ {ex.get("answer","")}'
            if ex.get("explanation"):
                md += f'<br>📝 {ex["explanation"]}'
            md += '</div></div>\n\n'

        slug = re.sub(r'[^\w-]', '', ch["title"][:20].lower()) or f"chapter-{i}"
        (content_dir / f"chapter-{i:02d}.md").write_text(md)

    # 构建
    print(f"🏗️  构建 Hugo 站点...")
    subprocess.run(["hugo", "--minify"], cwd=site_dir, check=True)
    print(f"✅ 站点已生成: {site_dir}/public/")


def make_readme(data: dict, output_dir: Path, slug: str) -> Path:
    """生成 README + 部署说明"""
    readme_path = output_dir / "README.md"
    readme_path.write_text(textwrap.dedent(f"""\
    # {data['title']}

    > 🤖 本知识站点由 [AI Pulse 知识商店](https://aipulse.lol) 自动生成
    > 包含 {len(data['chapters'])} 章内容，每章含面试题和练习题

    ## 快速部署

    ### 方式 1：GitHub Pages（免费）
    1. Fork 本仓库
    2. Settings → Pages → Source 选 GitHub Actions
    3. 访问 `https://你的用户名.github.io/{slug}/`

    ### 方式 2：本地运行
    ```bash
    hugo server
    ```

    ### 方式 3：一键部署到 Vercel
    [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

    ## 自定义内容
    编辑 `content/` 目录下的 Markdown 文件即可修改内容。
    编辑 `hugo.yaml` 修改网站配置。

    ## 升级到付费版
    联系 [aipulse.lol](https://aipulse.lol) 获取：
    - 自动内容生成 Agent（每天自动产出新题目）
    - 付费墙系统
    - 用户管理后台
    - 策略市场接入

    ---
    *由 AI Pulse 知识商店 Agent 生成 · {datetime.now().strftime("%Y-%m-%d")}*
    """))

    if not (output_dir / ".github" / "workflows").exists():
        (output_dir / ".github" / "workflows").mkdir(parents=True)
    workflow = textwrap.dedent("""\
    name: Deploy to GitHub Pages
    on: [push]
    permissions:
      contents: read
      pages: write
      id-token: write
    jobs:
      deploy:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: peaceiris/actions-hugo@v3
            with:
              hugo-version: "0.163.3"
              extended: true
          - run: hugo --minify
          - uses: actions/upload-pages-artifact@v3
            with:
              path: ./public
          - uses: actions/deploy-pages@v4
    """)
    (output_dir / ".github" / "workflows" / "pages.yml").write_text(workflow)

    return readme_path


def main():
    parser = argparse.ArgumentParser(description="知识商店搭建 Agent — MVP")
    parser.add_argument("topic", help="知识库主题，如 'Java 面试题库'")
    parser.add_argument("--category", "-c", default="技术面试", help="分类")
    parser.add_argument("--chapters", "-n", type=int, default=3, help="章节数（默认3）")
    parser.add_argument("--output", "-o", default=str(OUTPUT_DIR), help="输出目录")
    parser.add_argument("--preview", "-p", action="store_true", help="生成后启动本地预览")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🧠 知识商店 Agent v0.1")
    print(f"📚 主题: {args.topic}")
    print(f"📂 分类: {args.category}")
    print(f"📖 章节: {args.chapters} 章")
    print(f"⏳ 调用 AI 生成中...")

    user_prompt = USER_PROMPT_TEMPLATE.format(
        topic=args.topic, category=args.category, chapters=args.chapters
    )
    data = call_deepseek(SYSTEM_PROMPT, user_prompt)

    print(f"✅ 内容生成完成: {data['title']}")
    print(f"   共 {len(data['chapters'])} 章")

    # 构建 Hugo 站点
    build_hugo_site(data, output_dir, args)
    slug = re.sub(r'[^\w-]', '', data['title'].lower())[:30] or "knowledge-shop"

    # 生成 README + GitHub Actions
    readme_path = make_readme(data, output_dir / slug, slug)
    print(f"📄 README 已生成: {readme_path}")

    # 打印摘要
    print("\n" + "=" * 60)
    print(f"🎉 知识站点生成完毕！")
    print(f"   标题: {data['title']}")
    print(f"   章节: {len(data['chapters'])} 章")
    print(f"   目录: {output_dir / slug}")
    print(f"   预览: cd {output_dir / slug} && hugo server")
    print("=" * 60)


if __name__ == "__main__":
    main()
