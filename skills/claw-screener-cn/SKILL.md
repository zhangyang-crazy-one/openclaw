---
name: claw-screener-cn
description: A股V5多因子量化筛选工具，70分全绝对阈值评分体系(盈利25+质量8+安全13+动量8+风险10+规模6)，对齐V5深度报告标准，支持全量5400+股票批量筛选与个股深度分析
homepage: https://github.com/rsoutar/claw-screener
metadata:
  clawdbot:
    emoji: "📊"
    requires:
      env: []
      runtime: python3 >= 3.8
      config_paths: []
---

# Claw-Screener-CN V5 (升级版)

A股V5多因子量化筛选，完全对齐V5深度研究报告评分标准。全绝对阈值，零百分位排名。

## V5 vs V3 核心升级

| 维度     | V3               | V5                         |
| -------- | ---------------- | -------------------------- |
| 评分方式 | 布尔型(有/无)    | **绝对阈值6级**            |
| 现金流   | ❌ 无            | **OCF/NI质量 8pt**         |
| 负债率   | ⚠️ boolean       | **5级评分 8pt**            |
| 动量     | ⚠️ magic_formula | **主评分 8pt**             |
| 风险     | ❌ 无            | **波动率+回撤 10pt**       |
| 规模     | ❌ 无            | **NI/营收/资产 6pt**       |
| 亏损罚分 | ❌ 无            | **ROE×0.5, OCF×0.8**       |
| NPM上限  | ❌ 无            | **100%截断(防一次性收益)** |
| 总分     | ~24              | **70**                     |

---

## V5 评分体系 (70分制)

### 一、盈利能力 (25分)

| 因子   | 满分 | 评分标准 (绝对阈值)                          | 数据源              |
| ------ | :--: | -------------------------------------------- | ------------------- |
| ROE    |  10  | >20%=10, >15%=8, >10%=6, >5%=4, >0%=2, <0%=0 | profit.csv roeAvg   |
| 净利率 |  8   | >30%=8, >20%=6, >10%=4, >5%=3, >0%=1         | profit.csv npMargin |
| 毛利率 |  7   | >50%=7, >40%=5, >30%=3, >20%=2, >0%=1        | profit.csv gpMargin |

⚠️ **NPM上限**: 净利率>100%截断为100%（防止一次性收益虚高评分，如300723的153.7%→8pt而非虚高）

### 二、现金流质量 (8分)

| 因子     | 满分 | 评分标准                             | 数据源                                   |
| -------- | :--: | ------------------------------------ | ---------------------------------------- |
| OCF/净利 |  8   | OCF>NI=8, OCF>0.5NI=5, OCF>0=3, <0=0 | buffett operating_cash_flow + net_income |

### 三、财务安全 (13分)

| 因子        | 满分 | 评分标准 (越低越好)                    | 数据源                                 |
| ----------- | :--: | -------------------------------------- | -------------------------------------- |
| 资产负债率  |  8   | <20%=8, <40%=6, <60%=4, <80%=2, ≥80%=0 | buffett total_liabilities/total_assets |
| 现金/总资产 |  5   | >20%=5, >10%=4, >5%=3, >0%=1           | buffett cash/total_assets              |

### 四、成长动量 (8分)

| 因子    | 满分 | 评分标准                                         | 数据源          |
| ------- | :--: | ------------------------------------------------ | --------------- |
| 6月动量 |  8   | >50%=8, >20%=6, >0%=4, >-10%=2, >-20%=1, <-20%=0 | stocks/ K线计算 |

### 五、风险控制 (10分)

| 因子       | 满分 | 评分标准                                    | 数据源          |
| ---------- | :--: | ------------------------------------------- | --------------- |
| 年化波动率 |  5   | <30%=5, <40%=4, <50%=3, <60%=2, ≥60%=1      | stocks/ K线计算 |
| 最大回撤   |  5   | >-10%=5, >-20%=4, >-30%=3, >-40%=2, ≤-40%=1 | stocks/ K线计算 |

### 六、规模奖励 (6分)

| 条件           | 加分 |
| -------------- | :--: |
| 净利 > 10亿    |  +1  |
| 净利 > 50亿    |  +2  |
| 营收 > 50亿    |  +1  |
| 营收 > 100亿   |  +1  |
| 总资产 > 100亿 |  +1  |

### 亏损罚分乘数

```
最终得分 = (P+Q+S+M+R+B) × roe_mult × ocf_mult

roe_mult: ROE>0→1.0 | (-10%,0]→0.5 | <-10%→0.2
ocf_mult: OCF>0→1.0 | ≤0→0.8
```

---

## 数据源 (100%本地，零API依赖)

| 文件                      | 路径                                   | 用途                        |
| ------------------------- | -------------------------------------- | --------------------------- |
| profit.csv                | ~/金融数据/fundamentals/chuangye_full/ | ROE/净利率/毛利率/净利/股本 |
| buffett_supplementary.csv | ~/金融数据/fundamentals/               | 总资产/负债/现金/OCF/营收   |
| stocks/\*.csv             | ~/金融数据/stocks/                     | K线(计算动量/波动率/回撤)   |

**代码映射**: profit `sz.000001` ↔ buffett `1` (str(int(bn)))

---

## 护城河分析 (保留V3)

基于晨星框架，识别五大护城河来源：

- **无形资产**: 品牌、专利、监管特许权
- **转换成本**: 客户更换供应商的成本
- **网络效应**: 用户越多价值越大
- **成本优势**: 规模经济、独特位置
- **有效规模**: 市场规模有限

护城河评分：宽(5pt) / 窄(3pt) / 无(0pt)

---

## 价值投资附加分析 (保留V3)

### Piotroski F-score (9项)

- ROA>0, CFO>0, ΔROA>0, CFO>NI
- Δ长期负债<0, Δ流动比率>0, 无新股发行
- Δ毛利率>0, Δ资产周转率>0
- ≥7分为优质

### DCF估值

- FCF基数 = 经营CF
- WACC 8-10%, 永续增长率 2-3%

### 巴菲特10大公式

1. 现金测试 2. 负债权益比 3. ROE 4. 流动比率 5. 营业利润率
2. 资产周转率 7. 利息保障倍数 8. 盈利稳定性 9. 自由现金流 10. 资本配置(分红)

---

## 使用方法

### 全量批量筛选 (推荐)

```bash
python src/screening_v5.py
# 输出: ~/金融数据/screening_results/v5_top200_YYYYMMDD.csv
```

### 个股深度分析

```bash
python src/analyze.py 300502 --name "新易盛"
```

---

## 文件结构

```
claw-screener-cn/
├── SKILL.md                    # 本文件 (V5升级版)
├── src/
│   ├── screening_v5.py         # V5全量多因子筛选 (核心)
│   ├── analyze.py              # 个股深度分析
│   ├── data_loader.py          # 本地CSV加载器
│   ├── moat_analysis.py        # 护城河分析
│   ├── pitroski.py             # Piotroski F-score
│   ├── dcf_valuation.py        # DCF估值
│   ├── magic_formula.py        # 神奇公式 (保留)
│   ├── famafrench_screener.py  # Fama-French (保留)
│   └── risk_manager.py         # GARCH+VaR (保留)
```

---

## V5筛选脚本核心逻辑 (screening_v5.py)

```python
# 1. 加载本地数据 (profit.csv + buffett + stocks/)
# 2. 过滤: totalShare>0, assets>0, K线≥120条, ROE>-30%
# 3. 逐只评分:

profit_score = score_roe(roe) + score_npm(min(npm, 1.0)) + score_gpm(gpm)
quality_score = score_ocf(ocf, ni)
safety_score = score_debt(debt_ratio) + score_cash_ratio(cash, assets)
mom_score = score_momentum(mom6)
risk_score = score_volatility(vol) + score_maxdd(mdd)
scale_bonus = compute_scale(ni, rev, assets)

base = profit_score + quality_score + safety_score + mom_score + risk_score + scale_bonus
final = base * roe_multiplier * ocf_multiplier
```

---

## 参考来源

- V5 Hermes 筛选系统 (2026-05-14 实战验证)
- Warren Buffett 投资原则
- Morningstar 护城河评级
- Benjamin Graham 证券分析
- Piotroski F-score 研究
