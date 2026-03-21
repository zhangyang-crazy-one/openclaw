---
name: HTML Report Formatter
description: AI-powered HTML report creation skill for PDF export. Distinguishes between economic/financial reports and regular articles/blog posts for optimal PDF rendering.
read_when:
  - Creating HTML reports for PDF export
  - Generating professional documents from AI content
  - Formatting Anthropic blog translations
  - Creating economic/financial reports
metadata: { "clawdbot": { "emoji": "📄", "requires": { "bins": ["libreoffice"] } } }
allowed-tools: Bash(libreoffice:*)
---

# HTML Report Formatter Skill

创建适合 PDF 导出的专业 HTML 报告。区分经济报告和普通文章的不同格式要求。

## 核心原则

### 经济/金融报告 vs 普通文章的区别

| 特性     | 经济/金融报告    | 普通文章/博客  |
| -------- | ---------------- | -------------- |
| 标题字体 | 16-18px          | 24-28px        |
| 标题宽度 | 不超过页面80%    | 可占满行       |
| 表格     | 必须包含，带标题 | 可选           |
| 数字格式 | 货币/百分比      | 普通数字       |
| 行高     | 紧凑 (20-28px)   | 舒适 (30-40px) |
| 边距     | 较小 (20px)      | 舒适 (30-40px) |
| 段落间距 | 紧凑             | 宽松           |
| 代码块   | 较少             | 可选           |
| 脚注     | 经常需要         | 可选           |

## HTML 模板

### 1. 普通文章/博客翻译模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>{标题}</title>
    <style>
      body {
        font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
        line-height: 1.8;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 40px 20px;
      }
      h1 {
        font-size: 24px; /* 较小标题 */
        color: #1a1a1a;
        border-bottom: 3px solid #0066cc;
        padding-bottom: 12px;
        margin-bottom: 25px;
        word-wrap: break-word;
      }
      h2 {
        font-size: 18px;
        color: #0066cc;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-left: 10px;
        border-left: 3px solid #0066cc;
        word-wrap: break-word;
      }
      h3 {
        font-size: 15px;
        color: #333;
        margin-top: 20px;
        margin-bottom: 10px;
      }
      p {
        margin-bottom: 12px;
        text-align: justify;
      }
      .original {
        background-color: #f8f8f8;
        border-left: 3px solid #888;
        padding: 12px 15px;
        margin: 15px 0;
        font-size: 14px;
        color: #555;
        font-style: italic;
        word-wrap: break-word;
      }
      .translation {
        background-color: #f0f7ff;
        border-left: 3px solid #0066cc;
        padding: 12px 15px;
        margin: 15px 0;
        font-size: 14px;
        font-weight: 500;
        word-wrap: break-word;
      }
      .meta {
        background-color: #fff8e1;
        border: 1px solid #ffc107;
        padding: 12px;
        margin-bottom: 25px;
        border-radius: 4px;
        font-size: 13px;
      }
      ul,
      ol {
        margin: 12px 0;
        padding-left: 25px;
      }
      li {
        margin-bottom: 8px;
      }
      blockquote {
        background-color: #fafafa;
        border-left: 3px solid #28a745;
        padding: 10px 15px;
        margin: 15px 0;
        font-style: italic;
      }
      hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 30px 0;
      }
      .footer {
        text-align: center;
        color: #888;
        font-size: 12px;
        margin-top: 40px;
      }
    </style>
  </head>
  <body>
    <h1>{标题}</h1>

    <div class="meta">
      <strong>来源：</strong>{来源}<br />
      <strong>日期：</strong>{日期}<br />
      <strong>原文链接：</strong><a href="{链接}">{链接}</a>
    </div>

    <!-- 内容区域 -->
    {内容}

    <hr />
    <div class="footer">
      翻译日期：{翻译日期}<br />
      本报告采用原文+中文对照格式
    </div>
  </body>
</html>
```

### 2. 经济/金融报告模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>{标题}</title>
    <style>
      body {
        font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        font-size: 13px;
      }
      h1 {
        font-size: 18px; /* 较小标题避免超出行 */
        color: #1a1a1a;
        border-bottom: 2px solid #2c3e50;
        padding-bottom: 8px;
        margin-bottom: 20px;
        max-width: 85%;
        word-wrap: break-word;
      }
      h2 {
        font-size: 15px;
        color: #2c3e50;
        margin-top: 20px;
        margin-bottom: 12px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
        max-width: 80%;
      }
      h3 {
        font-size: 14px;
        color: #34495e;
        margin-top: 15px;
        margin-bottom: 8px;
      }
      p {
        margin-bottom: 8px;
        text-align: justify;
      }

      /* 表格样式 - 经济报告必须有表格 */
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 12px;
        table-layout: fixed;
      }
      th {
        background-color: #2c3e50;
        color: white;
        padding: 8px 5px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #2c3e50;
      }
      td {
        padding: 6px 5px;
        border: 1px solid #ddd;
        text-align: center;
        word-wrap: break-word;
      }
      tr:nth-child(even) {
        background-color: #f8f9fa;
      }
      tr:hover {
        background-color: #e8f4f8;
      }

      /* 数字格式化 */
      .money {
        font-family: "Courier New", monospace;
        text-align: right;
      }
      .positive {
        color: #27ae60;
      }
      .negative {
        color: #e74c3c;
      }

      /* 重要提示 */
      .highlight {
        background-color: #fff3cd;
        border-left: 3px solid #ffc107;
        padding: 8px 12px;
        margin: 10px 0;
      }

      .meta {
        background-color: #e8f4f8;
        border: 1px solid #b8d4e3;
        padding: 10px;
        margin-bottom: 15px;
        border-radius: 3px;
        font-size: 12px;
      }

      ul,
      ol {
        margin: 8px 0;
        padding-left: 20px;
      }
      li {
        margin-bottom: 5px;
      }

      hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 20px 0;
      }
    </style>
  </head>
  <body>
    <h1>{标题}</h1>

    <div class="meta">
      <strong>报告类型：</strong>{类型}<br />
      <strong>发布日期：</strong>{日期}<br />
      <strong>数据来源：</strong>{来源}
    </div>

    <!-- 内容区域 -->
    {内容}

    <hr />
    <div style="text-align: center; color: #888; font-size: 11px;">报告生成日期：{生成日期}</div>
  </body>
</html>
```

## 关键格式化规则

### 1. 标题自动换行

**重要**: 所有标题必须能够自动换行，防止超出页面宽度：

```css
h1,
h2,
h3 {
  max-width: 85%; /* 限制标题宽度 */
  word-wrap: break-word; /* 允许换行 */
  overflow-wrap: break-word;
}
```

### 2. 表格响应式设计

```css
table {
  width: 100%;
  table-layout: fixed; /* 固定列宽，防止溢出 */
}

td,
th {
  word-wrap: break-word; /* 单元格内文字换行 */
}
```

### 3. 原文/翻译对比块

```css
.original {
  background-color: #f8f8f8;
  border-left: 3px solid #888;
  padding: 12px 15px;
  margin: 15px 0;
  font-size: 14px;
}

.translation {
  background-color: #f0f7ff;
  border-left: 3px solid #0066cc;
  padding: 12px 15px;
  margin: 15px 0;
  font-size: 14px;
  font-weight: 500;
}
```

## PDF 转换命令

```bash
# HTML 转 PDF (使用 LibreOffice)
libreoffice --headless --convert-to pdf filename.html --outdir /tmp

# 批量转换
for f in *.html; do libreoffice --headless --convert-to pdf "$f" --outdir /tmp; done
```

## 格式化检查清单

### 普通文章检查项:

- [ ] 标题字体 22-26px
- [ ] 行高 1.7-2.0
- [ ] 边距 30-40px
- [ ] 原文/翻译使用对比色块
- [ ] 标题有 border-bottom

### 经济报告检查项:

- [ ] 标题字体 16-18px
- [ ] 标题不超过行80%
- [ ] 必须包含表格
- [ ] 表格有表头和边框
- [ ] 数字右对齐
- [ ] 行高紧凑 1.5-1.6
- [ ] 边距 20px

## 使用示例

### Anthropic 博客翻译

```bash
# 1. 创建 HTML 文件
cat > article.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>检测与防止蒸馏攻击</title>
    <style>
        /* 使用普通文章模板样式 */
    </style>
</head>
<body>
    <h1>检测与防止蒸馏攻击</h1>
    <div class="meta">来源：Anthropic Official Blog | 日期：2026-02-23</div>

    <div class="original">
        <p>原文内容...</p>
    </div>
    <div class="translation">
        <p>翻译内容...</p>
    </div>
</body>
</html>
EOF

# 2. 转换为 PDF
libreoffice --headless --convert-to pdf article.html --outdir /tmp
```

### 股票分析报告

```bash
# 1. 创建 HTML 文件
cat > stock_report.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>股票分析报告</title>
    <style>
        /* 使用经济报告模板样式 */
    </style>
</head>
<body>
    <h1>股票分析报告 - {股票名称}</h1>
    <div class="meta">类型：技术分析 | 日期：2026-03-18</div>

    <!-- 必须包含表格 -->
    <table>
        <tr><th>指标</th><th>数值</th><th>变化</th></tr>
        <tr><td>PE</td><td>15.2</td><td class="positive">+5%</td></tr>
    </table>
</body>
</html>
EOF

# 2. 转换为 PDF
libreoffice --headless --convert-to pdf stock_report.html --outdir /tmp
```

## 常见问题

### 问题1: 标题超出页面

**解决方案**:

```css
h1 {
  max-width: 80%;
  word-wrap: break-word;
}
```

### 问题2: 表格列太宽

**解决方案**:

```css
table {
  table-layout: fixed;
}
td,
th {
  max-width: 150px;
  word-wrap: break-word;
}
```

### 问题3: 数字显示不正确

**解决方案**:

```css
.money {
  font-family: "Courier New", monospace;
  text-align: right;
}
```

---

## 记住

1. **普通文章**: 标题大、边距宽、原文翻译对比明显
2. **经济报告**: 标题小、必须有表格、数字格式化、行紧凑
3. **PDF 导出**: 使用 HTML 模板而非 Markdown
4. **自动换行**: 所有标题设置 max-width 和 word-wrap
