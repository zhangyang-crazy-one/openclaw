# 短期量化交易技能

## 概述
本技能提供短期量化交易策略，包括 GARP 策略和配对交易策略。

## 策略1: GARP (合理价格成长)

### 核心思想
- 寻找估值合理的高成长股票
- PEG < 1.0 为最佳
- PE 适中，成长性强劲

### 选股标准
- PE (市盈率): 10-30
- PEG < 1.0
- 营收增长 > 15%
- 净利润增长 > 20%

### 买入信号
- PEG < 0.5: 强烈买入
- PEG < 0.8: 买入
- PEG < 1.0: 持有

## 策略2: 配对交易 (Pairs Trading)

### 核心思想
- 利用两只高度相关股票的价格偏离进行套利
- 当价差偏离均值超过2个标准差时入场
- 回归均值时平仓

### 配对选择
- 蓝筹股 (6xxx) ↔ 创业板 (3xxx) 跨市场配对
- 行业相关性 > 0.7

### 信号
- Z-score > 2: 做空 A / 做多 B
- Z-score < -2: 做多 A / 做空 B
- Z-score 回归 0: 平仓

## 脚本

### 短期策略分析
```bash
python3 garp_pairs_strategy.py
```

### 输出文件
- `/home/liujerry/金融数据/strategies/garp_pairs_results.json`
- `/home/liujerry/金融数据/strategies/blue_chuangye_pairs.json`

## 因子权重

### GARP 评分
- 估值因子 (40%): PE, PEG
- 成长因子 (40%): EPS增长率, 营收增长
- 动量因子 (20%): 60日涨幅

### 配对评分
- 相关性 (50%)
- Z-score 偏离度 (30%)
- 波动率 (20%)

## 使用方法
```bash
# 运行短期策略分析
cd /home/liujerry/moltbot/skills/stock-analyzer/scripts
python3 garp_pairs_strategy.py
```

## 风险提示
- 配对交易需关注流动性风险
- GARP 策略需关注业绩波动
- 建议设置止损线 5-8%
