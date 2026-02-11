"""
简化的提示词库 - 包含最常用的案例
"""
from typing import Dict, List, Any


# 预定义的提示词模板
PROMPT_TEMPLATES = {
    # 儿童学习场景
    "child_learning_scene": {
        "title": "儿童学习场景",
        "tags": ["儿童", "教育", "识字"],
        "prompt_template": """请生成一张儿童识字小报《{topic}》，竖版 A4，学习小报版式，适合 5–9 岁孩子认字与看图识物。

一、小报标题区（顶部）
顶部居中大标题：《{topic}识字小报》
风格：儿童学习报感
文本要求：大字、醒目、卡通手写体、彩色描边

二、小报主体（中间主画面）
画面中心是一幅卡通插画风的「{scene}」场景
整体气氛：明亮、温暖、积极
构图：物体边界清晰，方便对应文字

三、核心词汇清单
请务必在画面中清晰绘制以下词汇：
{words_list}

四、词汇标签规则
对上述清单中的物体，贴上标签：
格式：第一行拼音（带声调），第二行简体汉字
样式：彩色小贴纸风格，白底黑字

五、风格
风格：儿童绘本风
色彩：高饱和、明快、温暖
质量：8k resolution, high detail""",
        "variables": ["topic", "scene", "words_list"]
    },
    
    # 数字学习场景
    "number_learning": {
        "title": "数字学习场景",
        "tags": ["儿童", "教育", "数字"],
        "prompt_template": """一幅数字学习场景插画，展示数字 1-10：

画面包含：
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
    
    # 动物园场景
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
    
    # 颜色学习
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

Large text labels: 'RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, RAINBOW, APPLE, SUN, FROG, BUTTERFLY, GRAPES, FLOWER' at bottom.
Bright, cheerful educational illustration for children learning colors.""",
        "variables": []
    },
    
    # 家庭场景
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
    
    # 农场场景
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

Large text labels: 'FARM, APPLE, CORN, VEGETABLES, SKY, HORSE, SHEEP, ELEPHANT, PUMPKIN, RED, YELLOW, GREEN, BLUE, BROWN, WHITE, GREY' at bottom.
Cheerful farm landscape for children's vocabulary learning.""",
        "variables": []
    },
    
    # 身体部位
    "body_parts": {
        "title": "身体部位学习",
        "tags": ["儿童", "教育", "身体"],
        "prompt_template": """A happy BABY LEARNING SCENE showing body parts:
- HEAD with eyes, nose, mouth, HAIR
- TWO HANDS with fingers, TEN FINGERS
- ARMS, BODY
- TWO LEGS with feet, TEN TOES
- EARS, CHEEKS, NOSE, MOUTH

Large text labels: 'HEAD, EYES, NOSE, MOUTH, HAIR, HANDS, FINGERS, ARMS, BODY, LEGS, FEET, TOES, EARS, CHEEKS, BABY, BODY PARTS' at bottom.
Gentle, warm educational illustration.""",
        "variables": []
    },
    
    # 动作/动词
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
- SINGING bird
- DANCING children

Large text labels: 'RUN, JUMP, SWIM, FLY, WALK, EAT, DRINK, SLEEP, PLAY, READ, SING, DANCE, ACTIONS, MOVE' at bottom.
Energetic, educational illustration for children learning action words.""",
        "variables": []
    },
    
    # PIXAR 风格
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
- Warm amber highlights
- Smooth, clean textures
- Cute, appealing character design
- Expressive body language
- 8K resolution, cinematic composition

{additional_details}""",
        "variables": ["subject", "additional_details"]
    },
    
    # 3D 等距场景
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
- 4K quality

{additional_elements}""",
        "variables": ["scene_description", "additional_elements"]
    },
    
    # 信息图表
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
    
    # 材质贴图
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
- Clean, professional presentation

The texture should show realistic {material_properties}.""",
        "variables": ["material_type", "material_properties"]
    }
}


class SimplePromptLibrary:
    """简化提示词库"""
    
    def __init__(self):
        self.templates = PROMPT_TEMPLATES
    
    def list_templates(self) -> List[Dict[str, str]]:
        """列出所有模板"""
        return [
            {
                "id": key,
                "title": t["title"],
                "tags": ", ".join(t["tags"]),
                "variables": ", ".join(t["variables"])
            }
            for key, t in self.templates.items()
        ]
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """获取模板"""
        return self.templates.get(template_id, None)
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """搜索模板"""
        query_lower = query.lower()
        results = []
        
        for key, template in self.templates.items():
            score = 0
            
            # 标题匹配
            if query_lower in template["title"].lower():
                score += 10
            
            # 标签匹配
            for tag in template["tags"]:
                if query_lower in tag.lower():
                    score += 5
            
            if score > 0:
                results.append((score, {
                    "id": key,
                    "title": template["title"],
                    "tags": ", ".join(template["tags"]),
                    "score": score
                }))
        
        results.sort(key=lambda x: -x[0])
        return [r[1] for r in results[:limit]]
    
    def get_by_tags(self, tags: List[str], limit: int = 5) -> List[Dict[str, str]]:
        """按标签获取"""
        results = []
        
        for key, template in self.templates.items():
            for tag in tags:
                if tag.lower() in [t.lower() for t in template["tags"]]:
                    results.append({
                        "id": key,
                        "title": template["title"],
                        "tags": ", ".join(template["tags"])
                    })
                    break
        
        return results[:limit]
    
    def adapt(
        self,
        template_id: str,
        values: Dict[str, str]
    ) -> str:
        """适配模板"""
        template = self.templates.get(template_id)
        if not template:
            return ""
        
        prompt = template["prompt_template"]
        for key, value in values.items():
            prompt = prompt.replace(f"{{{key}}}", value)
        
        return prompt


# 便捷函数
def get_prompt_library():
    return SimplePromptLibrary()


def quick_search(query: str):
    """快速搜索"""
    lib = get_prompt_library()
    return lib.search(query)


def use_template(template_id: str, **values) -> str:
    """使用模板"""
    lib = get_prompt_library()
    return lib.adapt(template_id, values)


if __name__ == "__main__":
    lib = get_prompt_library()
    
    print("📚 可用的提示词模板:\n")
    for item in lib.list_templates():
        print(f"  • {item['title']}")
        print(f"    标签: {item['tags']}")
        print()
    
    # 测试搜索
    print("\n🔍 搜索 '儿童':")
    results = lib.search("儿童")
    for r in results:
        print(f"  - {r['title']}")
