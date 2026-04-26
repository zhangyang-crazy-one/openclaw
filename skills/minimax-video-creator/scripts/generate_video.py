#!/usr/bin/env python3
"""
MiniMax 视频生成脚本 - Hailuo-2.3

⚠️ 注意：MiniMax Token Plan 不包含视频生成配额。
调用前先 `mmx quota show` 确认有配额，或升级到 Max 套餐。
见 SKILL.md 中的「⚠️ Token Plan 视频配额」章节。
用法:
  python3 generate_video.py "一个宇航员在火星上行走，电影级画面"  [--duration 6] [--output /tmp/video.mp4]
  python3 generate_video.py --image /path/to/image.jpg "宇航员走向镜头" [--duration 6]
  python3 generate_video.py --i2v "宇航员走向镜头" --image-url https://... [--duration 6]
"""

import requests, os, sys, time, json, argparse
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
BASE_URL = "https://api.minimax.chat/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
OUTPUT_DIR = Path.home() / "视频生成"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 工具函数 ──────────────────────────────────────────
def create_task(prompt: str, duration: int = 6, model: str = "MiniMax-Hailuo-02-6s-768p",
                image_url: str = None, first_frame_url: str = None,
                last_frame_url: str = None) -> str:
    """创建视频生成任务，返回 task_id"""
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
    }
    if image_url:
        payload["image_url"] = image_url
    if first_frame_url:
        payload["first_frame_url"] = first_frame_url
    if last_frame_url:
        payload["last_frame_url"] = last_frame_url

    resp = requests.post(
        f"{BASE_URL}/video_generation",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    data = resp.json()
    base = data.get("base_resp", {})
    if base.get("status_code") != 0:
        raise RuntimeError(f"创建任务失败: {base.get('status_msg', base)}")
    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"无 task_id: {data}")
    return task_id


def query_task(task_id: str) -> dict:
    """查询任务状态"""
    resp = requests.get(
        f"{BASE_URL}/video_generation_query",
        headers=HEADERS,
        params={"task_id": task_id},
        timeout=10,
    )
    return resp.json()


def wait_for_video(task_id: str, poll_sec: int = 10, max_wait_sec: int = 300) -> str:
    """轮询直到视频就绪，返回 video_url"""
    elapsed = 0
    while elapsed < max_wait_sec:
        data = query_task(task_id)
        status = data.get("status", "")
        print(f"  [{elapsed}s] status={status}")
        if status == "success":
            video_url = data.get("data", {}).get("video_url", "")
            print(f"  ✓ 视频就绪: {video_url}")
            return video_url
        elif status in ("fail", "error", "FAILED"):
            raise RuntimeError(f"任务失败: {data}")
        time.sleep(poll_sec)
        elapsed += poll_sec
    raise TimeoutError(f"等待超时 ({max_wait_sec}s)")


def download_video(video_url: str, output_path: str) -> str:
    """下载视频到本地"""
    import urllib.request
    urllib.request.urlretrieve(video_url, output_path)
    size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  ✓ 已下载: {output_path} ({size:.1f} MB)")
    return output_path


# ── 主流程 ─────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="MiniMax hailuo-02 视频生成")
    p.add_argument("prompt", nargs="?", help="视频描述文字")
    p.add_argument("--duration", type=int, default=6, help="时长(秒)，默认6")
    p.add_argument("--model", default="MiniMax-Hailuo-02-6s-768p", help="模型，默认 MiniMax-Hailuo-02-6s-768p")
    p.add_argument("--output", help="输出路径")
    p.add_argument("--image", help="图片路径 (图生视频 / I2V)")
    p.add_argument("--image-url", help="图片 URL (图生视频)")
    p.add_argument("--first-frame", help="首帧图片 URL (首尾帧视频)")
    p.add_argument("--last-frame", help="尾帧图片 URL (首尾帧视频)")
    p.add_argument("--no-poll", action="store_true", help="创建后立即返回，不等待")
    args = p.parse_args()

    if not args.prompt:
        p.print_help()
        sys.exit(1)

    if not API_KEY:
        print("错误: 未设置 MINIMAX_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)

    # 图生视频处理
    image_url = None
    if args.image:
        # 上传图片到可访问 URL（这里假设是本地文件路径，需要先上传）
        # 简化处理：直接传本地路径给 image_url
        image_url = args.image
    if args.image_url:
        image_url = args.image_url

    print(f"[MiniMax hailuo-02] 提示词: {args.prompt[:60]}...")
    print(f"  模型={args.model}, 时长={args.duration}s")

    # 1. 创建任务
    print("\n[1/3] 创建生成任务...")
    task_id = create_task(
        prompt=args.prompt,
        duration=args.duration,
        model=args.model,
        image_url=image_url,
        first_frame_url=args.first_frame,
        last_frame_url=args.last_frame,
    )
    print(f"  task_id = {task_id}")

    # 2. 等待/轮询
    print("\n[2/3] 等待生成...")
    if args.no_poll:
        print(f"  (跳过轮询，task_id={task_id})")
        print(f"\n查询状态: curl '{BASE_URL}/video_generation_query?task_id={task_id}' \\")
        print(f"  -H 'Authorization: Bearer $MINIMAX_API_KEY'")
        sys.exit(0)

    video_url = wait_for_video(task_id)

    # 3. 下载
    print("\n[3/3] 下载视频...")
    ts = time.strftime("%Y%m%d_%H%M%S")
    default_name = f"hailuo_{args.model}_{ts}.mp4"
    output_path = args.output or str(OUTPUT_DIR / default_name)
    download_video(video_url, output_path)

    print(f"\n✓ 完成: {output_path}")


if __name__ == "__main__":
    main()
