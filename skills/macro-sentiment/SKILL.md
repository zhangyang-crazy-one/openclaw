---
name: macro-sentiment
version: 1.0.0
description: 宏观与情绪分析技能 - 洞察市场情绪与经济周期
---

# Macro & Sentiment Analysis

宏观与情绪分析技能，洞察市场情绪、经济周期与政策影响。

## 功能

- 📊 **宏观经济分析** - GDP、通胀、利率、汇率
- 😊 **情绪指标** - VIX、Put/Call Ratio、期权情绪
- 📈 **行为金融** - 投资者情绪、羊群效应
- 🏛️ **政策分析** - 美联储、央行政策
- 📉 **市场周期** - 复苏、扩张、顶峰、衰退

## 数据源

- **NBER** - 美国国家经济研究局
- **SSRN** - 经济学与社会科学研究
- **RePEc** - 经济学论文数据库
- **Crossref** - 金融期刊
- **Semantic Scholar** - 行为金融研究

## 使用方法

```bash
# 宏观经济分析
python3 macro_sentiment.py --query "monetary policy" --type macro

# 市场情绪研究
python3 macro_sentiment.py --query "investor sentiment" --type sentiment

# 美联储政策
python3 macro_sentiment.py --query "Federal Reserve" --type policy

# 经济周期
python3 macro_sentiment.py --query "business cycle" --type cycle

# 综合分析 + 投资建议
python3 macro_sentiment.py --query "market volatility" --analyze
```

## 情绪指标

| 指标 | 说明 | 信号 |
|------|------|------|
| VIX | 恐慌指数 | 高=恐惧，低=贪婪 |
| PCR | 看跌/看涨比率 | 高=看跌，低=看涨 |
| AAII | 个人投资者情绪 | 散户情绪调查 |
| CNN Fear & Greed | 恐惧贪婪指数 | 0-100 评分 |
