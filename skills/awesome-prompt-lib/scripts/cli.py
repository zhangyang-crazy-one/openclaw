#!/usr/bin/env python3
"""
CLI Tool for Awesome Prompt Library

命令行工具
"""
import argparse
import json
import sys

from .prompt_search import PromptSearcher
from .prompt_adapter import PromptAdapter
from .prompt_workflow import PromptWorkflow


def main():
    parser = argparse.ArgumentParser(
        description="Awesome Prompt Library CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索提示词")
    search_parser.add_argument("query", nargs="+", help="搜索关键词")
    search_parser.add_argument("-l", "--limit", type=int, default=5, help="结果数量限制")
    
    # adapt 命令
    adapt_parser = subparsers.add_parser("adapt", help="适配提示词")
    adapt_parser.add_argument("prompt", help="原始提示词")
    adapt_parser.add_argument("-c", "--context", required=True, help="上下文 JSON")
    adapt_parser.add_argument("-p", "--preserve", action="store_true", help="保留原始结构")
    
    # generate 命令
    generate_parser = subparsers.add_parser("generate", help="生成提示词")
    generate_parser.add_argument("request", nargs="+", help="用户请求")
    generate_parser.add_argument("-w", "--words", nargs="+", help="词汇列表")
    generate_parser.add_argument("-s", "--scene", help="场景描述")
    generate_parser.add_argument("-t", "--topic", help="主题")
    
    # sync 命令
    sync_parser = subparsers.add_parser("sync", help="同步提示词库")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出提示词")
    list_parser.add_argument("-l", "--limit", type=int, default=10, help="数量限制")
    
    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="分析请求")
    analyze_parser.add_argument("request", nargs="+", help="用户请求")
    
    args = parser.parse_args()
    
    if args.command == "search":
        do_search(args)
    elif args.command == "adapt":
        do_adapt(args)
    elif args.command == "generate":
        do_generate(args)
    elif args.command == "sync":
        do_sync(args)
    elif args.command == "list":
        do_list(args)
    elif args.command == "analyze":
        do_analyze(args)
    else:
        parser.print_help()


def do_search(args):
    """执行搜索"""
    searcher = PromptSearcher()
    query = " ".join(args.query)
    
    results = searcher.search(query, limit=args.limit)
    
    print(f"\n🔍 搜索 '{query}' 结果 ({len(results)} 个)")
    print("=" * 60)
    
    for i, case in enumerate(results, 1):
        print(f"\n{i}. {case.title}")
        print(f"   作者: {case.author}")
        print(f"   标签: {', '.join(case.tags) if case.tags else '无'}")
        print(f"   输入类型: {case.input_type}")
        
        # 显示提示词预览
        preview = case.prompt[:150] + "..." if len(case.prompt) > 150 else case.prompt
        print(f"   提示词: {preview}")


def do_adapt(args):
    """执行适配"""
    adapter = PromptAdapter()
    
    try:
        context = json.loads(args.context)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        return
    
    result = adapter.adapt(
        original_prompt=args.prompt,
        context=context,
        preserve_structure=args.preserve
    )
    
    print("\n📝 适配结果")
    print("=" * 60)
    print(result.adapted_prompt)
    
    if result.variables:
        print(f"\n📋 提取的变量: {result.variables}")
    
    if result.warnings:
        print(f"\n⚠️ 警告: {result.warnings}")


def do_generate(args):
    """执行生成"""
    workflow = PromptWorkflow()
    request = " ".join(args.request)
    
    # 分析请求
    context = workflow.analyze_request(request)
    
    # 覆盖参数
    if args.topic:
        context["topic"] = args.topic
    if args.words:
        context["words"] = args.words
    if args.scene:
        context["scene"] = args.scene
    
    print(f"\n📊 分析请求: {request}")
    print(f"📋 上下文: {context}")
    
    # 生成提示词
    result = workflow.generate(
        query=args.topic or request,
        context=context
    )
    
    print("\n" + "=" * 60)
    if result.success:
        print(f"✅ 使用案例: {result.case_title}")
        print(f"\n📝 适配提示词:\n{result.adapted_prompt}")
    else:
        print(f"❌ 生成失败: {result.warnings}")


def do_sync(args):
    """执行同步"""
    searcher = PromptSearcher()
    searcher.sync()
    print(f"✅ 同步完成，共 {len(searcher.cases)} 个案例")


def do_list(args):
    """列出提示词"""
    searcher = PromptSearcher()
    
    print(f"\n📚 提示词库 ({len(searcher.cases)} 个案例)")
    print("=" * 60)
    
    # 显示标签统计
    tags = searcher.get_all_tags()
    print(f"\n标签分类:")
    for tag in tags[:20]:
        count = sum(1 for c in searcher.cases if tag in c.tags)
        print(f"  - {tag}: {count} 个")
    
    # 随机显示案例
    print(f"\n随机案例:")
    random_cases = searcher.get_random(args.limit)
    for case in random_cases:
        print(f"  - {case.title}")


def do_analyze(args):
    """分析请求"""
    workflow = PromptWorkflow()
    request = " ".join(args.request)
    
    context = workflow.analyze_request(request)
    
    print(f"\n📊 分析请求: {request}")
    print("=" * 60)
    print(f"\n提取的上下文:")
    for key, value in context.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
