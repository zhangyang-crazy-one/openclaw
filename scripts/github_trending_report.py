#!/usr/bin/env python3
"""
GitHub Trending 简报生成脚本 v4
策略：多维度发现 — trending + 近期高星 + 快速增长
增强 (2026-06-04 v4):
  - checkpoint 落盘 ~/.cache/github_trending_partial.json
  - 单次 API 超时砍到 8s (符合 cron 380s 包装)
  - 退避砍半 BASE_DELAY 5s
  - 每成功获取一个 section 立即落盘 (崩了也能复用)
  - 支持 --resume 从 checkpoint 继续
  - 软超时 360s 整体 (cron outer timeout 380s)
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PROXY = "http://127.0.0.1:7897"
MAX_RETRIES = 2  # 从 3 砍到 2
BASE_DELAY = 5  # 从 10 砍到 5
API_TIMEOUT = 8  # 从 30 砍到 8 (符合 prompt "8s 放弃")
SEARCH_TIMEOUT = 15  # 大查询用 15s (从 60 砍)
SOFT_TIMEOUT_S = 360  # 整体软超时

CACHE_DIR = Path.home() / ".cache"
CHECKPOINT_PATH = CACHE_DIR / "github_trending_partial.json"
START_TS = time.time()

# ---- 软超时 ----
def _soft_timeout_handler(signum, frame):
    raise TimeoutError(f"soft timeout after {SOFT_TIMEOUT_S}s")

signal.signal(signal.SIGALRM, _soft_timeout_handler)
signal.alarm(SOFT_TIMEOUT_S)


def elapsed() -> float:
    return time.time() - START_TS


def remaining() -> float:
    return max(0, SOFT_TIMEOUT_S - elapsed())


# ---- checkpoint ----
def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH) as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_checkpoint(partial: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(partial, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CHECKPOINT_PATH)  # atomic


# ---- GitHub API ----
def github_api(path, params=None, timeout=API_TIMEOUT, quiet=False):
    """
    调用 GitHub API (走代理)，带重试+指数退避+8s 单次超时。
    返回 (data_or_None, error_message_or_None)
    """
    from urllib.parse import urlencode
    url = f"https://api.github.com{path}"
    if params:
        qs = urlencode(params)
        url += f"?{qs}"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        # 检查剩余时间
        if remaining() < 15:
            return None, f"soft timeout ({elapsed():.0f}s)"

        try:
            result = subprocess.run(
                ["curl", "-s", "-x", PROXY, "--max-time", str(timeout),
                 "--connect-timeout", "5",
                 "-H", "Accept: application/vnd.github+json",
                 "-H", "User-Agent: Mozilla/5.0",
                 url],
                capture_output=True, text=True, timeout=timeout + 5
            )

            if result.returncode != 0:
                last_error = f"curl exit={result.returncode}"
                _maybe_sleep(attempt, last_error, quiet)
                continue

            raw = result.stdout.strip()
            if not raw:
                last_error = "empty response"
                _maybe_sleep(attempt, last_error, quiet)
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                last_error = "JSON parse error"
                _maybe_sleep(attempt, last_error, quiet)
                continue

            # GitHub rate limit
            if isinstance(data, dict) and "message" in data:
                msg = data["message"]
                if "rate limit" in msg.lower() or "403" in msg:
                    last_error = f"rate limited: {msg[:50]}"
                    _maybe_sleep(attempt, last_error, quiet, rate_limit=True)
                    continue
                else:
                    last_error = f"API: {msg[:50]}"
                    _maybe_sleep(attempt, last_error, quiet)
                    continue

            return data, None

        except subprocess.TimeoutExpired:
            last_error = f"subprocess timeout ({timeout}s)"
            _maybe_sleep(attempt, last_error, quiet)
        except Exception as e:
            last_error = str(e)[:80]
            _maybe_sleep(attempt, last_error, quiet)

    return None, last_error


def _maybe_sleep(attempt, err, quiet, rate_limit=False):
    if attempt >= MAX_RETRIES:
        return
    delay = BASE_DELAY * (2 ** (attempt - 1))
    if rate_limit:
        delay *= 2
    if not quiet:
        print(f"  ⚠️ {err} (尝试 {attempt}/{MAX_RETRIES}, {delay}s 后重试, 剩余 {remaining():.0f}s)",
              file=sys.stderr)
    time.sleep(min(delay, max(0, remaining() - 5)))


# ---- 业务查询 ----
def format_stars(n):
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def search_new_repos(days=7, limit=10):
    """搜索最近N天创建的热门仓库"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    data, err = github_api("/search/repositories", {
        "q": f"created:>{since}",
        "sort": "stars",
        "order": "desc",
        "per_page": str(limit)
    }, timeout=SEARCH_TIMEOUT)
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
        }, timeout=API_TIMEOUT)
        if data:
            repos.extend(data.get("items", [])[:limit])
        if remaining() < 15:
            break
    return repos


# ---- 格式化输出 ----
def render_repos_section(title, repos, max_count=5, require_min_stars=None, with_lang=False):
    """渲染一个 section；返回 (lines, error_or_None)"""
    lines = [f"### {title}"]
    if not repos:
        return lines, "no data"
    seen = set()
    count = 0
    for r in repos:
        name = r.get("full_name", "")
        if not name or name in seen:
            continue
        seen.add(name)
        stars = r.get("stargazers_count", 0)
        if require_min_stars and stars < require_min_stars:
            continue
        desc = (r.get("description") or "暂无描述")[:50]
        lang = r.get("language", "")
        lang_str = f" [{lang}]" if (with_lang and lang) else ""
        lines.append(f"- **{name}** ⭐{format_stars(stars)}{lang_str}")
        if desc and desc != "暂无描述" and with_lang:
            lines.append(f"  {desc}")
        count += 1
        if count >= max_count:
            break
    if count == 0:
        lines.append("  _(无符合条件项)_")
    return lines, None


# ---- 主流程 ----
def generate_report(resume=False):
    print("🐙 **GitHub 热门项目简报**", end="\n\n")
    if resume:
        print("_(从 checkpoint 恢复)_", end="\n\n")

    cp = load_checkpoint() if resume else {}
    errors = []

    # === 1. 本周新晋热门 ===
    if "new_7d" in cp:
        print(f"  ↻ [checkpoint] 复用 7d 数据 ({len(cp['new_7d'])} repos)")
        new_repos = cp["new_7d"]
        err = cp.get("new_7d_err")
    else:
        print("🆕 **本周新晋热门**")
        new_repos, err = search_new_repos(days=7, limit=10)
        cp["new_7d"] = new_repos
        cp["new_7d_err"] = err
        save_checkpoint(cp)
    if err and not new_repos:
        errors.append(f"本周新晋热门: {err}")
        print(f"  ⚠️ API 获取失败 ({err})")
    else:
        lines, _ = render_repos_section("🆕 本周新晋热门", new_repos, max_count=5, require_min_stars=10)
        print("\n".join(lines))
    print()

    if remaining() < 30:
        return _finish(errors, early=True)

    # === 2. 近30天热门 ===
    if "new_30d" in cp:
        print(f"  ↻ [checkpoint] 复用 30d 数据 ({len(cp['new_30d'])} repos)")
        recent = cp["new_30d"]
        err = cp.get("new_30d_err")
    else:
        print("🔥 **近30天热门 (按星数)**")
        recent, err = search_new_repos(days=30, limit=10)
        cp["new_30d"] = recent
        cp["new_30d_err"] = err
        save_checkpoint(cp)
    if err and not recent:
        errors.append(f"近30天热门: {err}")
        print(f"  ⚠️ API 获取失败 ({err})")
    else:
        lines, _ = render_repos_section("🔥 近30天热门", recent, max_count=5, with_lang=True)
        print("\n".join(lines))
    print()

    if remaining() < 30:
        return _finish(errors, early=True)

    # === 3. AI/Agent 新品 ===
    if "ai_30d" in cp:
        print(f"  ↻ [checkpoint] 复用 AI 数据 ({len(cp['ai_30d'])} repos)")
        ai_repos = cp["ai_30d"]
        err = cp.get("ai_30d_err")
    else:
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        print("🤖 **AI/Agent 新品 (近30天)**")
        ai_data, err = github_api("/search/repositories", {
            "q": f"ai agent OR llm agent OR agent framework OR mcp server in:name,description created:>{thirty_days_ago}",
            "sort": "stars", "order": "desc", "per_page": "5"
        }, timeout=SEARCH_TIMEOUT)
        ai_repos = ai_data.get("items", []) if ai_data else []
        cp["ai_30d"] = ai_repos
        cp["ai_30d_err"] = err
        save_checkpoint(cp)
    if err and not ai_repos:
        errors.append(f"AI新品: {err}")
        print(f"  ⚠️ API 获取失败 ({err})")
    else:
        lines, _ = render_repos_section("🤖 AI/Agent 新品", ai_repos, max_count=3, require_min_stars=100)
        print("\n".join(lines))
    print()

    return _finish(errors)


def _finish(errors, early=False):
    if errors:
        print("---")
        print(f"⚠️ 以下板块获取失败 ({len(errors)}/3):")
        for e in errors:
            print(f"  - {e}")
        print()
    if early:
        print(f"⏱️ 软超时提前结束 (用了 {elapsed():.0f}s / {SOFT_TIMEOUT_S}s)")
    print(f"📅 更新于 {datetime.now().strftime('%Y-%m-%d %H:%M')} CST")
    # 完成后保留 checkpoint 24h, 24h 后下次跑新数据
    # 不在这里删, 让 --resume 机制能复用同一天数据


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    parser.add_argument("--clear-cache", action="store_true", help="清空 checkpoint")
    args = parser.parse_args()

    if args.clear_cache:
        if CHECKPOINT_PATH.exists():
            CHECKPOINT_PATH.unlink()
            print(f"✅ 已清空 {CHECKPOINT_PATH}")
        sys.exit(0)

    try:
        generate_report(resume=args.resume)
    except TimeoutError as e:
        print(f"\n⏱️ {e}", file=sys.stderr)
        sys.exit(124)  # 124 = timeout convention
