# OpenDataLoader PDF 技能

## 概述

**OpenDataLoader PDF** 是 GitHub 上顶级的开源 PDF 解析工具，专注于 AI -ready 数据提取和 PDF 无障碍自动化。

| 指标       | 数值                                                                                                      |
| ---------- | --------------------------------------------------------------------------------------------------------- |
| ⭐ Stars   | 14,565                                                                                                    |
| 🍴 Forks   | 1,237                                                                                                     |
| 💻 语言    | Java + Python                                                                                             |
| 📄 License | Apache 2.0                                                                                                |
| 创建时间   | 2025-05-13                                                                                                |
| GitHub     | [opendataloader-project/opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) |

## 核心能力

### 数据提取

| 功能                    | 支持情况   | 备注                 |
| ----------------------- | ---------- | -------------------- |
| 文本提取 + 正确阅读顺序 | ✅         | XY-Cut++ 算法        |
| Bounding Box 坐标       | ✅         | 精确到 [x1,y1,x2,y2] |
| 表格提取（简单/复杂）   | ✅         | Hybrid 模式更准      |
| OCR（80+语言）          | ✅         | Hybrid 模式          |
| 公式提取（LaTeX）       | ✅         | Hybrid 模式          |
| 图表描述 AI 生成        | ✅         | Hybrid 模式          |
| 自动 Tagged PDF         | ⏳ Q2 2026 | 免费                 |

### Benchmark 性能 (#1)

在 200 份真实 PDF 测试集上综合准确率 **0.907**，表格提取 **0.928**。

| 引擎                    | 综合分    | 速度     |
| ----------------------- | --------- | -------- |
| opendataloader [hybrid] | **0.907** | 0.46s/页 |
| docling                 | 0.882     | 0.76s/页 |
| marker                  | 0.861     | 53.9s/页 |

## 安装

### 依赖要求

- **Java 11+** (必需，本地引擎)
- Python 3.10+

### 安装步骤

```bash
# 1. 安装 Python 包
pip install opendataloader-pdf

# 2. 安装 Java ( Adoptium/Eclipse Temurin)
# 下载地址: https://adoptium.net/
# 或使用包管理器:
#   Ubuntu/Debian: sudo apt install openjdk-17-jdk-headless
#   macOS: brew install openjdk@17
#   Windows: 下载 MSI 安装包

# 3. 验证安装
java -version  # 应显示 17.x.x 或更高
opendataloader-pdf --version  # 应显示版本号
```

### Java 安装 (无 sudo)

```bash
# 方法1: 下载 portable JDK 到用户目录
mkdir -p ~/tools/java
cd ~/tools/java
wget https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.13%2B11/OpenJDK17U-jdk_x64_linux_hotspot_17.0.13_11.tar.gz
tar -xzf OpenJDK17U-jdk_x64_linux_hotspot_17.0.13_11.tar.gz
export PATH=$HOME/tools/java/jdk-17.0.13+11/bin:$PATH

# 方法2: 使用 conda (如果有)
conda install -c conda-forge openjdk=17
```

## 使用方法

### Python API

```python
import opendataloader_pdf

# 基本转换 (输出 JSON + Markdown)
opendataloader_pdf.convert(
    input_path=["document.pdf", "folder/"],
    output_dir="output/",
    format="json,markdown"
)

# 只输出 Markdown
opendataloader_pdf.convert(
    input_path="report.pdf",
    output_dir="output/",
    format="markdown"
)

# 输出带坐标的 JSON (用于 RAG 引用)
opendataloader_pdf.convert(
    input_path="annual_report.pdf",
    output_dir="output/",
    format="json"  # JSON 包含每元素的 bounding box
)
```

### 命令行

```bash
# 基本用法
opendataloader-pdf input.pdf -o output/

# 输出多种格式
opendataloader-pdf input.pdf -o output/ --format json,markdown,html

# 使用 Hybrid 模式 (复杂表格/扫描件)
pip install "opendataloader-pdf[hybrid]"
opendataloader-pdf-hybrid --port 5002  # Terminal 1: 启动服务
opendataloader-pdf --hybrid docling-fast input.pdf  # Terminal 2: 转换
```

### 输出格式

**JSON** (含 bounding boxes):

```json
{
  "pages": [
    {
      "page_number": 1,
      "width": 612,
      "height": 792,
      "elements": [
        {
          "type": "heading",
          "bbox": [72, 72, 540, 100],
          "text": "Annual Report 2024"
        },
        {
          "type": "table",
          "bbox": [72, 120, 540, 300],
          "rows": [...]
        }
      ]
    }
  ]
}
```

**Markdown**:

```markdown
# Annual Report 2024

## Financial Highlights

| Metric     | Value  |
| ---------- | ------ |
| Revenue    | $10.2B |
| Net Income | $2.1B  |

## Analysis

Text content here...
```

## 在股票报告技能中的应用

### V4 技能中的 PDF 解析工作流

当需要从 PDF 提取财务数据时使用：

```python
import opendataloader_pdf

def extract_financial_data_from_pdf(pdf_path: str, output_dir: str) -> dict:
    """从 PDF 提取财务数据用于股票报告"""

    # 转换为 JSON (保留结构化数据)
    opendataloader_pdf.convert(
        input_path=pdf_path,
        output_dir=output_dir,
        format="json",
        quiet=True
    )

    # 读取转换后的 JSON
    import json
    with open(f"{output_dir}/{pdf_path.name}.json") as f:
        data = json.load(f)

    return data
```

### 使用场景

1. **年报/季报解析** - 提取表格数据（ROE、毛利率等）
2. **招股说明书** - 提取业务描述、供应链信息
3. **券商研报** - 提取投资建议、数据
4. **监管文件** - 提取政策文本

### 与现有技能集成

在 V4 股票报告技能中，可以通过 agent-browser 下载 PDF 后使用 OpenDataLoader 解析：

```python
# 1. 下载 PDF
browser action=open url="https://example.com/annual_report.pdf"

# 2. 使用 OpenDataLoader 解析
opendataloader_pdf.convert(
    input_path="annual_report.pdf",
    output_dir="/tmp/parsed/",
    format="json,markdown"
)
```

## 故障排除

### Java 未找到

```
Error: 'java' command not found
```

**解决**: 安装 Java 11+ 并添加到 PATH

### 中文 PDF 乱码

```python
opendataloader_pdf.convert(
    input_path="chinese.pdf",
    output_dir="output/",
    format="json",
    replace_invalid_chars="?"  # 替换无法识别的字符
)
```

### 表格提取不准确

使用 Hybrid 模式：

```bash
pip install "opendataloader-pdf[hybrid]"
opendataloader-pdf input.pdf --hybrid docling-fast
```

### 内存不足

```python
# 分批处理
for pdf in pdf_list:
    opendataloader_pdf.convert(
        input_path=pdf,
        output_dir="output/",
        format="json",
        quiet=True
    )
```

## 相关资源

- **官网**: https://opendataloader.org
- **GitHub**: https://github.com/opendataloader-project/opendataloader-pdf
- **文档**: https://opendataloader.org/docs
- **Benchmark**: https://github.com/opendataloader-project/opendataloader-bench
- **LangChain 集成**: https://github.com/opendataloader-project/langchain-opendataloader-pdf

## 更新日志

- **2026-04-11**: 技能创建，版本 1.0.0
