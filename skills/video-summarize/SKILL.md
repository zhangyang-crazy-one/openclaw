---
name: video-summarize
description: Summarize video content using Minimax API. Supports Bilibili, YouTube, and other video platforms.
metadata: { "openclaw": { "emoji": "🎬", "requires": { "bins": ["curl"] } } }
---

# Video Summarize

使用 Minimax API 分析视频内容并生成总结。

## 支持平台

- Bilibili（哔哩哔哩）
- YouTube
- 其他网页视频

## 使用方法

### 命令行

```bash
# 总结 B 站视频
python3 /home/liujerry/moltbot/skills/video-summarize/summarize.py "https://b23.tv/xxx"

# 总结 YouTube
python3 /home/liujerry/moltbot/skills/video-summarize/summarize.py "https://youtube.com/watch?v=xxx"
```

### 直接调用函数

```python
from summarize import summarize_video
result = summarize_video("https://b23.tv/xxx")
print(result)
```

## 配置

API Key 从 `~/.bashrc` 自动读取：

```bash
export MINIMAX_API_KEY="sk-cp-..."
```

## 输出示例

```
==================================================
视频内容总结
==================================================

本视频介绍如何利用 Claude Code 搭配 Obsidian 笔记软件，
构建自动化论文阅读工作流...

```

## 触发词

当用户说：

- "总结这个视频"
- "视频内容是什么"
- "这个视频讲了什么"
