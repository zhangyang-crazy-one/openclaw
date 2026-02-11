# Awesome Prompt Library Skill

基于 Awesome-Nano-Banana-images 仓库的提示词库技能。

## 概述

从高质量提示词库中搜索相关案例，自动适配生成图片。

## 安装

```bash
cd /home/liujerry/moltbot/skills/awesome-prompt-lib
uv pip install tiktoken orjson
```

## 使用方法

### 1. 搜索提示词

```python
from scripts.prompt_search import PromptSearcher

searcher = PromptSearcher()

# 关键词搜索
results = searcher.search("儿童 识字", limit=5)
# 返回相关案例列表

# 查看案例详情
for case in results:
    print(f"标题: {case.title}")
    print(f"提示词: {case.prompt}")
    print(f"标签: {case.tags}")
```

### 2. 适配提示词

```python
from scripts.prompt_adapter import PromptAdapter

adapter = PromptAdapter()

# 适配提示词到新场景
adapted = adapter.adapt(
    original_prompt="儿童识字小报《游乐园》...",
    new_context={"topic": "动物园", "words": ["狮子", "老虎", "熊猫"]}
)
print(adapted)
```

### 3. 完整工作流

```python
from scripts.prompt_workflow import PromptWorkflow

workflow = PromptWorkflow()

# 搜索 + 适配
result = workflow.generate(
    query="生成一个儿童英语学习场景",
    context={"words": ["apple", "banana", "cat"], "scene": "教室"}
)

if result:
    print(f"找到案例: {result['case_title']}")
    print(f"适配提示词: {result['adapted_prompt']}")
```

## 目录结构

```
awesome-prompt-lib/
├── data/
│   └── prompts.json      # 解析后的提示词库
├── scripts/
│   ├── __init__.py
│   ├── prompt_search.py  # 搜索模块
│   ├── prompt_adapter.py # 提示词适配模块
│   └── prompt_workflow.py # 完整工作流
├── repo/                 # Git 克隆的 Awesome-Nano-Banana-images
└── SKILL.md
```

## 命令行工具

```bash
# 搜索提示词
python3 scripts/cli.py search "儿童 识字"

# 适配提示词
python3 scripts/cli.py adapt "原提示词" --context '{"topic":"动物园"}'

# 生成提示词
python3 scripts/cli.py generate "我想生成儿童英语学习图片"

# 同步提示词库
python3 scripts/cli.py sync
```

## API 接口

### PromptSearcher

```python
searcher = PromptSearcher()

# 关键词搜索
results = searcher.search(query: str, limit: int = 10)

# 标签搜索
results = searcher.search_by_tags(tags: list[str], limit: int = 10)

# 获取所有标签
tags = searcher.get_all_tags()
```

### PromptAdapter

```python
adapter = PromptAdapter()

# 适配提示词
adapted = adapter.adapt(
    original_prompt: str,
    context: dict,
    preserve_structure: bool = True
)

# 提取变量
variables = adapter.extract_variables(prompt: str)
```

## 提示词库内容

仓库包含以下类型的案例：

- **儿童教育**: 识字小报、数字学习、英语场景
- **角色设计**: 游戏角色、动漫角色、人物设定
- **产品设计**: 材质贴图、包装设计、展示架
- **场景生成**: 城市地图、室内设计、微缩场景
- **特效处理**: 照片特效、材质转换、风格迁移
- **信息图表**: 数据可视化、流程图、海报

## 搜索示例

```python
# 搜索儿童相关
searcher.search("儿童 学习 识字")
searcher.search("children learning")

# 搜索场景相关
searcher.search("教室 classroom")
searcher.search("动物园 zoo")

# 搜索风格相关
searcher.search("卡通风格")
searcher.search("手绘 等距")
```

## 适配示例

```python
# 将儿童识字小报适配到动物园主题
adapter.adapt(
    original_prompt="儿童识字小报《游乐园》...",
    context={
        "topic": "动物园",
        "words": ["狮子", "老虎", "大象", "熊猫"],
        "scene": "动物园入口",
        "style": "儿童绘本风"
    }
)
```

## 注意事项

- 提示词库会自动从 Git 仓库同步
- 搜索使用语义匹配，支持中文和英文
- 适配时会保留原始提示词结构
- 部分提示词需要额外输入参数（用 `{}` 标注）
