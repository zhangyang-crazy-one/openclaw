"""
Complete Workflow Module

完整的提示词工作流：搜索 -> 适配 -> 生成
"""
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .prompt_search import PromptSearcher
from .prompt_adapter import PromptAdapter


@dataclass
class WorkflowResult:
    """工作流结果"""
    success: bool
    case_title: str
    adapted_prompt: str
    warnings: list[str]
    search_results: list


class PromptWorkflow:
    """提示词工作流"""
    
    def __init__(self):
        self.searcher = PromptSearcher()
        self.adapter = PromptAdapter()
    
    def generate(
        self,
        query: str,
        context: Dict[str, Any],
        limit: int = 5
    ) -> Optional[WorkflowResult]:
        """
        完整工作流：搜索 + 适配
        
        Args:
            query: 搜索查询
            context: 适配上下文
            limit: 返回结果数量限制
        
        Returns:
            WorkflowResult: 工作流结果
        """
        # 1. 搜索相关案例
        results = self.searcher.search(query, limit=limit)
        
        if not results:
            return WorkflowResult(
                success=False,
                case_title="",
                adapted_prompt="",
                warnings=["未找到相关提示词"],
                search_results=[]
            )
        
        # 2. 选择最佳案例（选择第一个）
        best_case = results[0]
        
        # 3. 适配提示词
        adaptation = self.adapter.adapt(
            original_prompt=best_case.prompt,
            context=context,
            preserve_structure=True
        )
        
        return WorkflowResult(
            success=True,
            case_title=best_case.title,
            adapted_prompt=adaptation.adapted_prompt,
            warnings=adaptation.warnings,
            search_results=[{"title": r.title, "score": i+1} for i, r in enumerate(results)]
        )
    
    def generate_with_refinement(
        self,
        query: str,
        context: Dict[str, Any],
        refinement: str = ""
    ) -> WorkflowResult:
        """
        带精炼的工作流
        
        在基础适配后，根据用户反馈精炼提示词
        """
        result = self.generate(query, context)
        
        if result.success and refinement:
            # 精炼适配
            refined_prompt = result.adapted_prompt
            
            # 添加精炼要求
            if refinement:
                refined_prompt += f"\n\n精炼要求：{refinement}"
            
            result.adapted_prompt = refined_prompt
            result.warnings.append(f"已添加精炼要求: {refinement}")
        
        return result
    
    def quick_generate(
        self,
        topic: str,
        words: list[str],
        scene: str = ""
    ) -> str:
        """
        快速生成儿童学习提示词
        
        Args:
            topic: 主题（如"动物园"、"教室"）
            words: 词汇列表
            scene: 场景描述
        
        Returns:
            str: 适配后的提示词
        """
        # 如果没有找到相关案例，使用内置模板
        results = self.searcher.search(topic, limit=3)
        
        if results:
            # 使用搜索到的案例适配
            context = {
                "topic": topic,
                "words": words,
                "scene": scene or f"{topic}场景"
            }
            result = self.generate(topic, context)
            return result.adapted_prompt if result.success else ""
        else:
            # 使用适配器内置模板
            return self.adapter.adapt_for_child_learning(
                topic=topic,
                words=words,
                scene=scene,
                age_group="5-9"
            )
    
    def find_similar(self, prompt: str, limit: int = 5) -> list:
        """找到相似的提示词"""
        return self.searcher.search(prompt, limit)
    
    def recommend_by_tags(self, tags: list[str], limit: int = 5) -> list:
        """根据标签推荐"""
        return self.searcher.search_by_tags(tags, limit)
    
    def analyze_request(self, request: str) -> Dict[str, Any]:
        """
        分析用户请求，提取关键信息
        
        Args:
            request: 用户请求（如"生成儿童英语学习图片"）
        
        Returns:
            Dict: 提取的上下文信息
        """
        request_lower = request.lower()
        
        context = {
            "topic": "",
            "words": [],
            "scene": "",
            "style": "卡通",
            "age_group": "5-9"
        }
        
        # 提取主题
        topics = ["动物园", "教室", "家庭", "农场", "游乐园", "厨房", "卧室", "花园"]
        for topic in topics:
            if topic in request:
                context["topic"] = topic
                break
        else:
            if "儿童" in request or "children" in request_lower:
                context["topic"] = "儿童学习"
            if "英语" in request or "english" in request_lower:
                context["topic"] = "英语学习"
        
        # 提取风格
        if "卡通" in request or "cartoon" in request_lower:
            context["style"] = "卡通"
        elif "写实" in request or "真实" in request:
            context["style"] = "写实"
        elif "水墨" in request or "国风" in request:
            context["style"] = "水墨国风"
        
        # 提取年龄
        if "婴儿" in request or "baby" in request_lower:
            context["age_group"] = "0-3"
        elif "小学" in request:
            context["age_group"] = "6-12"
        
        return context


if __name__ == "__main__":
    workflow = PromptWorkflow()
    
    # 示例请求分析
    request = "生成一个儿童英语学习场景，包含 apple, banana, cat"
    context = workflow.analyze_request(request)
    
    print("请求:", request)
    print("分析结果:", context)
    
    # 生成提示词
    result = workflow.generate(
        query="儿童 学习 识字",
        context={
            "topic": "动物园",
            "words": ["狮子", "老虎", "熊猫"],
            "scene": "动物园"
        }
    )
    
    print("\n" + "=" * 50)
    if result.success:
        print(f"✅ 找到案例: {result.case_title}")
        print(f"\n适配提示词:\n{result.adapted_prompt[:300]}...")
    else:
        print(f"❌ {result.warnings}")
