# Local Image Generation Skill

本地图片生成技能，使用 Antigravity 反向代理生成图片。

## 概述

使用本地 127.0.0.1:8045 的 Antigravity 反向代理，通过 OpenAI 兼容 API 生成图片。

## 安装

```bash
uv pip install openai pillow
```

## 使用方法

### 命令行

```bash
# 生成单张图片
python3 scripts/image_gen.py --prompt "一座未来主义风格的城市"

# 指定尺寸
python3 scripts/image_gen.py --prompt "一只可爱的猫咪" --size "1920x1080"

# 使用预设宽高比
python3 scripts/image_gen.py --prompt "赛博朋克城市" --aspect_ratio 16:9

# 使用标准分辨率
python3 scripts/image_gen.py --prompt "高清风景" --resolution 4k

# 指定输出格式
python3 scripts/image_gen.py --prompt "可爱动物" --format png

# 批量生成
python3 scripts/image_gen.py --prompts "词1" "词2" "词3"
```

### Python 调用

```python
from scripts.image_gen import LocalImageGenerator

generator = LocalImageGenerator()

# 生成单张图片
image = generator.generate(
    prompt="一座未来主义风格的城市，赛博朋克，霓虹灯",
    size="1920x1080",  # WxH 格式或预设
    quality="hd"         # standard | hd | medium
)

# 保存图片
image.save("output.png")

# 批量生成
generator.batch_generate(
    prompts=["提示词1", "提示词2"],
    size="16:9",
    output_dir="output"
)
```

## 尺寸参数

### 宽高比预设

| 参数 | 尺寸 |
|------|------|
| `1:1` | 1024x1024 |
| `4:3` | 1024x768 |
| `16:9` | 1920x1080 |
| `9:16` | 1080x1920 |
| `21:9` | 1920x820 |

### 标准分辨率

| 参数 | 尺寸 |
|------|------|
| `sd` | 640x360 |
| `hd` | 1280x720 |
| `fhd` | 1920x1080 |
| `2k` | 2560x1440 |
| `4k` | 3840x2160 |

### 自定义尺寸

支持任意 `WxH` 格式：
- `1920x1080`
- `1024x1024`
- `800x600`

## 输出格式

- `png` (默认)
- `jpeg` / `jpg`
- `webp`

## 输出位置

默认输出到项目目录：
```
/home/liujerry/moltbot/output/local-image-generation/
```

## 配置

环境变量：
- `LOCAL_IMAGE_API_KEY`: API密钥（默认: sk-antigravity）
- `LOCAL_IMAGE_BASE_URL`: API地址（默认: http://127.0.0.1:8045/v1）

## 支持的模型

- `gemini-3-pro-image` (默认)
- `gemini-3-pro-image-4k-16x9`
- `gemini-3-pro-image-1x1`
- `gemini-3-pro-image-9x16`

## 命令行参数

```
python3 scripts/image_gen.py [OPTIONS]

Options:
  --prompt, -p       单张图片提示词
  --prompts, -P      批量提示词列表
  --output, -o       输出文件路径 (默认: output.png)
  --output_dir, -d   批量输出目录 (默认: output)
  --size, -s         图片尺寸，支持 WxH 格式或预设 (默认: 1920x1080)
  --width            图片宽度 (与 --height 一起使用)
  --height           图片高度 (与 --width 一起使用)
  --aspect_ratio, -a 预设宽高比
  --resolution, -r   标准分辨率
  --quality, -q      图片质量 (默认: hd)
  --format, -f       输出格式 (默认: png)
  --interactive, -i  交互模式
  --api_key          API密钥
  --base_url         API地址
  --model, -m        模型名称 (默认: gemini-3-pro-image)
  --help             显示帮助
```

## 注意事项

- 使用 Antigravity 反向代理，API 格式与 OpenAI 兼容
- 最大支持 4096x4096 尺寸
- 建议使用 hd 质量获得最佳效果
- 注意每日图片生成额度限制
