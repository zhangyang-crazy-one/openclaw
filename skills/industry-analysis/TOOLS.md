# 行业分析技能工具说明

## 使用方法

### 1. 命令行基本用法

```bash
# 进入技能目录
cd /home/liujerry/moltbot/skills/industry-analysis/scripts

# 运行分析
python3 industry_analysis.py

# 指定因子
python3 industry_analysis.py --factors value momentum profitability

# 生成轮动信号
python3 industry_analysis.py --rotation

# 保存结果
python3 industry_analysis.py --save
```

### 2. 快速测试

```bash
python3 quick_test.py
```

### 3. Python API

```python
from industry_analysis import IndustryAnalyzer

# 初始化
analyzer = IndustryAnalyzer(
    data_dir='/path/to/stocks',
    output_dir='/path/to/output'
)

# 分析股票
results = analyzer.analyze_industry(['300750', '300014', '300017'])

# 获取TOP
top_10 = analyzer.get_top_industries(10)

# 轮动信号
signals = analyzer.generate_rotation_signals()

# 生成报告
report = analyzer.generate_report('markdown')

# 保存
analyzer.save_results('my_results.json')
```

## 因子说明

| 因子 | 缩写 | 权重 | 含义 |
|------|------|------|------|
| 规模因子 | SIZE | 15% | 小市值效应 |
| 价值因子 | VALUE | 20% | 低估值 |
| 盈利能力因子 | PROFIT | 20% | 高ROE |
| 动量因子 | MOMENTUM | 15% | 趋势跟踪 |
| 毛利率因子 | GPM | 10% | 高毛利 |
| 成长因子 | GROWTH | 10% | 高增长 |
| 投资因子 | INVEST | 10% | 低投资率 |

## 学术支撑

### 核心论文

1. **Fama, French (1992)** - 三因子模型基础
2. **Carhart (1997)** - 四因子模型（加入动量）
3. **Fama, French (2006)** - 五因子模型（加入盈利和投资）
4. **Novy-Marx (2013)** - 毛利率因子
5. **Hou et al. (2015)** - 四因子模型

### 行业分类

基于 [证监会2023指引](http://www.csrc.gov.cn)

## 配置文件

编辑 `config.yaml` 自定义：

```yaml
# 因子权重
factor_weights:
  size: 0.15
  value: 0.20
  profitability: 0.20
  momentum: 0.15
  growth: 0.10

# 行业配置
industry_mapping:
  technology: ["C09", "C10"]
  healthcare: ["C13", "C14"]
```

## 输出文件

- `industry_analysis_results.json` - 完整分析结果
- 控制台报告 - 终端输出

## 示例输出

```
TOP 10 股票评分:
 1. 300750: 85.2
 2. 300014: 82.1
 3. 300274: 80.5

轮动信号:
  BULL: 45只
  NEUTRAL: 30只
  BEAR: 25只
```

## 常见问题

### Q: 如何添加新因子？
A: 在 `IndustryAnalyzer` 类中添加 `calculate_factor_score` 方法，并更新 `factor_weights`。

### Q: 如何更改行业分类？
A: 修改 `INDUSTRY_CLASSIFICATION` 字典或配置文件 `industry_mapping`。

### Q: 支持哪些输出格式？
A: 当前支持 `json` 和 `markdown`，可通过 `--format` 参数指定。
