---
name: quant-backtest
version: 1.0.0
description: 量化回测与价格预测系统 - 基于最新学术论文的机器学习模型
---

# Quant Backtest & Price Prediction

量化回测与价格预测系统，基于2024-2025年最新学术研究成果。

## 理论基础

### 1. 回测方法论 (基于2025年最新研究)

**核心框架：**
- 四步框架：定义规则 → 准备数据 → 运行测试 → 分析结果
- 事件驱动架构 (Event-Driven)
- 关键指标：Sharpe比率、最大回撤、胜率、盈亏比

**性能指标：**
| 指标 | 说明 | 目标值 |
|------|------|--------|
| Sharpe Ratio | 风险调整收益 | >1.0 |
| Max Drawdown | 最大回撤 | <20% |
| Win Rate | 胜率 | >40% |
| Profit Factor | 盈亏比 | >1.5 |

### 2. 价格预测模型 (基于2024-2025论文)

**推荐模型：**

1. **LSTM模型** (最高引用)
   - 论文: Enhanced Stock Price Prediction Using Optimized Deep LSTM Model (2025)
   - 优势: 捕捉长期依赖关系
   - 适用: 短期/长期价格预测

2. **LSTM-GNN混合模型** (最新2025)
   - 论文: Stock Price Prediction Using a Hybrid LSTM-GNN Model (arXiv:2502.15813)
   - 优势: 结合时序+图神经网络
   - 适用: 个股+行业关联预测

3. **LSTM-ARIMA混合模型**
   - 论文: Prediction of Stock Prices Using LSTM-ARIMA Hybrid
   - 优势: 捕捉线性和非线性模式

4. **Transformer-LSTM混合模型** (最新2025)
   - 论文: An AI-Enhanced Forecasting Framework
   - 优势: 时间序列+情绪分析

**模型对比：**
| 模型 | 准确率 | 适用场景 |
|------|--------|----------|
| LSTM | 高 | 长期趋势 |
| CNN-LSTM | 高 | 短期波动 |
| GRU | 中 | 快速训练 |
| Transformer | 高 | 情绪+价格 |

## 使用方法

```bash
# 回测分析
python3 scripts/backtest.py --stock 300456 --strategy momentum --start 2024-01-01

# 价格预测
python3 scripts/predict.py --stock 300456 --model lstm --days 30

# 综合分析
python3 scripts/quant_analysis.py --stocks 300456,300442,300059
```

## 脚本说明

### backtest.py
- 动量策略回测 (优化参数: RSI<25 买入, RSI>75 卖出)
- 均值回归策略回测
- 多策略对比

### predict.py  
- LSTM价格预测
- 趋势预测
- 买入卖出信号

### quant_analysis.py
- 综合量化分析
- 策略推荐
- 风险评估

## 数据源

- Baostock - A股历史数据
- AKShare - 实时行情

## 输出

- 回测绩效报告
- 预测信号
- 综合评分
