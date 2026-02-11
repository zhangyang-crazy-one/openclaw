#!/usr/bin/env python3
"""
完整提取 Awesome-Nano-Banana-images 仓库中的所有提示词
"""
import re
import json
from pathlib import Path


def extract_all_prompts():
    """提取所有提示词"""
    readme_path = Path(__file__).parent.parent / "repo" / "README.md"
    content = readme_path.read_text(encoding='utf-8')
    
    all_cases = []
    
    # ===== Nano Banana Pro =====
    pro_section = content[content.find("## 🍌 Nano Banana Pro 例子"):]
    pro_section = pro_section[:pro_section.find("## 🖼️ Nano Banana 例子")]
    pro_blocks = pro_section.split('<!-- 例 ')
    
    print(f"Nano Banana Pro: {len(pro_blocks)-1} 个案例\n")
    
    for i, block in enumerate(pro_blocks[1:], 1):
        if not block.strip():
            continue
        
        # 提取标题 (格式: "例号: 标题（by @作者）" 或 "例号: 标题（by @作者)）-->")
        title_match = re.match(r'(\d+): ([^（]+)（([^)]+)）', block)
        
        if title_match:
            title = title_match.group(2).strip()
            author = title_match.group(3).strip()
        else:
            # 备选方案
            title_match = re.search(r'例 \d+:? \[([^\]]+)\]', block)
            author_match = re.search(r'（by @([^）]+)）', block)
            title = title_match.group(1).strip() if title_match else f"案例 {i}"
            author = author_match.group(1).strip() if author_match else "unknown"
        
        # 提取提示词
        prompt_match = re.search(r'```\s*\n([\s\S]*?)\n```', block)
        prompt = prompt_match.group(1).strip() if prompt_match else ""
        
        # 提取输入类型
        input_type = "none"
        if "需上传" in block:
            input_type = "image" if "图片" in block else "text"
        
        # 提取标签
        tags = extract_tags(block[:1500])
        
        # 提取变量
        variables = extract_variables(prompt)
        
        case = {
            "id": f"pro_{i}",
            "title": title,
            "author": author.lstrip('@'),
            "prompt": prompt,
            "input_type": input_type,
            "tags": tags,
            "variables": variables,
            "category": "pro",
            "url": f"https://x.com/{author}/status/{i}"
        }
        
        all_cases.append(case)
        print(f"{i}. {title} (@{author})")
    
    # ===== Nano Banana =====
    nano_section = content[content.find("## 🖼️ Nano Banana 例子"):]
    nano_section = nano_section[:nano_section.find("## 🙏 Acknowledge")]
    nano_blocks = nano_section.split('<!-- 例 ')
    
    nano_start = len(all_cases)
    
    print(f"\n\nNano Banana: {len(nano_blocks)-1} 个案例\n")
    
    for i, block in enumerate(nano_blocks[1:], 1):
        if not block.strip():
            continue
        
        # 提取标题
        title_match = re.match(r'(\d+): ([^（]+)（([^)]+)）', block)
        
        if title_match:
            title = title_match.group(2).strip()
            author = title_match.group(3).strip()
        else:
            title_match = re.search(r'例 \d+:? \[([^\]]+)\]', block)
            author_match = re.search(r'（by @([^）]+)）', block)
            title = title_match.group(1).strip() if title_match else f"案例 {nano_start + i}"
            author = author_match.group(1).strip() if author_match else "community"
        
        # 提取提示词
        prompt_match = re.search(r'```\s*\n([\s\S]*?)\n```', block)
        prompt = prompt_match.group(1).strip() if prompt_match else ""
        
        # 提取输入类型
        input_type = "none"
        if "需上传" in block or "参考图片" in block:
            input_type = "image"
        
        # 提取标签
        tags = extract_tags(block[:1500])
        
        # 提取变量
        variables = extract_variables(prompt)
        
        case = {
            "id": f"nano_{nano_start + i}",
            "title": title,
            "author": author.lstrip('@'),
            "prompt": prompt,
            "input_type": input_type,
            "tags": tags,
            "variables": variables,
            "category": "nano",
            "url": f"https://x.com/{author}/status/{nano_start + i}"
        }
        
        all_cases.append(case)
        print(f"{nano_start + i}. {title} (@{author})")
    
    # ===== 保存 =====
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    output_file = data_dir / "prompts_full.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n✅ 保存 {len(all_cases)} 个提示词")
    
    generate_index(all_cases, data_dir)
    
    return all_cases


def extract_tags(text: str) -> list:
    """提取标签"""
    tags = []
    text_lower = text.lower()
    
    tag_keywords = {
        "儿童教育": ["儿童", "识字", "教育", "学习", "孩子"],
        "数字学习": ["数字", "count", "1-10"],
        "颜色学习": ["颜色", "color", "彩虹"],
        "场景": ["场景", "scene", "教室", "动物园", "农场", "家庭", "公园", "房间"],
        "动物": ["动物", "zoo", "farm", "animal", "宠物"],
        "3D": ["3D", "等距", "isometric", "微缩"],
        "照片处理": ["照片", "自拍", "photo", "相机"],
        "卡通风格": ["卡通", "动漫", "cartoon", "漫画", "anime"],
        "材质": ["材质", "texture", "贴图", "material"],
        "特效": ["特效", "effect", "故障", "glitch"],
        "信息图表": ["信息图", "流程图", "infographic", "海报", "报告"],
        "PIXAR风格": ["PIXAR", "pixar"],
        "角色设计": ["角色", "人物", "角色设计", "角色设定", "coser"],
        "游戏设计": ["游戏", "game"],
        "地图生成": ["地图", "map"],
        "食物": ["食物", "food", "美食"],
        "产品设计": ["产品", "product", "包装", "商品"],
        "风格化": ["风格", "style", "风格化"],
    }
    
    for tag, keywords in tag_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                if tag not in tags:
                    tags.append(tag)
                break
    
    return tags


def extract_variables(prompt: str) -> list:
    """提取变量"""
    variables = []
    
    # 匹配各种变量格式
    patterns = [
        r'[【\[\{]([^}\]]{1,20})[】\]\}]',  # 中文括号
        r'\{([a-zA-Z][^}]{1,30})\}',  # 英文变量
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, prompt)
        for var in matches:
            var = var.strip()
            if var and len(var) > 1:
                formatted = f"[{var}]" if pattern == patterns[0] else f"{{{var}}}"
                if formatted not in variables:
                    variables.append(formatted)
    
    return variables


def generate_index(cases: list, data_dir: Path):
    """生成索引"""
    
    tag_groups = {}
    for case in cases:
        for tag in case.get("tags", []):
            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(case["id"])
    
    index_file = data_dir / "prompts_index.json"
    
    index = {
        "total_cases": len(cases),
        "categories": {
            "pro": len([c for c in cases if c["category"] == "pro"]),
            "nano": len([c for c in cases if c["category"] == "nano"])
        },
        "tag_groups": tag_groups,
        "all_tags": sorted(list(tag_groups.keys()))
    }
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 索引: {index['total_cases']} 案例, {len(index['all_tags'])} 标签")


if __name__ == "__main__":
    extract_all_prompts()
