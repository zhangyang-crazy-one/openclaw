---
name: Stock Report V2 Generator
slug: stock-report-v2
version: 1.0.0
description: 生成V2.0格式股票研究报告，严格按照7个章节结构
metadata: { "openclaw": { "emoji": "📊" } }
---

# 股票研究报告V2.0生成技能

## 格式要求 (必须严格遵守)

### 7个章节结构

1. 一、公司概况 - 1.1基本信息(table)+1.2主营业务+1.3主要产品/服务+1.4市场地位
2. 二、商业模式分析 - 2.1商业模式概述+2.2行业地位+2.3竞争优势
3. 三、技术面分析 - 3.1技术指标(table)+3.2技术面得分(table)
4. 四、基本面分析 - 4.1财务指标+4.2 Carlson质量评分+4.3巴菲特10大公式+4.4历史分红数据+4.5基本面得分
5. 五、DCF估值模型 - 5.1估值假设+5.2估值结果+5.3 DCF得分
6. 六、行业对比
7. 七、结论 - 7.1综合评分(table)+7.2投资建议

### HTML模板 (使用weasyprint)

```html
<html>
  <head>
    <meta charset="UTF-8" />
    <style>
      body {
        font-family: "Microsoft YaHei";
        font-size: 10pt;
        line-height: 1.5;
        padding: 20px;
      }
      h1 {
        font-size: 18pt;
        text-align: center;
        color: #1a1a1a;
      }
      h2 {
        font-size: 14pt;
        color: #2c3e50;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
      }
      h3 {
        font-size: 12pt;
        color: #34495e;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
      }
      th,
      td {
        border: 1px solid #bdc3c7;
        padding: 6px 8px;
        text-align: center;
      }
      th {
        background: #ecf0f1;
        font-weight: bold;
      }
      .highlight {
        background: #fff3cd;
      }
      .score {
        font-weight: bold;
        color: #27ae60;
      }
    </style>
  </head>
  <body>
    {content}
  </body>
</html>
```

## 数据来源

- K线数据: /home/liujerry/金融数据/stocks_clean/{code}.csv
- 财务数据: /home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv
- 公司信息: akshare stock_individual_info_em

## 必含字段

### 技术面 (6分)

- Williams %R: <-80得3分
- RSI: <30得1分
- MACD: 金叉得1分
- KDJ: K<20得1分
- 布林: 触及得1分

### 基本面 (7分)

- ROE: >20%得2分, >10%得1分
- 净利润: >1亿得1分
- 毛利率: >30%得1分
- 净利率: >10%得1分
- EPS: >0.3得1分

### DCF (5分)

- 上涨空间 >50%: 5分
- > 30%: 4分
- > 10%: 3分
- > -10%: 2分
- > -30%: 1分

### 巴菲特10大公式 (10分制)

1. 现金测试
2. 负债权益比
3. ROE
4. 流动比率
5. 营业利润率
6. 资产周转率
7. 利息保障倍数
8. 盈利稳定性
9. 自由现金流
10. 资本配置(分红)

## 使用方法

1. 读取股票K线数据计算技术指标
2. 读取本地财务数据获取基本面
3. 使用akshare获取公司深度调研信息
4. 按7章节结构生成Markdown
5. 使用weasyprint转为PDF
