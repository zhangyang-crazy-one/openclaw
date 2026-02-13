# 行业分析技能 (Industry Analysis Skill)

## 概述

本技能提供基于学术研究成果的股票行业分析能力，包括：
- 多因子行业评分模型
- 行业轮动策略
- 行业配置建议
- 风险评估

## 学术支撑

### 核心文献

| # | 作者 | 年份 | 论文 | 期刊 |
|---|------|------|------|------|
| 1 | Fama, French | 1992 | The Cross-Section of Expected Stock Returns | Journal of Finance |
| 2 | Carhart | 1997 | On Persistence in Mutual Fund Performance | Journal of Finance |
| 3 | Fama, French | 2006 | Profitability, Investment and Average Returns | JFE |
| 4 | Novy-Marx | 2013 | The Other Side of Value | JFE |
| 5 | Hou et al. | 2015 | Digesting Anomalies | RFS |
| 6 | Asness et al. | 2013 | Value and Momentum Everywhere | Journal of Finance |

### 多因子框架

| 因子 | 名称 | 权重 | 在创业板的应用 |
|------|------|------|----------------|
| SIZE | 规模因子 | 15% | 创业板以中小盘为主 |
| VALUE | 价值因子 | 20% | PB/PE估值分析 |
| PROFIT | 盈利能力因子 | 20% | ROE筛选优质企业 |
| MOMENTUM | 动量因子 | 15% | 趋势跟踪 |
| GPM | 毛利率因子 | 10% | 竞争优势筛选 |
| GROWTH | 成长因子 | 10% | 营收/利润增速 |
| INVEST | 投资因子 | 10% | 低投资率选股 |

## 行业分类

基于 [证监会《上市公司行业分类指引》(2023)](http://www.csrc.gov.cn) 和 [申万宏源行业分类(2024)](https://www.swsresearch.com):

| 行业代码 | 行业名称 | 特点 |
|----------|----------|------|
| C06 | 医药生物 | 刚需，创新驱动 |
| C09 | 计算机 | 数字经济，国产替代 |
| C14 | 电力设备 | 双碳目标 |
| C05 | 电子 | 创新驱动 |
| C08 | 国防军工 | 计划性，高壁垒 |
| C12 | 机械设备 | 周期复苏 |
| C13 | 汽车 | 新能源车渗透率 |
| C10 | 传媒 | 数字化转型 |
| C07 | 电气设备 | 新能源转型 |
| C02-C20 | 其他 | - |

## 使用方法

### 命令行

```bash
# 基本分析
python3 industry_analysis.py --data /path/to/stocks

# 指定因子
python3 industry_analysis.py --factors value,momentum,growth

# 行业轮动
python3 industry_analysis.py --rotation

# 完整报告
python3 industry_analysis.py --full
```

### 输出文件

- `industry_scores.json` - 行业评分
- `industry_rotation.json` - 轮动信号
- `industry_report.md` - 分析报告

## API 调用

```python
from industry_analysis import IndustryAnalyzer

# 初始化
analyzer = IndustryAnalyzer(
    data_path='/path/to/stocks',
    factors=['value', 'momentum', 'profitability']
)

# 获取行业评分
scores = analyzer.get_industry_scores()

# 获取轮动信号
signals = analyzer.get_rotation_signals()

# 生成报告
report = analyzer.generate_report()
```

## 贡献者

- 基于 Fama-French, Carhart, Novy-Marx 等学术研究
- 针对中国A股市场优化
- 持续更新最新研究成果

## 参考

- [Fama-French 三因子模型 (1992)](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1992.tb02669.x)
- [Carhart 四因子模型 (1997)](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1997.tb03808.x)
- [Novy-Marx 毛利率因子 (2013)](https://www.sciencedirect.com/science/article/pii/S0304405X12001435)
