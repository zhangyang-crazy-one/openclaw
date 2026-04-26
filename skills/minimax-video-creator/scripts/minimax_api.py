#!/usr/bin/env python3
"""
MiniMax API 封装：图片生成 + TTS + 音乐
支持 image-01、speech-2.8-hd、music-2.6

关键发现（2026-04-20 网络调研）：
- TTS: model=speech-2.8-hd, voice_setting.voice_id 必填，返回 base64 音频
- Music: model=music-2.6, lyrics 必填（is_instrumental 只在 music-2.5+ 支持）
- Music 是异步接口，需通过 task_id 轮询 /v1/query/task 直到完成
"""

import os
import json
import time
import base64
import urllib.request
from pathlib import Path
from typing import Optional

# ============================================================
# 配置
# ============================================================
def _get_env(key: str, default: str = "") -> str:
    """从 ~/.hermes/.env 读取环境变量"""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip()
    return os.environ.get(key, default)


BASE_URL = "https://api.minimax.chat/v1"
API_KEY = _get_env("MINIMAX_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def _post(endpoint: str, payload: dict, timeout: int = 60):
    """发送 POST 请求，返回 parsed JSON"""
    url = f"{BASE_URL}{endpoint}"
    data_bytes = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data_bytes, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _poll_task(task_id: str, timeout: int = 120, interval: int = 5) -> dict:
    """
    轮询 music 生成任务直到完成。
    返回最终结果 dict，包含 audio_url 或 audio_base64。
    timeout: 最大等待秒数
    """
    start = time.time()
    while time.time() - start < timeout:
        result = _post("/query/task", {"task_id": task_id}, timeout=15)
        status = result.get("status") or result.get("data", {}).get("status")
        if status == 2:  # SUCCESS
            return result
        elif status == 3:  # FAILED
            raise RuntimeError(f"Music generation failed: {result}")
        print(f"  等待音乐生成... ({int(time.time()-start)}s)")
        time.sleep(interval)
    raise TimeoutError(f"Music generation timed out after {timeout}s (task_id={task_id})")


# ============================================================
# 图片生成 (image-01)
# ============================================================
def generate_image(
    prompt: str,
    output_dir: str = ".",
    aspect_ratio: str = "16:9",
    resolution: Optional[str] = None,
) -> str:
    """
    调用 MiniMax image-01 生成图片，返回本地保存路径。
    """
    payload = {
        "model": "image-01",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
    }
    if resolution:
        payload["resolution"] = resolution

    data = _post("/image_generation", payload)

    # image-01 返回: { base_resp: {...}, data: { image_urls: ["..."] } }
    img_url = data["data"]["image_urls"][0]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "png" if "png" in img_url.lower() else "jpg"
    safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:40]).strip("_")
    filename = f"{safe_name}_{os.getpid()}.{ext}"
    filepath = out_dir / filename

    urllib.request.urlretrieve(img_url, filepath)
    return str(filepath)


# ============================================================
# TTS 语音 (speech-2.8-hd)
# ============================================================
def generate_speech(
    text: str,
    output_dir: str = ".",
    voice_id: str = "male-qn-qingse",
    speed: float = 1.0,
    pitch: float = 0.0,
    vol: float = 1.0,
    timeout: int = 60,
) -> str:
    """
    调用 MiniMax speech-2.8-hd 生成语音，同步返回 base64 → 保存为 MP3。
    返回本地保存路径。

    voice_id 可选（必填）:
      male-qn-qingse   男声-青年男声
      female-tianmei   女声-甜妹
      male-yuanbing    男声-渊冰
      female-zhiqi     女声-知沁
      male-shaonian    男声-少年
      female-shaonv    女声-少女
    """
    payload = {
        "model": "speech-2.8-hd",
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": int(speed * 10),   # 0.5~2.0 → 5~20 (int)
            "pitch": int(pitch * 10),   # -12~12 → -120~120 (int)
            "vol": int(vol * 10),       # 0~10 → 0~100 (int)
        },
    }

    result = _post("/t2a_v2", payload, timeout=timeout)

    audio_raw = result.get("data", {}).get("audio", "")
    if not audio_raw:
        raise RuntimeError(f"TTS API 返回无 audio 字段: {result}")

    # MiniMax TTS 返回 hex 编码（不是 base64），与 music-2.6 一致
    try:
        audio_bytes = bytes.fromhex(audio_raw)
    except ValueError:
        audio_bytes = base64.b64decode(audio_raw)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"speech_{abs(hash(text[:50])) % 100000:05d}.mp3"
    filepath = out_dir / filename

    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    return str(filepath)


# ============================================================
# 背景音乐 (music-2.6)
# ============================================================
def generate_music(
    prompt: str,
    output_dir: str = ".",
    lyrics: str = None,
    timeout: int = 180,
    poll_interval: int = 5,
) -> str:
    """
    调用 MiniMax music-2.6 生成背景音乐（异步，需轮询）。
    返回本地保存的 .mp3 文件路径。

    注意: music-2.6 强制要求 lyrics 参数！
    如需纯音乐，用 music-2.5+（需确认 Token Plan 支持）。

    lyrics 格式: 每句一行，用 \\n 分隔，如 "第一句歌词\\n第二句歌词"
    """
    # music-2.6 必须有 lyrics，music-2.5+ 支持 is_instrumental
    payload = {
        "model": "music-2.6",
        "prompt": prompt,
    }
    if lyrics:
        payload["lyrics"] = lyrics
    # 不发 is_instrumental，music-2.6 不支持该字段

    result = _post("/music_generation", payload, timeout=45)

    # 情况1: status=2 + audio 字段 = hex 编码的音频数据（同步返回，无需轮询）
    audio_hex = result.get("data", {}).get("audio", "")
    status = result.get("data", {}).get("status")
    if status == 2 and audio_hex:
        # MiniMax music-2.6 返回 hex 编码的二进制音频，不是 base64！
        audio_bytes = bytes.fromhex(audio_hex)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:40]).strip("_")
        filename = f"music_{safe_name}.mp3"
        filepath = out_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        return str(filepath)

    # 情况2: 有 music_url → 直接下载
    audio_url = result.get("data", {}).get("music_url") or result.get("data", {}).get("audio_url")
    if audio_url:
        return _download_and_save(audio_url, output_dir, prompt)

    # 情况3: 返回 task_id / music_id → 异步轮询
    task_id = (
        result.get("data", {}).get("music_id")
        or result.get("data", {}).get("task_id")
        or result.get("task_id")
    )
    if not task_id:
        raise RuntimeError(f"music_generation 解析失败（无 audio/status/music_id/task_id）: {result}")

    print(f"  Music task_id={task_id}，开始轮询...")
    final = _poll_task(task_id, timeout=timeout, interval=poll_interval)

    # 轮询完成后再次检查 audio 字段（可能仍是 hex 格式）
    audio_hex = final.get("data", {}).get("audio", "")
    if audio_hex:
        audio_bytes = bytes.fromhex(audio_hex)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:40]).strip("_")
        filename = f"music_{safe_name}.mp3"
        filepath = out_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        return str(filepath)

    audio_url = final.get("data", {}).get("music_url") or final.get("data", {}).get("audio_url")
    if not audio_url:
        raise RuntimeError(f"Music poll 完成但无 audio_url: {final}")
    return _download_and_save(audio_url, output_dir, prompt)


def _download_and_save(url: str, output_dir: str, prompt: str) -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:40]).strip("_")
    filename = f"music_{safe_name}.mp3"
    filepath = out_dir / filename
    urllib.request.urlretrieve(url, filepath)
    return str(filepath)


# ============================================================
# 批量生成场景素材
# ============================================================
def generate_scene_assets(
    scenes: list,
    output_base: str = "./public",
) -> list:
    """
    批量生成一组场景的图片+旁白。

    scenes: [{"image_prompt": "...", "narration": "...", "duration_seconds": 5}, ...]
    返回: [{"scene_id": 0, "image_path": "...", "audio_path": "...", "duration_frames": 150}, ...]
    """
    import concurrent.futures

    scenes_dir = Path(output_base) / "scenes"
    audio_dir = Path(output_base) / "audio"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    def gen_single(scene: dict, idx: int):
        img_path = generate_image(
            prompt=scene["image_prompt"],
            output_dir=str(scenes_dir),
        )
        audio_path = generate_speech(
            text=scene["narration"],
            output_dir=str(audio_dir),
        )
        duration_frames = scene.get("duration_seconds", 5) * 30
        return {
            "scene_id": idx,
            "image_path": img_path,
            "audio_path": audio_path,
            "duration_frames": duration_frames,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(gen_single, s, i): i for i, s in enumerate(scenes)}
        results = []
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    return sorted(results, key=lambda x: x["scene_id"])


if __name__ == "__main__":
    print("Testing image generation...")
    img = generate_image("A futuristic city at night with neon lights, cinematic")
    print(f"Image saved: {img}")

    print("\nTesting TTS...")
    audio = generate_speech("欢迎观看这个视频，让我们一起探索AI生成的精彩世界。")
    print(f"Audio saved: {audio}")
