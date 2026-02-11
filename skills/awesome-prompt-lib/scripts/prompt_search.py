"""
Prompt Search Module

从 Awesome-Nano-Banana-images 仓库中搜索提示词
使用内置模板 + Git 仓库解析
"""
import json
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field

# 内置提示词模板
PROMPT_TEMPLATES = {
    "child_learning_scene": {
        "title": "儿童学习场景",
        "tags": ["儿童", "教育", "识字"],
        "prompt_template": """请生成一张儿童识字小报《{topic}》，竖版 A4，学习小报版式，适合 5–9 岁孩子认字与看图识物。

一、小报标题区（顶部）
顶部居中大标题：《{topic}识字小报》
风格：儿童学习报感

二、小报主体（中间主画面）
画面中心是一幅卡通插画风的「{scene}」场景
整体气氛：明亮、温暖、积极

三、核心词汇清单
{words_list}

四、词汇标签规则
格式：第一行拼音（带声调），第二行简体汉字

五、风格
风格：儿童绘本风
色彩：高饱和、明快、温暖""",
        "variables": ["topic", "scene", "words_list"]
    },
    
    "number_learning": {
        "title": "数字学习场景",
        "tags": ["儿童", "教育", "数字"],
        "prompt_template": """一幅数字学习场景插画，展示数字 1-10：
- ONE elephant with big ears
- TWO apples in basket
- THREE stars in sky
- FOUR butterflies in garden
- FIVE fish in pond
- SIX ducks near pond
- SEVEN birds on tree
- EIGHT cats playing
- NINE dogs running
- TEN frogs on lily pads

Large clear text labels for each number and animal.
Colorful educational illustration for children learning to count.""",
        "variables": []
    },
    
    "zoo_scene": {
        "title": "动物园场景",
        "tags": ["动物", "场景", "教育"],
        "prompt_template": """A beautiful illustrated ZOO SCENE showing:
- ELEPHANT near pond
- GIRAFFE eating leaves
- colorful BIRD on branch
- orange TIGER walking
- cute RABBIT in grass
- jumping FISH in pond

Numbers 1-6 clearly visible on each animal.
Large text labels: 'ONE ELEPHANT, TWO GIRAFFES, THREE BIRDS, FOUR TIGERS, FIVE RABBITS, SIX FISH' at bottom.
Cheerful children's educational illustration style.""",
        "variables": []
    },
    
    "color_learning": {
        "title": "颜色学习场景",
        "tags": ["儿童", "教育", "颜色"],
        "prompt_template": """A colorful RAINBOW SCENE with:
- RED apple
- ORANGE orange
- YELLOW sun
- GREEN frog on lily pad
- BLUE butterfly
- PURPLE grapes
- PINK flower

Large text labels: 'RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, RAINBOW, APPLE, SUN, FROG' at bottom.
Bright, cheerful educational illustration for children learning colors.""",
        "variables": []
    },
    
    "family_scene": {
        "title": "家庭场景",
        "tags": ["家庭", "场景", "儿童"],
        "prompt_template": """A warm HAPPY FAMILY SCENE at home:
- MOM cooking in kitchen with APPLE and BANANA on counter
- DAD reading newspaper with children on sofa
- cute CAT sleeping on armchair
- friendly DOG playing with toy
- colorful FISH swimming in aquarium

Large clear text labels: 'MOM, DAD, APPLE, BANANA, CAT, DOG, FISH, FAMILY, HOME, LOVE' at bottom.
Cozy, loving atmosphere. Educational illustration for children.""",
        "variables": []
    },
    
    "farm_scene": {
        "title": "农场场景",
        "tags": ["农场", "动物", "场景"],
        "prompt_template": """A fun FARM SCENE with:
- RED apple tree
- YELLOW corn field
- GREEN vegetable garden
- BLUE sky with clouds
- BROWN horse
- WHITE sheep
- GREY elephant
- ORANGE pumpkin

Large text labels: 'FARM, APPLE, CORN, VEGETABLES, SKY, HORSE, SHEEP, PUMPKIN, RED, YELLOW, GREEN, BLUE' at bottom.
Cheerful farm landscape for children's vocabulary learning.""",
        "variables": []
    },
    
    "body_parts": {
        "title": "身体部位学习",
        "tags": ["儿童", "教育", "身体"],
        "prompt_template": """A happy BABY LEARNING SCENE showing body parts:
- HEAD with eyes, nose, mouth, HAIR
- TWO HANDS with fingers, TEN FINGERS
- ARMS, BODY
- TWO LEGS with feet, TEN TOES
- EARS, CHEEKS, NOSE, MOUTH

Large text labels: 'HEAD, EYES, NOSE, MOUTH, HAIR, HANDS, FINGERS, ARMS, BODY, LEGS, FEET, TOES, BABY' at bottom.
Gentle, warm educational illustration.""",
        "variables": []
    },
    
    "action_words": {
        "title": "动作词汇学习",
        "tags": ["儿童", "教育", "动词"],
        "prompt_template": """A lively ACTION SCENE showing verbs:
- RUNNING boy
- JUMPING cat
- SWIMMING fish
- FLYING bird
- WALKING dog
- EATING apple
- DRINKING water
- SLEEPING cat
- PLAYING ball
- READING book

Large text labels: 'RUN, JUMP, SWIM, FLY, WALK, EAT, DRINK, SLEEP, PLAY, READ, SING, DANCE' at bottom.
Energetic, educational illustration for children learning action words.""",
        "variables": []
    },
    
    "pixar_style": {
        "title": "PIXAR 风格图片",
        "tags": ["风格", "动画", "PIXAR"],
        "prompt_template": """A stunning PIXAR-style animated image featuring {subject}.

Style characteristics:
- Expressive, large eyes with sparkles
- Soft, dreamy lighting with warm tones
- Volumetric lighting with visible light rays
- Shallow depth of field with soft bokeh
- Vibrant, saturated colors
- Smooth, clean textures
- Cute, appealing character design
- 8K resolution, cinematic composition

{additional_details}""",
        "variables": ["subject", "additional_details"]
    },
    
    "isometric_scene": {
        "title": "3D 等距场景",
        "tags": ["3D", "等距", "场景"],
        "prompt_template": """An isometric 3D scene showing {scene_description}.

Features:
- Isometric projection (30-degree angle)
- Clean, modern design
- Soft shadows and lighting
- Professional product visualization
- Neutral background
- High detail level

{additional_elements}""",
        "variables": ["scene_description", "additional_elements"]
    },
    
    "infographic": {
        "title": "信息图表",
        "tags": ["信息图", "图表", "数据"],
        "prompt_template": """A professional infographic about {topic}.

Elements:
- Clean, modern layout
- Clear hierarchy
- Engaging visuals
- Key statistics highlighted
- {data_points}
- Consistent color scheme
- Easy to understand

Style: Professional, clean, data-driven""",
        "variables": ["topic", "data_points"]
    },
    
    "material_texture": {
        "title": "材质贴图生成",
        "tags": ["材质", "纹理", "产品"],
        "prompt_template": """A high-quality material texture for {material_type}.

Characteristics:
- Photorealistic rendering
- High resolution (4K-8K)
- Seamless/tileable pattern
- Accurate material properties
- PBR-ready textures

The texture should show realistic {material_properties}.""",
        "variables": ["material_type", "material_properties"]
    }
}


@dataclass
class PromptCase:
    """提示词案例"""
    case_id: str
    title: str
    author: str = "system"
    prompt: str = ""
    input_type: str = "none"
    tags: list[str] = field(default_factory=list)
    url: str = ""
    output_example: str = ""


class PromptSearcher:
    """提示词搜索器"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"
        self.prompts_file = self.data_dir / "prompts.json"
        self.cases: list[PromptCase] = []
        
        # 从模板构建
        self._build_from_templates()
    
    def _build_from_templates(self):
        """从模板构建案例列表"""
        for template_id, template in PROMPT_TEMPLATES.items():
            case = PromptCase(
                case_id=f"template_{template_id}",
                title=template["title"],
                author="system",
                prompt=template["prompt_template"],
                input_type="none",
                tags=template["tags"]
            )
            self.cases.append(case)
    
    def search(self, query: str, limit: int = 10) -> List[PromptCase]:
        """搜索提示词"""
        query_lower = query.lower()
        query_words = query_lower.split()
        
        scored = []
        for case in self.cases:
            score = 0
            
            # 标题匹配
            if any(word in case.title.lower() for word in query_words):
                score += 10
            
            # 标签匹配
            for tag in case.tags:
                if any(word in tag.lower() for word in query_words):
                    score += 5
            
            # 精确匹配加分
            if query_lower in case.title.lower():
                score += 20
            
            if score > 0:
                scored.append((score, case))
        
        # 按分数排序
        scored.sort(key=lambda x: -x[0])
        
        return [case for _, case in scored[:limit]]
    
    def search_by_tags(self, tags: list[str], limit: int = 10) -> List[PromptCase]:
        """按标签搜索"""
        results = []
        for case in self.cases:
            if any(tag in case.tags for tag in tags):
                results.append(case)
        
        return results[:limit]
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for case in self.cases:
            tags.update(case.tags)
        return sorted(list(tags))
    
    def get_by_id(self, case_id: str) -> Optional[PromptCase]:
        """根据 ID 获取案例"""
        for case in self.cases:
            if case.case_id == case_id:
                return case
        return None
    
    def get_random(self, limit: int = 5) -> List[PromptCase]:
        """获取随机案例"""
        import random
        return random.sample(self.cases, min(limit, len(self.cases)))
    
    def list_templates(self) -> List[Dict]:
        """列出所有模板"""
        return [
            {
                "id": key,
                "title": t["title"],
                "tags": ", ".join(t["tags"]),
                "variables": ", ".join(t["variables"])
            }
            for key, t in PROMPT_TEMPLATES.items()
        ]


if __name__ == "__main__":
    searcher = PromptSearcher()
    
    print(f"📚 加载了 {len(searcher.cases)} 个提示词案例\n")
    
    # 列出所有模板
    print("可用模板:")
    for item in searcher.list_templates():
        print(f"  • {item['title']} ({item['tags']})")
    
    # 示例搜索
    print("\n🔍 搜索 '儿童 教育':")
    results = searcher.search("儿童 教育", limit=3)
    for case in results:
        print(f"  - {case.title}")
