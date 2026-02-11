# Nano Banana Image Generation Skill

## 概述

使用 nanobanana 反向代理生成图片，支持 gemini-3-pro-image 等模型。

## 安装

```bash
uv pip install openai pillow
```

## 使用方法

### 命令行

```bash
# 基本用法
python3 scripts/nanobanana_gen.py --prompt "你的提示词"

# 指定输出
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --output my_image.png

# 指定尺寸 (宽x高)
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --size "1024x1024"

# 使用预设宽高比
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --aspect_ratio 16:9

# 使用标准分辨率
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --resolution 4K

# 指定宽和高
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --width 1920 --height 1080

# 指定输出格式
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --format png

# 高质量模式
python3 scripts/nanobanana_gen.py --prompt "赛博朋克城市" --quality hd

# 批量生成
python3 scripts/nanobanana_gen.py --prompts "词1" "词2" "词3"

# 交互模式
python3 scripts/nanobanana_gen.py --interactive
```

### Python 调用

```python
from scripts.nanobanana_gen import NanoBanana

client = NanoBanana()

# 生成图片
image = client.generate(
    prompt="未来主义城市，霓虹灯，赛博朋克风格",
    size="1920x1080",  # WxH 格式或预设
    quality="hd"       # standard | hd | medium
)

# 保存图片
image.save("output.png")

# 批量生成
client.batch_generate(
    prompts=["提示词1", "提示词2"],
    size="16:9",
    quality="hd",
    output_dir="output",
    output_format="png"
)
```

## 尺寸参数

### 宽高比预设

| 参数 | 尺寸 |
|------|------|
| `1:1` | 1024x1024 |
| `4:3` | 1024x768 |
| `3:4` | 768x1024 |
| `16:9` | 1920x1080 |
| `9:16` | 1080x1920 |
| `21:9` | 1920x820 |
| `3:2` | 1536x1024 |
| `2:3` | 1024x1536 |
| `2:1` | 2048x1024 |
| `1:2` | 1024x2048 |

### 标准分辨率

| 参数 | 尺寸 |
|------|------|
| `sd` | 640x360 |
| `hd` | 1280x720 |
| `fhd` | 1920x1080 |
| `2k` | 2560x1440 |
| `4k` | 3840x2160 |
| `8k` | 7680x4320 |

### 自定义尺寸

支持任意 `WxH` 格式：
- `1920x1080`
- `1024x1024`
- `800x600`
- `4096x4096` (最大支持)

## 输出格式

- `png` (默认)
- `jpeg` / `jpg`
- `webp`

## 输出位置

默认输出到项目目录：
```
/home/liujerry/moltbot/output/nanobanana/
```

## 配置

环境变量：
- `NANOBANANA_API_KEY`: API密钥（默认: sk-antigravity）
- `NANOBANANA_BASE_URL`: API地址（默认: http://127.0.0.1:8045/v1）

## 支持的模型

- `gemini-3-pro-image` (默认)
- `gemini-3-pro-image-1x1`
- `gemini-3-pro-image-16x9`
- `gemini-3-pro-image-21x9`
- `gemini-3-pro-image-4k`
- 等

## 注意事项

- nanobanica 使用反向代理，API 格式与 OpenAI 兼容
- 最大支持 4096x4096 尺寸
- 建议使用 hd 质量获得最佳效果
