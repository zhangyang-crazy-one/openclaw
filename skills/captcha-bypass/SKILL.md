---
name: captcha-bypass
description: 使用 ACP + Claude Code 自动分析和绕过滑块验证码。支持极验、腾讯防水墙等主流验证码平台。
user-invocable: true
---

# Captcha Bypass Skill

使用 Claude Code 分析并生成滑块验证码绕过代码。

## 功能

1. **目标分析** — 分析目标网站的验证码机制
2. **代码生成** — 生成 Python 绕过代码（缺口识别 + 轨迹模拟）
3. **本地验证** — 在本地测试绕过方案

## 依赖

- Claude Code CLI (`claude`)
- acpx (OpenClaw ACP 协议)
- Python 3.8+ with: `selenium`, `pillow`, `numpy`, `opencv-python`
- 浏览器驱动: `chromedriver` 或 `geckodriver`

## 使用方法

### 命令行

```bash
# 分析并生成绕过代码
python3 ~/moltbot/skills/captcha-bypass/bypass.py "https://example.com/login"

# 指定输出目录
python3 ~/moltbot/skills/captcha-bypass/bypass.py "https://example.com/login" --output ~/captcha_bypass

# 仅分析（不生成代码）
python3 ~/moltbot/skills/captcha-bypass/bypass.py "https://example.com/login" --analyze-only
```

### ACP 调用

```
@DeepSeeker 帮我绕过这个验证码 https://example.com/captcha
```

## 工作流程

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Claude Code 分析目标网站                      │
│  - 访问目标 URL                                          │
│  - 识别验证码类型（极验4代/腾讯防水墙/其他）              │
│  - 抓包分析验证码初始化请求和参数                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 2: 生成绕过代码                                   │
│  - 缺口识别算法（OpenCV 模板匹配）                       │
│  - 人类轨迹模拟（贝塞尔曲线 + 随机抖动）                  │
│  - 加密参数还原（如需要）                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: 本地验证                                      │
│  - 使用 Selenium 加载目标页面                            │
│  - 执行绕过代码                                          │
│  - 验证是否成功                                          │
└─────────────────────────────────────────────────────────┘
```

## 输出文件

| 文件                | 说明           |
| ------------------- | -------------- |
| `analyze_result.md` | 验证码分析报告 |
| `solver.py`         | 主绕过代码     |
| `trajectory.py`     | 轨迹生成模块   |
| `requirements.txt`  | Python 依赖    |

## 支持的验证码类型

| 类型        | 状态        | 说明                       |
| ----------- | ----------- | -------------------------- |
| 极验4代滑块 | ✅ 完整支持 | 缺口识别 + 轨迹 + 加密参数 |
| 极验3代     | ✅ 完整支持 | 略有差异的参数             |
| 腾讯防水墙  | 🔜 开发中   | 待实现                     |
| AWS WAF     | 🔜 开发中   | 待实现                     |
| reCAPTCHA   | 🔜 开发中   | 待实现                     |

## 局限性

⚠️ **仅用于授权安全测试** — 请确保您拥有目标网站的授权许可。

## 触发词

- "绕过验证码"
- "captcha bypass"
- "滑块验证"
- "分析验证码"
