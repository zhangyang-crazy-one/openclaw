# MiniMax API Reference

## Verified Endpoints (2026-04-20)

| Capability       | Endpoint                    | Model           | Status  |
| ---------------- | --------------------------- | --------------- | ------- |
| Image generation | `POST /v1/image_generation` | `image-01`      | Working |
| Text-to-speech   | `POST /v1/t2a_v2`           | `speech-2.8-hd` | Working |
| Background music | `POST /v1/music_generation` | `music-2.6`     | Async   |

**Base URL:** `https://api.minimax.chat/v1`
**Auth:** `Authorization: Bearer {MINIMAX_API_KEY}`

## Image Generation (image-01)

```json
POST /v1/image_generation
{
  "model": "image-01",
  "prompt": "English prompt — be specific, include style + lighting + mood",
  "aspect_ratio": "16:9"
}
```

Response: `{ "data": { "image_urls": ["https://..."] } }`

**Critical:** URLs expire within minutes — download immediately.

### Character Reference (img2img)

For consistent characters across scenes, use `image_url` parameter for img2img:

```json
POST /v1/image_generation
{
  "model": "image-01",
  "prompt": "The orange tabby cat (from reference) standing on a grassy hilltop...",
  "aspect_ratio": "16:9",
  "image_url": "https://example.com/character_reference.jpg"
}
```

## Text-to-Speech (speech-2.8-hd)

```json
POST /v1/t2a_v2
{
  "model": "speech-2.8-hd",
  "text": "Chinese narration — short sentences, natural pacing",
  "voice_setting": {
    "voice_id": "male-qn-qingse",
    "speed": 10,
    "pitch": 0,
    "vol": 10
  }
}
```

Response: `{ "data": { "audio": "<hex_encoded>" } }`

### Voice IDs

| ID               | Voice    | Best For             |
| ---------------- | -------- | -------------------- |
| `male-qn-qingse` | 青年男声 | 纪录片、叙述、科技   |
| `female-tianmei` | 甜妹     | 生活方式、可爱、轻松 |
| `male-shaonian`  | 少年     | 青春、活力           |
| `female-shaonv`  | 少女     | 清新、自然           |
| `male-yuanbing`  | 渊冰     | 深沉、史诗、严肃     |
| `female-zhiqi`   | 知沁     | 知性、温和、教学     |

**Speed/pitch/vol are int (x10):** speed=1.0 → 10, pitch=0 → 0, vol=1.0 → 10

## Background Music (music-2.6) — Async

```json
POST /v1/music_generation
{
  "model": "music-2.6",
  "prompt": "Epic orchestral with electronic elements",
  "lyrics": "la la la\nla la la"
}
```

Returns `task_id` → poll `/v1/query/task` → `status==2` = complete.

**Note:** music-2.6 requires `lyrics` field. music-2.5+ supports `is_instrumental` but Token Plan may not support it.

## Python API (`scripts/minimax_api.py`)

```python
from minimax_api import generate_image, generate_speech, generate_music, generate_scene_assets

# Single image
img_path = generate_image(
    prompt="Cinematic scene: ancient library...",
    output_dir="./public/scenes",
    aspect_ratio="16:9"
)

# TTS
audio_path = generate_speech(
    text="在信息的海洋深处，有些东西正在苏醒。",
    output_dir="./public/audio",
    voice_id="male-qn-qingse"
)

# Batch (parallel, concurrent)
assets = generate_scene_assets(scenes, output_base="./public")
```
