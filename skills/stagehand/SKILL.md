# Stagehand Browser Automation (V3)

**基于 Stagehand 核心架构重构的浏览器自动化技能**

## 🎯 核心设计优势

### 1. Hybrid Accessibility Tree
```
传统方式 (脆弱):              V3 方式 (稳定):
CSS selector:                语义描述:
#login-btn-1234              <button> "登录"
                              role="button"
                              state=enabled
```

### 2. Two-Phase Inference (两阶段推理)
```
用户指令: "点击登录按钮"
         ↓
┌─────────────────────────────────────┐
│ Phase 1: 找到元素                    │
│   从 A11y Tree 匹配 "登录按钮"        │
│   → element_id: 5                    │
│   → description: 登录按钮             │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ Phase 2: 确定动作                     │
│   method: click                     │
│   arguments: ["left"]               │
│   reasoning: 找到登录按钮，执行点击    │
└─────────────────────────────────────┘
```

### 3. Self-Healing (自愈能力)
- 页面更新 → 元素 ID 变化
- **但**: 语义描述不变
- AI 自动适配新页面结构

## 📦 依赖

```bash
# Python packages
pip install playwright httpx

# System
# - Chrome/Chromium installed
# - Playwright browsers (playwright install)
```

## 🔧 配置

```bash
# MiniMax API (国内版)
export MINIMAX_API_KEY="your-api-key"
export MINIMAX_API_BASE="https://api.minimaxi.com/v1"

# 可选: Chrome 路径
export CHROME_PATH="/usr/bin/google-chrome"
```

## 🚀 使用方法

### 基本命令

```bash
# 初始化浏览器
/stagehand init

# 导航到 URL
/stagehand navigate <url>

# 执行自然语言动作
/stagehand act <instruction>

# 提取结构化数据
/stagehand extract <instruction>

# 观察页面元素
/stagehand observe <instruction>

# 运行自主代理
/stagehand agent <task>
```

### 示例

```bash
# 导航
/stagehand navigate https://github.com

# 执行动作
/stagehand act "点击登录按钮"
/stagehand act "向下滚动 50%"
/stagehand act "按回车键"

/stagehand act "在搜索框输入 Python"
/stagehand act "点击搜索按钮"

/stagehand extract "提取所有项目标题"
/stagehand extract "获取价格列表"

/stagehand observe "找到所有可点击的按钮"

/stagehand agent "搜索 AI 相关论文并提取标题"
```

## 🏗️ 架构

```
MiniMaxBrowserV3
├── AccessibilityTreeBuilder
│   └── 构建语义化元素树
├── LLM Client
│   └── MiniMax API 调用
├── Actions
│   ├── act() - 两阶段推理
│   ├── extract() - 数据提取
│   ├── observe() - 元素观察
│   └── agent() - 自主规划
└── Self-Healing
    └── 每次操作后刷新 A11y Tree
```

## 📊 技术细节

### A11y Tree 元素格式
```json
{
  "tag": "button",
  "selector": "[id="login"]",
  "role": "button",
  "name": "登录",
  "placeholder": "",
  "type": "",
  "interactive": true
}
```

### 动作支持
| 动作 | 描述 |
|------|------|
| `click` | 左/中/右键点击 |
| `hover` | 鼠标悬停 |
| `fill` | 填充输入框 |
| `press` | 按键 (Enter, Space...) |
| `scroll` | 滚动 (百分比) |

## 🔍 vs 传统方法

| 特性 | 传统 Selenium/Playwright | Stagehand V3 |
|------|-------------------------|--------------|
| 元素定位 | CSS Selector (脆弱) | A11y Tree (稳定) |
| 页面适应 | ❌ 手动更新 | ✅ 自愈 |
| 动态内容 | 需要等待 | 自动处理 |
| 学习成本 | 高 | 低 |
| 维护成本 | 高 | 低 |

## 📝 注意事项

1. **首次运行**: 需要下载 Playwright 浏览器
2. **API Key**: 确保 MiniMax API 配额充足
3. **页面刷新**: 每次重大操作后自动刷新 A11y Tree
4. **复杂任务**: 使用 `/stagehand agent` 获取最佳效果

## 🐛 故障排除

### 元素未找到
```bash
# 强制刷新 A11y Tree
/stagehand observe "页面所有元素"
```

### API 错误
```bash
# 检查 API 配置
export MINIMAX_API_KEY="correct-key"
export MINIMAX_API_BASE="https://api.minimaxi.com/v1"
```

### 浏览器问题
```bash
# 使用系统 Chrome
export CHROME_PATH="/usr/bin/google-chrome"
```

## 📚 参考

- [Stagehand 源码](https://github.com/browserbase/stagehand)
- [Playwright 文档](https://playwright.dev/)
- [MiniMax API](https://api.minimax.io/)
