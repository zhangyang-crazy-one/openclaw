---
name: claw-screener-cn
description: A股股票综合分析工具，结合技术分析(Williams %R, RSI, MACD, KDJ, 布林带)和基本面分析(巴菲特公式, Carlson评分, DCF估值)
homepage: https://github.com/rsoutar/claw-screener
metadata:
  clawdbot:
    emoji: "📊"
    requires:
      env: []
      runtime: python3 >= 3.8
      config_paths: []
---

# Claw-Screener-CN

A股股票综合分析工具，结合技术分析与基本面分析，为投资决策提供支持。

## 功能特点

### 📈 技术分析

- **Williams %R**: 超卖/超买指标
- **RSI**: 相对强弱指数
- **MACD**: 指数平滑异同移动平均线
- **布林带**: 价格波动通道

### 📋 基本面分析

- **巴菲特10大公式**: 现金流、负债、ROE、流动性等
- **Carlson质量评分**: 营收增长、净利润增长、ROIC、回购、营业利润率
- **DCF估值**: 现金流折现计算内在价值

### ⚡ 性能优化

- **本地缓存**: 4小时技术面缓存，24小时基本面缓存
- **增量更新**: 只分析新数据

## 数据源

- **价格数据**: 本地CSV文件 (`/home/liujerry/金融数据/stocks_clean/`)
- **财务数据**: 模拟数据 (可接入真实API)

## 使用方法

### 完整分析 (技术面 + 基本面 + DCF)

```bash
python src/screening_full.py
```

### 快速筛选 (技术面)

```bash
python src/screening_local.py
```

### 个股深度分析

```bash
python src/analyze.py 300502 --name "新易盛"
```

## 输出示例

```
================================================================================
📊 A股自选股综合分析报告 (技术面 + 基本面 + DCF估值)
================================================================================

📈 符合买入条件的股票 (总分 >= 4)
--------------------------------------------------------------------------------

300502 新易盛
   价格: 364.06 | WR: -93.86 | RSI: 41.02 | MACD: 死叉
   技术分: 4/6 | Carlson: 58 (B (一般))
   DCF: 内在价值=4.73 | 上涨空间=-98.7%
   ➡️ 🚀 强烈推荐买入
```

## 评分体系

| 指标             | 权重  | 说明       |
| ---------------- | ----- | ---------- |
| Williams %R <-80 | +3    | 超卖信号   |
| RSI < 30         | +1    | 超卖信号   |
| 布林下轨         | +1    | 触及支撑   |
| Carlson评分      | 0-100 | 质量评估   |
| DCF上涨空间      | -     | 估值合理性 |

## 环境要求

- Python 3.8+
- pandas
- numpy

## 文件结构

```
claw-screener-cn/
├── SKILL.md
├── requirements.txt
└── src/
    ├── screening_full.py    # 完整分析
    ├── screening_local.py  # 快速筛选
    ├── analyze.py          # 个股分析
    ├── data_fetcher.py    # 数据获取
    ├── technical_indicators.py  # 技术指标
    ├── advanced_analysis.py      # 基本面分析
    └── cache.py           # 缓存管理
```
