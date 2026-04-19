# MiniMax 视频生成 (Hailuo-2.3)

用 MiniMax API 生成视频（文生视频、图生视频）。

## 触发条件

用户想用 MiniMax 生成视频、图片、语音、音乐，或用 MiniMax 模型聊天。

---

## 方法一：mmx CLI（推荐）

MiniMax 官方 CLI 工具，已集成到 OpenClaw skills。

### 安装

```bash
npm install -g mmx-cli
mmx auth login --api-key "$MINIMAX_API_KEY"
mmx auth status  # 验证
```

### OpenClaw skill 安装（agent 自动加载）

```bash
npx skills add MiniMax-AI/cli -y
# skill doc: ~/hermes-agent/.agents/skills/mmx-cli/SKILL.md
```

### 常用命令

```bash
mmx video generate --prompt "描述" --download out.mp4 --quiet
mmx text chat --message "你好" --model MiniMax-M2.7 --output json
mmx image generate --prompt "描述" --out-dir ./gen/
mmx speech synthesize --text "文字" --out audio.mp3
mmx music generate --prompt "风格描述" --instrumental --out music.mp3
mmx quota show --output json   # 查看 Token Plan 配额
```

### 视频生成（异步模式）

```bash
# 获取 task ID
mmx video generate --prompt "A robot." --async --quiet
# -> {"taskId":"..."}

# 查询状态
mmx video task get --task-id <id> --output json

# 下载
mmx video download --file-id <id> --out robot.mp4
```

### ⚠️ Token Plan 视频配额

- **Token Plan 不含视频**：`mmx video` 返回 `exit code 4`
  ```
  "This model is not available on your current Token Plan.
   MiniMax-Hailuo-2.3-6s-768p requires Max plan or above"
  ```
- 查看配额：`mmx quota show`（视频行显示 `0 / 0` 即无配额）
- 升级：https://platform.minimaxi.com/subscribe/token-plan

---

## 方法二：直接调用 API

### 核心端点

- API Base: `https://api.minimax.chat`
- 创建任务: `POST /v1/video_generation`
- 查询状态: `GET /v1/video_generation_query?task_id=xxx`
- 下载视频: `GET /v1/video_generation_download?task_id=xxx`

### 模型（已验证）

| 模型名                            | 状态                     | 说明         |
| --------------------------------- | ------------------------ | ------------ |
| `MiniMax-Hailuo-2.3-6s-768p`      | Token Plan 不支持 (2061) | 需 Max 套餐  |
| `MiniMax-Hailuo-2.3-Fast-6s-768p` | Token Plan 不支持 (2061) | 需 Max 套餐  |
| `Video-01` / `Video-01-live2d`    | Token Plan 不支持 (2061) | 需 Max 套餐  |
| `T2V-01` / `S2V-01` / `I2V-01`    | Token Plan 不支持 (2061) | 需 Max 套餐  |
| `hailuo-02` / `hailuo-01`         | 错误 2013（参数错误）    | 模型名已改名 |

## 必需工具

- `requests` 或 `httpx` — HTTP 调用（已安装）
- `ffmpeg` — 视频处理（已安装）
- MiniMax API Key — 从 `~/.hermes/.env` 读取 `MINIMAX_API_KEY`

## 工作流程

### 1. 创建视频生成任务

```python
import requests, os, time, json

API_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL = "https://api.minimax.chat/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 文生视频
payload = {
    "model": "hailuo-02",
    "prompt": "你的视频描述",
    "duration": 6,  # 6秒
    "resolution": "1080p",
    "fps": 30,
}

resp = requests.post(
    f"{BASE_URL}/video_generation",
    headers=headers,
    json=payload,
    timeout=30,
)
data = resp.json()
print(data)
# -> {"base_resp": {"status_code": 0, ...}, "task_id": "xxx"}

task_id = data.get("task_id")
if not task_id:
    print(f"创建失败: {data}")
    return
```

### 2. 轮询任务状态（每 10 秒，最多 5 分钟）

```python
for i in range(30):
    time.sleep(10)
    resp = requests.get(
        f"{BASE_URL}/video_generation_query",
        headers=headers,
        params={"task_id": task_id},
        timeout=10,
    )
    data = resp.json()
    status = data.get("status", "")
    print(f"[{i+1}] 状态: {status}")

    if status == "success":
        video_url = data.get("data", {}).get("video_url")
        print(f"完成: {video_url}")
        break
    elif status in ("fail", "error"):
        print(f"失败: {data}")
        break
```

### 3. 下载视频到本地

```python
import urllib.request

output_path = f"/tmp/hailuo_{task_id}.mp4"
urllib.request.urlretrieve(video_url, output_path)
print(f"已保存: {output_path}")
```

## 完整示例脚本

见 `scripts/generate_video.py`

## 输出格式

- 分辨率: 1080p (默认), 720p
- 时长: 6秒 (默认), 可选 6/10/15 秒（取决于模型）
- 格式: MP4 (h.264)
- FPS: 30

## ⚠️ Token Plan 限制

**当前 Token Plan 不包含视频生成模型。**

```
错误码 2061: your current token plan not support model, MiniMax-Hailuo-02-6s-768p
```

视频生成需要单独订阅，见：

- https://platform.minimaxi.com/subscribe/token-plan （找含视频的套餐）
- https://platform.minimaxi.com/docs/guides/pricing-video （按量付费）

**已测试可用的模型（需单独订阅）：**

- `MiniMax-Hailuo-02-6s-768p` — 最新模型
- `Video-01` / `Video-01-live2d` — 旧版
- `T2V-01` / `S2V-01` / `I2V-01` — 各类型

## 价格参考

- hailuo-02: ~¥0.05-0.1/秒（按量）
- 具体价格查上述定价页面

## 常见错误

- `1004 login fail` — API Key 无效或格式错误
- `1001 rate limit` — 请求过于频繁，等一下再试
- `status: fail` — 任务失败，看 `err` 字段

## 后期处理（可选）

用 FFmpeg 添加字幕、剪辑：

```bash
ffmpeg -i input.mp4 -vf "subtitles=subs.srt" -c:a copy output_with_subs.mp4
```
