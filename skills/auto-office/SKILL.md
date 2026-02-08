# Auto Office 技能

自动生成 Excel 和 PPT 文件的 Moltbot 技能。

## 功能特性

### Excel 功能
- 创建 xlsx 格式文件
- 支持自定义工作表
- 设置单元格格式（字体、颜色、边框）
- 插入表格、图片
- 数据格式化（日期、数字、百分比）
- 合并单元格

### PPT 功能
- 创建 pptx 格式演示文稿
- 添加标题页、内容页
- 插入表格、图表
- 设置文本样式
- 添加图片
- 自定义主题颜色

## 使用方法

### 生成 Excel 报表

```python
# 导入工具
from auto_office.tool import ExcelTool

# 创建Excel工具实例
excel = ExcelTool()

# 生成简单报表
excel.create_workbook(
    filename="report.xlsx",
    data=[
        ["姓名", "年龄", "成绩"],
        ["张三", 25, 95],
        ["李四", 24, 88],
    ],
    sheet_name="成绩单"
)

# 生成带格式的报表
excel.create_formatted_report(
    filename="formatted_report.xlsx",
    title="学生成绩报告",
    headers=["姓名", "数学", "语文", "英语", "总分"],
    data=[
        ["张三", 95, 88, 92, 275],
        ["李四", 85, 90, 87, 262],
        ["王五", 78, 85, 80, 243],
    ],
    title_style={"font_size": 16, "bold": True, "bg_color": "4472C4"},
    header_style={"bold": True, "bg_color": "D9E2F3"},
)
```

### 生成 PPT 演示文稿

```python
from auto_office.tool import PPTTool

# 创建PPT工具实例
ppt = PPTTool()

# 创建简单演示文稿
ppt.create_presentation(
    filename="presentation.pptx",
    slides=[
        {"type": "title", "title": "演示标题", "subtitle": "副标题"},
        {"type": "content", "title": "内容页标题", "content": ["要点1", "要点2", "要点3"]},
    ]
)

# 创建带表格的演示文稿
ppt.create_report_presentation(
    filename="report.pptx",
    title="数据分析报告",
    slides=[
        {
            "type": "table",
            "title": "数据汇总",
            "headers": ["项目", "数值", "占比"],
            "data": [
                ["A项目", 1500, "30%"],
                ["B项目", 2500, "50%"],
                ["C项目", 1000, "20%"],
            ]
        }
    ]
)
```

## API 参考

### ExcelTool

| 方法 | 参数 | 说明 |
|------|------|------|
| `create_workbook` | filename, data, sheet_name | 创建基础工作簿 |
| `create_formatted_report` | filename, title, headers, data, styles | 创建格式化报表 |
| `add_image` | filename, sheet_name, image_path, cell | 插入图片 |
| `set_column_width` | filename, sheet_name, column, width | 设置列宽 |

### PPTTool

| 方法 | 参数 | 说明 |
|------|------|------|
| `create_presentation` | filename, slides | 创建演示文稿 |
| `create_report_presentation` | filename, title, slides | 创建报告类型演示文稿 |
| `add_slide` | slide_type, title, content | 添加幻灯片 |

## 依赖库

- `openpyxl>=3.0.0` - Excel 文件读写
- `python-pptx>=0.6.23` - PPT 文件生成

## 安装

```bash
pip install -r requirements.txt
```

## 注意事项

1. 生成的 Excel 文件默认保存在当前工作目录
2. PPT 文件支持 .pptx 格式
3. 颜色使用十六进制格式（如 "FF0000" 表示红色）
4. 图片支持 PNG、JPG 格式
