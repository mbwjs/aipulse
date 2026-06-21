#!/usr/bin/env python3
"""
题库生成 Agent — 基于用户上传的知识 + 联网搜索
用法：
  python3 quiz-agent.py --file my-notes.md --topic "Java 面试"
  python3 quiz-agent.py --url "https://example.com/article" --topic "系统设计"
  python3 quiz-agent.py --topic "Python 并发" --search  # 联网搜索最新资料
"""

import os, sys, json, re, argparse, textwrap
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import quote


# ── 配置 ──────────────────────────────────
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/v1/chat/completions"


def load_file(path: str) -> str:
    """读取用户上传的知识文件"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 截断（API context 有限）
    if len(content) > 12000:
        content = content[:12000] + "\n...(内容已截断)"
    return content


def fetch_url(url: str) -> str:
    """抓取网页内容（简单版）"""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urlopen(req, timeout=30)
        html = resp.read().decode("utf-8", errors="ignore")
        # 简易清洗：去掉 HTML 标签
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:12000]
    except Exception as e:
        print(f"⚠️  抓取失败: {e}", file=sys.stderr)
        return ""


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> dict:
    """调用 DeepSeek，返回 JSON"""
    if not API_KEY:
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)

    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }).encode()

    try:
        req = Request(API_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        })
        resp = urlopen(req, timeout=180)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        content = re.sub(r'^```json\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"❌ API 错误: {e}", file=sys.stderr)
        if hasattr(e, "read"):
            print(e.read().decode()[:500], file=sys.stderr)
        sys.exit(1)


SYSTEM_PROMPT = textwrap.dedent("""\
你是一个专业的题库生成专家。你的任务是根据提供的知识材料，生成高质量的面试题和练习题。

题目要求：
- 覆盖材料的核心知识点
- 从简单到困难递进
- 单选题必须有 4 个选项，干扰项要有迷惑性
- 每道题附带详细解析
- 简答题需要参考答案和评分要点

严格输出 JSON。
""")


def build_user_prompt(topic: str, knowledge_text: str = "", num_questions: int = 20) -> str:
    """构建 prompt"""
    parts = [f'生成一套关于"{topic}"的题库，共 {num_questions} 题。']

    if knowledge_text:
        parts.append(f"""参考以下知识材料（用户上传 + 网络搜索）：

---
{knowledge_text[:8000]}
---

请严格基于以上材料出题，不要编造材料中没有的知识点。""")

    parts.append("""题目分配：
- 40% 单选题（4个选项）
- 30% 多选题（4个选项，可能多个正确答案）
- 20% 判断题
- 10% 简答题""")

    parts.append("""按难度分三级：
- 基础（40%）：概念记忆和理解
- 进阶（40%）：分析应用
- 困难（20%）：综合评估和设计""")

    parts.append('输出格式：{"title":"题库标题","description":"简介","total":N,"questions":[...]}')
    parts.append('每道题格式：{"id":1,"type":"choice|multi|tf|essay","difficulty":"basic|medium|hard","tags":["标签"],"q":"题目","options":["A.xx","B.xx"],"answer":"A","explanation":"解析","points":5}')

    return "\n\n".join(parts)


def generate(topic: str, knowledge_text: str = "", num: int = 20) -> dict:
    return call_llm(SYSTEM_PROMPT, build_user_prompt(topic, knowledge_text, num))


def to_markdown(data: dict) -> str:
    """题库 → Markdown 文件"""
    md = f'# {data.get("title", "题库")}\n\n'
    md += f'> {data.get("description", "")}\n\n'
    md += f'共 {data.get("total", len(data.get("questions", [])))} 题\n\n---\n\n'

    by_diff = {"basic": [], "medium": [], "hard": []}
    for q in data.get("questions", []):
        by_diff.get(q.get("difficulty", "basic"), by_diff["basic"]).append(q)

    diff_labels = {"basic": "基础", "medium": "进阶", "hard": "困难"}
    tag_icons = {"choice": "🔘", "multi": "☑️", "tf": "✅", "essay": "✍️"}

    for level in ["basic", "medium", "hard"]:
        questions = by_diff[level]
        if not questions:
            continue
        md += f"## {diff_labels[level]}（{len(questions)} 题）\n\n"
        for q in questions:
            md += f'### {tag_icons.get(q.get("type",""), "")} 第{q.get("id", "?")}题'
            md += f' · {q.get("difficulty", "")}\n\n'
            md += f'{q.get("q", "")}\n\n'

            if q.get("type") in ("choice", "multi"):
                for opt in q.get("options", []):
                    md += f"- {opt}\n"
                md += f'\n<details><summary>点击查看答案</summary>\n\n✅ **{q.get("answer", "")}**\n\n'
            elif q.get("type") == "tf":
                md += f'\n<details><summary>点击查看答案</summary>\n\n✅ **{q.get("answer", "")}**\n\n'
            else:
                md += f'\n<details><summary>点击查看答案</summary>\n\n📝 参考答案：\n\n{q.get("answer", "")}\n\n'

            md += f'📖 解析：{q.get("explanation", "")}\n\n'
            md += '</details>\n\n---\n\n'

    return md


def save_output(data: dict, output_dir: str, topic: str):
    """保存 JSON + Markdown"""
    os.makedirs(output_dir, exist_ok=True)
    slug = re.sub(r'[^\w-]', '', topic.lower())[:30] or "quiz"

    # JSON
    json_path = os.path.join(output_dir, f"{slug}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Markdown
    md_path = os.path.join(output_dir, f"{slug}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(to_markdown(data))

    return json_path, md_path


def print_preview(data: dict):
    """打印预览到终端"""
    qs = data.get("questions", [])
    print(f'📚 {data.get("title", "题库")}')
    print(f'   共 {len(qs)} 题')
    by_diff = {}
    for q in qs:
        d = q.get("difficulty", "basic")
        by_diff[d] = by_diff.get(d, 0) + 1
    for d, c in by_diff.items():
        print(f'   {d}: {c} 题')
    print()

    # 展示前 3 题
    for q in qs[:3]:
        print(f'第{q.get("id","?")}题 [{q.get("difficulty","")}] {q.get("q","")[:80]}...')
        print(f'   答案: {q.get("answer","")}')
        print()


def main():
    parser = argparse.ArgumentParser(description="题库生成 Agent — 基于知识材料 + 联网搜索")
    parser.add_argument("--topic", "-t", required=True, help="题库主题，如 'Java 并发编程'")
    parser.add_argument("--file", "-f", help="用户上传的知识文件（.md/.txt）")
    parser.add_argument("--url", "-u", help="参考网页 URL")
    parser.add_argument("--search", "-s", action="store_true", help="启用联网搜索最新资料")
    parser.add_argument("--num", "-n", type=int, default=20, help="生成题目数（默认 20）")
    parser.add_argument("--output", "-o", default="/tmp/quiz-output", help="输出目录")
    parser.add_argument("--preview", "-p", action="store_true", help="仅终端预览，不保存")
    args = parser.parse_args()

    print(f"🧠 题库生成 Agent v0.2")
    print(f"📝 主题: {args.topic}")
    print(f"📊 目标: {args.num} 题")

    # 收集知识材料
    knowledge_parts = []

    if args.file:
        print(f"📂 读取文件: {args.file}")
        knowledge_parts.append(f"## 用户上传资料\n{load_file(args.file)}")

    if args.url:
        print(f"🌐 抓取网页: {args.url}")
        web_content = fetch_url(args.url)
        if web_content:
            knowledge_parts.append(f"## 网页内容\n{web_content}")

    if args.search:
        print(f"🔍 联网搜索（模拟：请在生产环境接入搜索 API）")
        knowledge_parts.append("(联网搜索结果将在正式版中接入 Bing/Google Search API)")

    knowledge_text = "\n\n---\n\n".join(knowledge_parts)

    # 生成
    print(f"⏳ AI 生成中...")
    data = generate(args.topic, knowledge_text, args.num)

    print(f"✅ 生成完成：{len(data.get('questions', []))} 题")

    if args.preview:
        print_preview(data)
        return

    # 保存
    json_path, md_path = save_output(data, args.output, args.topic)
    print(f"💾 已保存:")
    print(f"   JSON: {json_path}")
    print(f"   MD:   {md_path}")
    print_preview(data)


if __name__ == "__main__":
    main()
