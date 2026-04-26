---
name: claw-screener-cn
description: A股股票综合分析工具，结合技术分析(Williams %R, RSI, MACD, KDJ, 布林带)和基本面分析(护城河评估、安全边际、长期ROE、价值陷阱检测、Piotroski F-score、DCF/EPV估值)
homepage: https://github.com/rsoutar/claw-screener
metadata:
  clawdbot:
    emoji: "📊"
    requires:
      env: []
      runtime: python3 >= 3.8
      config_paths: []
---

# Claw-Screener-CN (优化版)

A股股票综合分析工具，结合技术分析与价值投资分析，为投资决策提供支持。

## 功能特点

### 📈 技术分析

- **Williams %R**: 超卖/超买指标
- **RSI**: 相对强弱指数
- **MACD**: 指数平滑异同移动平均线
- **KDJ**: 随机指标
- **布林带**: 价格波动通道

### 🏰 护城河分析 (新增)

基于晨星(Morningstar)框架，识别五大护城河来源：

- **无形资产**: 品牌、专利、监管特许权
- **转换成本**: 客户更换供应商的成本
- **网络效应**: 用户越多价值越大
- **成本优势**: 规模经济、独特位置
- **有效规模**: 市场规模有限，领先者占据优势

### 📋 价值投资筛选 (优化)

#### 1. 长期ROE筛选

- **10年平均ROE ≥ 15%** (严格标准: >20%)
- 排除单一年份ROE < 15%的企业

#### 2. 质量指标

- **债务权益比 < 0.5**
- **毛利率 > 40%**
- **连续5年自由现金流为正**

#### 3. 价值陷阱检测 (新增)

- **Piotroski F-score**: 9项二元检验，综合得分≥7为优质
- **EPV (盈利功率价值)**: 检验是否存在价值陷阱

### 💰 安全边际计算 (新增)

多种估值方法综合评估：

- **DCF估值**: 现金流折现 (WACC 8-10%, 永续增长率2-3%)
- **EPV法**: 盈利功率价值
- **格雷厄姆公式**: 快速估算

### 📊 仓位管理建议 (新增)

基于安全边际的仓位建议：
| 安全边际 | 建议仓位 | 风险等级 |
|----------|----------|----------|
| > 50% | 3-5% | 低 |
| 30-50% | 2-3% | 中低 |
| 20-30% | 1-2% | 中 |
| < 20% | 观望 | 高 |

### ⚡ 原有功能

- **巴菲特10大公式**: 现金流、负债、ROE、流动性等
- **Carlson质量评分**: 营收增长、净利润增长、ROIC、回购、营业利润率
- **DCF估值**: 现金流折现计算内在价值

### ⚡ 性能优化

- **本地缓存**: 4小时技术面缓存，24小时基本面缓存
- **增量更新**: 只分析新数据

### 🎯 多因子选股模型 (新增 v2.0)

基于NotebookLM深度研究，新增五大选股模块：

#### 1. 多通道数据获取 (`data_source.py`)

- **自动重试**: 3次重试，递增延迟 (1s→2s→3s)
- **通道切换**: akshare → baostock → 缓存
- **容错机制**: 东财API限流时自动切换备用源

#### 2. 增强筛选器 (`enhanced_screening.py`)

新增5大筛选因子：
| 因子 | 说明 | 阈值 |
|------|------|------|
| ROE稳定性 | 10年平均ROE≥15% | ≥15% |
| 自由现金流 | FCF连续3-5年为正 | 3年+ |
| 动量因子 | 6个月涨幅 | 0-50% |
| 低波动因子 | 年化波动率 | <50% |
| 估值因子 | PE/PB | PE<30, PB<5 |

#### 3. 神奇公式+动量 (`magic_formula.py`)

- **高盈利收益率**: EBIT/EV (简化: ROE)
- **高资本回报率**: ROIC
- **动量过滤**: 6个月涨幅 0-30%最佳
- **综合排名**: ROE排名 + 动量排名

#### 4. Fama-French六因子 (`famafrench_screener.py`)

六因子模型：
| 因子 | 含义 | 得分规则 |
|------|------|----------|
| SMB | 规模 | 小市值得分高 |
| HML | 价值 | 低PE得分高 |
| RMW | 盈利 | 高ROE得分高 |
| CMA | 投资 | 温和增长得分高 |
| Mom | 动量 | 0-30%涨幅得分高 |

#### 5. 动态因子加权 (`dynamic_factor.py`)

- **IC追踪**: 记录因子与收益相关性
- **动态权重**: 根据IC表现自动调整
- **IR最大化**: IR = IC / IC标准差
- **失效检测**: 剔除IC < 0.02的因子

#### 6. GARCH+VaR风控 (`risk_manager.py`)

- **GARCH波动率**: EWMA方法预测未来波动率
- **VaR风险价值**: 95%/99%置信度最大损失
- **风险评级**: 🟢低🟡中🟠较高🔴高
- **自动过滤**: 剔除高风险股票

## 数据源

- **价格数据**: 本地CSV文件 (`/home/liujerry/金融数据/stocks/`)
- **财务数据**: akshare API + 本地缓存

## 使用方法

### 完整分析 (技术面 + 基本面 + 护城河 + 安全边际)

```bash
python src/screening_full.py
```

### 价值投资筛选 (护城河 + ROE + 安全边际)

```bash
python src/screening_value.py
```

### 快速筛选 (技术面)

```bash
python src/screening_local.py
```

### 个股深度分析

```bash
python src/analyze.py 300926 --name "博俊科技"
```

### 新模块使用方法 (v2.0)

#### 多通道数据获取

```bash
cd src
python data_source.py
```

#### 神奇公式+动量选股

```bash
python magic_formula.py
```

#### Fama-French六因子选股

```bash
python famafrench_screener.py
```

#### 动态因子筛选

```bash
python dynamic_factor.py
```

#### 风险分析 (GARCH+VaR)

```bash
python risk_manager.py
```

## 输出示例

```
================================================================================
📊 A股自选股综合分析报告 (技术面 + 基本面 + 护城河 + 安全边际)
================================================================================

🏰 护城河分析: 品牌优势 + 转换成本
📈 10年平均ROE: 22.58% | Piotroski F-score: 8/9
💰 安全边际: 25% | 内在价值: 38.50元 | 当前价格: 29.09元
📊 建议仓位: 2-3%

300926 博俊科技
   价格: 29.09 | WR: -85.64 | RSI: 20.81 | MACD: 死叉
   技术分: 5/7 | Carlson: 5/7 | 巴菲特公式: 7/10
   护城河: 品牌优势, 转换成本
   DCF: 内在价值=38.50 | 上涨空间=25%
   ✅ 安全边际充足 | 建议仓位: 2-3%
```

## 评分体系

### 技术面评分

| 指标              | 得分 | 说明     |
| ----------------- | ---- | -------- |
| Williams %R < -80 | +3   | 超卖信号 |
| RSI < 30          | +1   | 超卖信号 |
| MACD金叉          | +1   | 买入信号 |
| KDJ超卖           | +1   | 超卖信号 |
| 布林下轨          | +1   | 触及支撑 |

### 护城河评分

| 护城河类型 | 得分 | 权重 |
| ---------- | ---- | ---- |
| 宽护城河   | 5分  | 最高 |
| 窄护城河   | 3分  | 中   |
| 无护城河   | 0分  | 低   |

### 质量评分

| 指标              | 标准 | 得分 |
| ----------------- | ---- | ---- |
| 10年平均ROE       | >20% | 2分  |
| 净利润            | >1亿 | 1分  |
| 毛利率            | >30% | 1分  |
| 净利率            | >10% | 1分  |
| Piotroski F-score | ≥7/9 | 2分  |

### 安全边际评分

| 上涨空间 | 得分 |
| -------- | ---- |
| > 50%    | 5分  |
| > 30%    | 4分  |
| > 10%    | 3分  |
| > -10%   | 2分  |
| < -30%   | 1分  |

## 选股流程 (五阶段模型)

### 阶段1: 界定能力圈

- 确定自己理解的行业

### 阶段2: 质量指标初筛

- 10年平均ROE > 15%
- 债务权益比 < 0.5

### 阶段3: 护城河分析

- 识别五大护城河来源
- 评估持久性

### 阶段4: 系统性估值

- DCF/EPV/格雷厄姆公式
- 计算安全边际

### 阶段5: 风险审核

- Piotroski F-score
- 仓位建议

## 环境要求

- Python 3.8+
- pandas
- numpy
- akshare

## 文件结构

```
claw-screener-cn/
├── SKILL.md
├── requirements.txt
└── src/
    ├── screening_full.py       # 完整分析
    ├── screening_value.py     # 价值投资筛选
    ├── screening_local.py     # 快速筛选
    ├── analyze.py             # 个股分析
    ├── data_fetcher.py        # 数据获取
    ├── technical_indicators.py # 技术指标
    ├── moat_analysis.py       # 护城河分析
    ├── safety_margin.py       # 安全边际计算
    ├── pitroski.py            # Piotroski F-score
    ├── advanced_analysis.py   # 基本面分析
    ├── cache.py               # 缓存管理
    # ---- 新增 v2.0 模块 ----
    ├── data_source.py         # 多通道数据获取 (重试+切换)
    ├── enhanced_screening.py  # 增强筛选器 (5大新因子)
    ├── magic_formula.py       # 神奇公式+动量
    ├── famafrench_screener.py # Fama-French六因子
    ├── dynamic_factor.py      # 动态因子加权 (IC/IR)
    └── risk_manager.py        # GARCH+VaR风控
```

## 参考来源

- Warren Buffett 投资原则
- Morningstar 护城河评级
- Benjamin Graham 证券分析
- Fama-French 因子模型
- Magic Formula 投资策略 (Joel Greenblatt)
- Piotroski F-score 研究
- GARCH 波动率模型 (Robert Engle)
- VaR 风险价值理论
- NotebookLM 深度研究 (2026-03-16)
