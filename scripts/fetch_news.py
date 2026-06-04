#!/usr/bin/env python3
"""
每日 AI 资讯抓取脚本
GitHub Actions 每天 7 点自动运行
"""

import json
import os
import re
from datetime import date
from urllib.request import Request, urlopen
from urllib.error import URLError

NEWS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "news")

def fetch_json(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠ 请求失败: {url} -> {e}")
        return None

def fetch_text(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠ 请求失败: {url} -> {e}")
        return None

# ─── Hacker News ────────────────────────────────────────────────

def fetch_hn_ai_stories():
    """从 Hacker News 获取 AI 相关热门文章"""
    print("📡 正在获取 Hacker News 热门...")
    top_ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not top_ids:
        return []

    ai_keywords = re.compile(
        r"ai|artificial\s*intelligen|machine\s*learn|deep\s*learn|neural|"
        r"llm|gpt|chatgpt|claude|anthropic|openai|gemini|bard|"
        r"transformer|diffusion|langchain|agent|rag|fine.tun|"
        r"copilot|llama|mistral|mixtral|qwen|yi-34b", re.I
    )

    results = []
    for story_id in top_ids[:100]:
        story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not story or not story.get("title"):
            continue
        title = story["title"]
        if ai_keywords.search(title):
            results.append({
                "title": title,
                "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "score": story.get("score", 0),
                "source": "Hacker News",
                "desc": f"🔥 {story.get('score', 0)} 分 · {story.get('by', 'anonymous')}"
            })
            if len(results) >= 30:
                break

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"  ✓ 获取 {len(results)} 条 HN AI 资讯")
    return results

# ─── Reddit ─────────────────────────────────────────────────────

def fetch_reddit_ai():
    """从 Reddit 获取 AI 热门帖子"""
    print("📡 正在获取 Reddit AI 热门...")
    data = fetch_json("https://www.reddit.com/r/artificial/hot.json?limit=25")
    if not data:
        return []

    results = []
    for item in data.get("data", {}).get("children", []):
        d = item.get("data", {})
        title = d.get("title", "")
        if not title:
            continue
        results.append({
            "title": title,
            "url": d.get("url", f"https://reddit.com{d.get('permalink', '')}"),
            "score": d.get("score", 0),
            "source": "Reddit r/artificial",
            "desc": f"💬 {d.get('score', 0)} 票 · {d.get('num_comments', 0)} 评论"
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"  ✓ 获取 {len(results)} 条 Reddit AI 资讯")
    return results[:20]

# ─── GitHub Issue ────────────────────────────────────────────────

def create_github_issue(content):
    """在 GitHub 仓库创建 Issue 推送日报"""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("INPUT_GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("  ⚠ 无 GITHUB_TOKEN 或 GITHUB_REPOSITORY，跳过 Issue 创建")
        return False

    today = date.today().isoformat()
    weekday_map = ["一", "二", "三", "四", "五", "六", "日"]
    weekday = weekday_map[date.today().weekday()]

    body = f"""# 🤖 AI 资讯日报 — {today}（周{weekday}）

> 自动聚合 · 来源：Hacker News / Reddit · 由 GitHub Actions 自动生成

{content}

---

*事实与判断区分：以上内容为 AI 聚合，仅供参考。*
"""

    payload = json.dumps({
        "title": f"🤖 AI 资讯日报 - {today}",
        "body": body
    }).encode("utf-8")

    req = Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=payload,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "AI-News-Bot/1.0"
        }
    )
    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"✅ Issue 已创建: {result.get('html_url', '')}")
            return True
    except Exception as e:
        print(f"  ⚠ Issue 创建失败: {e}")
        return False

# ─── 生成 Markdown ──────────────────────────────────────────────

def generate_markdown(hn_news, reddit_news):
    today = date.today().isoformat()
    weekday_map = ["一", "二", "三", "四", "五", "六", "日"]
    weekday = weekday_map[date.today().weekday()]

    lines = [
        f"# 🤖 AI 资讯日报 — {today}（周{weekday}）\n",
        "> 自动聚合 · 每天 7:00 更新 · 来源：Hacker News / Reddit\n",
        "---\n"
    ]

    # ── HN ──
    if hn_news:
        lines.append("## 🔥 Hacker News 热门 AI 话题\n")
        for i, n in enumerate(hn_news[:15], 1):
            lines.append(f"### {i}. [{n['title']}]({n['url']})")
            lines.append(f"*{n['desc']}*\n")

    # ── Reddit ──
    if reddit_news:
        lines.append("## 💬 Reddit 热门讨论\n")
        for i, n in enumerate(reddit_news[:10], 1):
            lines.append(f"### {i}. [{n['title']}]({n['url']})")
            lines.append(f"*{n['desc']}*\n")

    # ── Tail ──
    lines.append("---\n")
    lines.append(f"*本日报由 GitHub Actions 自动生成 · {today}*\n")
    lines.append("*事实与判断区分：以上内容为 AI 聚合，仅供参考。*\n")
    lines.append("#AI日报 #人工智能\n")

    return "\n".join(lines)

def save_markdown(content):
    os.makedirs(NEWS_DIR, exist_ok=True)
    filename = f"{date.today().isoformat()}-AI资讯日报.md"
    filepath = os.path.join(NEWS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已保存: {filepath}")
    return filepath

def main():
    print("=" * 50)
    print(f"  AI 资讯日报生成器 — {date.today().isoformat()}")
    print("=" * 50)

    hn = fetch_hn_ai_stories()
    reddit = fetch_reddit_ai()

    md = generate_markdown(hn, reddit)
    path = save_markdown(md)

    # 在 GitHub Actions 环境也创建 Issue 推送
    create_github_issue(md)

    # 输出 GitHub Actions 能用的变量
    with open(os.environ.get("GITHUB_ENV", os.devnull), "a") as f:
        f.write(f"NEWS_FILE={path}\n")

    print(f"\n📄 生成完成: {path}")
    print(f"   共 {len(hn) + len(reddit)} 条资讯")

if __name__ == "__main__":
    main()
