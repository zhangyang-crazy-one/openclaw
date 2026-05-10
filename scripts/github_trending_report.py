#!/usr/bin/env python3
"""
GitHub Trending 简报生成脚本 v3
策略：多维度发现 — trending + 近期高星 + 快速增长
增强：重试+退避、超时调优、优雅降级
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import quote

PROXY = "http://127.0.0.1:7897"
MAX_RETRIES = 3
BASE_DELAY = 10  # 基础退避秒数


def github_api(path, params=None, timeout=30, quiet=False):
    """
    调用 GitHub API (走代理)，带重试+指数退避。
    timeout 针对不同查询调优。
    返回 (data_or_None, error_message_or_None)
    """
    from urllib.parse import urlencode
    url = f"https://api.github.com{path}"
    if params:
        qs = urlencode(params)
        url += f"?{qs}"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                ["curl", "-s", "-x", PROXY, "--max-time", str(timeout),
                 "--connect-timeout", "15",
                 "-H", "Accept: application/vnd.github+json",
                 "-H", "User-Agent: Mozilla/5.0",
                 url],
                capture_output=True, text=True, timeout=timeout + 10
            )

            if result.returncode != 0:
                last_error = f"curl exit={result.returncode}"
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))
                    if not quiet:
                        print(f"  ⚠️ 重试 {attempt}/{MAX_RETRIES} ({last_error})，{delay}s后重试...",
                              file=sys.stderr)
                    time.sleep(delay)
                continue

            raw = result.stdout.strip()
            if not raw:
                last_error = "empty response"
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))
                    if not quiet:
                        print(f"  ⚠️ 重试 {attempt}/{MAX_RETRIES} ({last_error})，{delay}s后重试...",
                              file=sys.stderr)
                    time.sleep(delay)
                continue

            data = json.loads(raw)

            # GitHub rate limit
            if isinstance(data, dict) and "message" in data:
                msg = data["message"]
                if "rate limit" in msg.lower() or "403" in msg:
                    last_error = f"rate limited: {msg}"
                    if attempt < MAX_RETRIES:
                        delay = BASE_DELAY * (2 ** (attempt - 1)) * 2  # 加倍等待
                        print(f"  ⚠️ 速率限制 {attempt}/{MAX_RETRIES}，{delay}s后重试...",
                              file=sys.stderr)
                        time.sleep(delay)
                    continue
                else:
                    last_error = f"API message: {msg}"
                    if attempt < MAX_RETRIES:
                        delay = BASE_DELAY * (2 ** (attempt - 1))
                        print(f"  ⚠️ 重试 {attempt}/{MAX_RETRIES} ({last_error})，{delay}s后重试...",
                              file=sys.stderr)
                        time.sleep(delay)
                    continue

            return data, None

        except subprocess.TimeoutExpired:
            last_error = "subprocess timeout"
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                if not quiet:
                    print(f"  ⚠️ 重试 {attempt}/{MAX_RETRIES} ({last_error})，{delay}s后重试...",
                          file=sys.stderr)
                time.sleep(delay)
        except json.JSONDecodeError:
            last_error = "JSON parse error"
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                if not quiet:
                    print(f"  ⚠️ 重试 {attempt}/{MAX_RETRIES} ({last_error})，{delay}s后重试...",
                          file=sys.stderr)
                time.sleep(delay)
        except Exception as e:
            last_error = str(e)[:100]
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                if not quiet:
                    print(f"  ⚠️ 重试 {attempt}/{MAX_RETRIES} ({last_error})，{delay}s后重试...",
                          file=sys.stderr)
                time.sleep(delay)

    return None, last_error


def format_stars(n):
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def search_new_repos(days=7, limit=15):
    """搜索最近N天创建的热门仓库。使用更高超时因为这查询最昂贵。"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    data, err = github_api("/search/repositories", {
        "q": f"created:>{since}",
        "sort": "stars",
        "order": "desc",
        "per_page": str(limit)
    }, timeout=60)  # 长超时 — 无关键词全量搜索
    if data is None:
        return [], err
    return data.get("items", []), None


def search_fast_growing(limit=10):
    """搜索本周增长最快的仓库"""
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    data, err = github_api("/search/repositories", {
        "q": f"pushed:>{since} stars:>500",
        "sort": "updated",
        "order": "desc",
        "per_page": str(limit)
    }, timeout=30)
    if data is None:
        return [], err
    return data.get("items", []), None


def search_topic_repos(topics, limit=5):
    """搜索特定 topic 的仓库"""
    repos = []
    for topic in topics:
        data, err = github_api("/search/repositories", {
            "q": f"topic:{topic}",
            "sort": "stars",
            "order": "desc",
            "per_page": str(limit)
        }, timeout=30)
        if data:
            repos.extend(data.get("items", [])[:limit])
    return repos


def categorize(repo):
    name = (repo.get("full_name") or "").lower()
    desc = (repo.get("description") or "").lower()
    topics = repo.get("topics", [])
    lang = repo.get("language") or ""

    combined = f"{name} {desc} {' '.join(topics)}"

    if any(k in combined for k in ["ai", "llm", "agent", "machine-learning", "deep-learning",
                                     "rag", "prompt", "langchain", "gpt", "transformer"]):
        return "🤖 AI/Agent"
    elif any(k in combined for k in ["cli", "devops", "kubernetes", "docker", "monitor",
                                      "debug", "testing", "ci", "terminal", "shell"]):
        return "🛠 开发工具/DevOps"
    elif any(k in combined for k in ["rust", "go", "python", "typescript", "compiler",
                                      "framework", "library", "sdk", "api"]):
        return "🔧 框架/库"
    elif any(k in combined for k in ["data", "database", "analytics", "visualization",
                                      "pipeline", "etl", "streaming"]):
        return "📊 数据/分析"
    elif any(k in combined for k in ["security", "privacy", "crypto"]):
        return "🔐 安全"
    else:
        return "📦 其他"


def generate_report():
    print("🐙 **GitHub 热门项目简报**", end="\n\n")

    errors = []

    # 1. 本周新晋热门 (创建7天内 + 星星) — 最容易失败的板块
    print("🆕 **本周新晋热门**")
    new_repos, err = search_new_repos(days=7, limit=10)
    if new_repos:
        seen = set()
        count = 0
        for r in new_repos:
            name = r.get("full_name", "")
            if name in seen:
                continue
            seen.add(name)
            stars = r.get("stargazers_count", 0)
            if stars < 10:
                continue
            desc = (r.get("description") or "暂无描述")[:50]
            print(f"- **{name}** ⭐{format_stars(stars)} | {desc}")
            count += 1
            if count >= 5:
                break
        if count == 0:
            print("  _(本周暂无值得关注的新项目)_")
    else:
        errors.append(f"本周新晋热门: {err}")
        print(f"  ⚠️ API 获取失败 ({err})")
    print()

    # 2. 近30天热门 (按星数)
    print("🔥 **近30天热门 (按星数)**")
    recent, err = search_new_repos(days=30, limit=10)
    if recent:
        seen = set()
        count = 0
        for r in recent:
            name = r.get("full_name", "")
            if name in seen:
                continue
            seen.add(name)
            stars = r.get("stargazers_count", 0)
            desc = (r.get("description") or "暂无描述")[:50]
            lang = r.get("language", "")
            lang_str = f" [{lang}]" if lang else ""
            print(f"- **{name}** ⭐{format_stars(stars)}{lang_str}")
            if desc and desc != "暂无描述":
                print(f"  {desc}")
            count += 1
            if count >= 5:
                break
    else:
        errors.append(f"近30天热门: {err}")
        print(f"  ⚠️ API 获取失败 ({err})")
    print()

    # 3. AI/Agent 领域新品 (近30天) — 用固定日期避免动态计算漂移
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    print("🤖 **AI/Agent 新品 (近30天)**")
    ai_data, err = github_api("/search/repositories", {
        "q": f"ai agent OR llm agent OR agent framework OR mcp server in:name,description created:>{thirty_days_ago}",
        "sort": "stars", "order": "desc", "per_page": "5"
    }, timeout=45)
    all_repos = ai_data.get("items", []) if ai_data else []

    if all_repos:
        seen = set()
        count = 0
        for r in all_repos:
            name = r.get("full_name", "")
            if name in seen:
                continue
            seen.add(name)
            stars = r.get("stargazers_count", 0)
            if stars < 100:
                continue
            desc = (r.get("description") or "暂无描述")[:50]
            print(f"- **{name}** ⭐{format_stars(stars)} | {desc}")
            count += 1
            if count >= 3:
                break
    else:
        errors.append(f"AI新品: {err}")
        print(f"  ⚠️ API 获取失败 ({err})")
    print()

    # 错误汇总
    if errors:
        print("---")
        print(f"⚠️ 以下板块获取失败 ({len(errors)}/{3}):")
        for e in errors:
            print(f"  - {e}")
        print()

    print(f"📅 更新于 {datetime.now().strftime('%Y-%m-%d %H:%M')} CST")


if __name__ == "__main__":
    generate_report()
