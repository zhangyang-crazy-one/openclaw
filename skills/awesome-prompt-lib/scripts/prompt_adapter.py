"""
Prompt Adapter Module

适配提示词到新的场景和需求
"""
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AdaptationResult:
    """适配结果"""
    adapted_prompt: str
    variables: Dict[str, str]
    warnings: list[str]


class PromptAdapter:
    """提示词适配器"""
    
    # 常见替换模式
    REPLACEMENT_PATTERNS = {
        # 儿童教育场景
        "儿童": {
            "children": ["kids", "children", "child"],
            "学习": ["learning", "education", "study"]
        },
        # 场景类型
        "教室": ["classroom", "school room", "class room"],
        "动物园": ["zoo", "animal park", "wildlife"],
        "游乐园": ["amusement park", "theme park", "playground"],
        "家庭": ["home", "family house", "family setting"],
        "农场": ["farm", "farmyard", "ranch"],
    }
    
    def __init__(self):
        pass
    
    def adapt(
        self,
        original_prompt: str,
        context: Dict[str, Any],
        preserve_structure: bool = True
    ) -> AdaptationResult:
        """
        适配提示词
        
        Args:
            original_prompt: 原始提示词
            context: 上下文（包含 topic, words, scene, style 等）
            preserve_structure: 是否保留原始结构
        
        Returns:
            AdaptationResult: 适配结果
        """
        adapted = original_prompt
        variables = {}
        warnings = []
        
        # 提取需要替换的占位符
        placeholders = self._extract_placeholders(original_prompt)
        
        # 替换占位符
        for placeholder in placeholders:
            key = placeholder.strip("{}")
            if key in context:
                adapted = adapted.replace(placeholder, context[key])
                variables[key] = context[key]
            else:
                warnings.append(f"缺少变量: {key}")
        
        # 根据场景适配
        topic = context.get("topic", "")
        scene = context.get("scene", "")
        style = context.get("style", "")
        words = context.get("words", [])
        
        # 替换主题相关词汇
        adapted = self._replace_topic_words(adapted, topic, context)
        
        # 替换场景描述
        if scene:
            adapted = adapted.replace("场景描述", scene)
            adapted = self._enhance_scene(adapted, scene, style)
        
        # 替换具体词汇
        if words:
            adapted = self._replace_words(adapted, words)
        
        # 添加/修改标签
        if topic:
            adapted = self._add_labels(adapted, words, topic)
        
        return AdaptationResult(
            adapted_prompt=adapted,
            variables=variables,
            warnings=warnings
        )
    
    def _extract_placeholders(self, prompt: str) -> list[str]:
        """提取占位符"""
        pattern = r'\[([^\]]+)\]|\{([^}]+)\}'
        matches = re.findall(pattern, prompt)
        
        placeholders = []
        for m in matches:
            placeholders.extend([x for x in m if x])
        
        return placeholders
    
    def _replace_topic_words(
        self,
        prompt: str,
        topic: str,
        context: Dict[str, Any]
    ) -> str:
        """替换主题相关词汇"""
        topic_lower = topic.lower()
        
        # 根据主题类型替换
        if "动物" in topic or "zoo" in topic_lower:
            words = context.get("words", ["elephant", "lion", "panda"])
            prompt = prompt.replace("游乐园", "动物园")
            prompt = prompt.replace("游乐设施", "动物围栏")
            prompt = prompt.replace("售票处", "动物介绍牌")
        
        elif "教室" in topic or "classroom" in topic_lower:
            prompt = prompt.replace("动物园", "教室")
            prompt = prompt.replace("动物", "学习用品")
        
        elif "家庭" in topic or "home" in topic_lower:
            prompt = prompt.replace("游乐场", "客厅")
        
        return prompt
    
    def _enhance_scene(
        self,
        prompt: str,
        scene: str,
        style: str
    ) -> str:
        """增强场景描述"""
        if not scene:
            return prompt
        
        # 添加场景细节
        scene_enhancements = []
        
        if "教室" in scene:
            scene_enhancements = [
                "明亮的教室",
                "整洁的课桌椅",
                "绿板/白板",
                "窗外阳光"
            ]
        elif "动物园" in scene:
            scene_enhancements = [
                "绿色植被",
                "动物围栏",
                "游客步道",
                "指示牌"
            ]
        elif "农场" in scene:
            scene_enhancements = [
                "蓝天白云",
                "绿色草地",
                "木围栏",
                "谷仓"
            ]
        
        if scene_enhancements:
            scene_text = "场景包含: " + ", ".join(scene_enhancements)
            if "场景描述" not in prompt:
                prompt += f"\n\n{scene_text}"
        
        return prompt
    
    def _replace_words(self, prompt: str, words: list[str]) -> str:
        """替换具体词汇"""
        if not words:
            return prompt
        
        words_str = ", ".join(words)
        
        # 替换常见的词汇列表位置
        if "清单" in prompt or "list" in prompt.lower():
            prompt = prompt.replace("必画物体与识字清单", f"核心词汇: {words_str}")
        
        elif "物体" in prompt:
            prompt = prompt.replace("物体", f"词汇: {words_str}")
        
        # 如果提示词中有固定的词汇位置，用新词汇替换
        if "、" in prompt:
            # 尝试找出词汇替换的位置
            word_pattern = r'[^\s,、]{2,10}(?:[、,]\s*[^\s,、]{2,10}){2,}'
            if re.search(word_pattern, prompt):
                prompt = re.sub(
                    word_pattern,
                    words_str,
                    prompt,
                    count=1
                )
        
        return prompt
    
    def _add_labels(
        self,
        prompt: str,
        words: list[str],
        topic: str
    ) -> str:
        """添加标签"""
        labels = []
        
        # 添加主题标签
        labels.append(topic)
        
        # 添加词汇标签
        if words:
            # 限制标签数量
            display_words = words[:5] if len(words) > 5 else words
            labels.extend(display_words)
        
        if labels:
            labels_str = ", ".join(labels)
            if "标签" not in prompt.lower():
                prompt += f"\n\n词汇标签: {labels_str}"
        
        return prompt
    
    def extract_variables(self, prompt: str) -> Dict[str, str]:
        """提取提示词中的变量"""
        variables = {}
        
        # 提取 [] 类型的变量
        bracket_vars = re.findall(r'\[([^\]]+)\]', prompt)
        for var in bracket_vars:
            if var not in variables:
                variables[f"[{var}]"] = ""
        
        # 提取 {} 类型的变量
        brace_vars = re.findall(r'\{([^\}]+)\}', prompt)
        for var in brace_vars:
            if var not in variables:
                variables[f"{{{var}}}"] = ""
        
        return variables
    
    def get_required_inputs(self, prompt: str) -> list[str]:
        """获取提示词需要的输入"""
        inputs = []
        
        # 检查特定模式的提示词
        if "需要的信息" in prompt or "输入" in prompt:
            # 提取需要填写的字段
            field_pattern = r'([^\s：:]+)[：:]\[?[^\]]*\]?'
            matches = re.findall(field_pattern, prompt)
            for match in matches[:10]:  # 限制数量
                if len(match) > 2 and match not in ["提示词", "Note", "输入"]:
                    inputs.append(match.strip())
        
        return inputs[:10]
    
    def adapt_for_child_learning(
        self,
        topic: str,
        words: list[str],
        scene: str = "",
        age_group: str = "5-9"
    ) -> str:
        """专为儿童学习场景生成提示词"""
        
        if not words:
            return ""
        
        # 构建提示词
        prompt_parts = []
        
        # 标题
        prompt_parts.append(f"儿童识字小报《{topic}》")
        prompt_parts.append("适合 5-9 岁孩子认字与看图识物")
        
        # 主体场景
        if scene:
            prompt_parts.append(f"\n画面中心是一幅卡通插画风的「{scene}」场景")
            prompt_parts.append("整体气氛：明亮、温暖、积极")
        else:
            prompt_parts.append(f"\n画面中心是一幅卡通插画风的「{topic}」场景")
        
        # 核心词汇
        prompt_parts.append("\n必画物体与词汇清单：")
        for i, word in enumerate(words[:15], 1):
            prompt_parts.append(f"{i}. {word}")
        
        # 标签格式
        prompt_parts.append("\n词汇标签格式：")
        prompt_parts.append("第一行：拼音（带声调）")
        prompt_parts.append("第二行：简体汉字")
        
        # 风格
        prompt_parts.append("\n风格：儿童绘本风")
        prompt_parts.append("色彩：高饱和、明快、温暖")
        prompt_parts.append("质量：8k resolution, high detail")
        
        return "\n".join(prompt_parts)
    
    def adapt_for_scene_generation(
        self,
        scene_type: str,
        elements: list[str],
        style: str = "卡通"
    ) -> str:
        """为场景生成适配提示词"""
        
        elements_str = ", ".join(elements)
        
        prompt = f"""一个{style}风格的{scene_type}场景。

核心元素：{elements_str}

场景包含多个互动区域，人物自然分布在场景中。
整体构图清晰，色彩明亮，适合教学展示。"""
        
        return prompt


if __name__ == "__main__":
    adapter = PromptAdapter()
    
    # 测试适配
    original = """请生成一张儿童识字小报《游乐园》...
必画物体：售票处, 过山车, 摩天轮, 旋转木马
标签格式：拼音 + 汉字"""

    result = adapter.adapt(
        original_prompt=original,
        context={
            "topic": "动物园",
            "words": ["狮子", "老虎", "大象", "熊猫"],
            "scene": "动物园入口",
            "style": "儿童绘本风"
        }
    )
    
    print("=" * 50)
    print("原始提示词:")
    print(original[:100])
    print("\n适配结果:")
    print(result.adapted_prompt)
    print("\n警告:", result.warnings if result.warnings else "无")
