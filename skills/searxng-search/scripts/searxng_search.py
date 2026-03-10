#!/usr/bin/env python3
"""
SearXNG Search Script
支持多引擎学术搜索（带重试机制）
"""
import argparse
import json
import urllib.request
import urllib.parse
import sys
import time
from typing import List, Dict, Optional

# SearXNG 服务地址
SEARXNG_BASE_URL = "http://localhost:8080"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


def search_with_retry(
    query: str,
    engines: Optional[List[str]] = None,
    max_results: int = 10,
    format_json: bool = True,
    language: str = "zh"
) -> Dict:
    """
    执行 SearXNG 搜索（带重试机制）
    
    Args:
        query: 搜索关键词
        engines: 指定搜索引擎列表
        max_results: 最大结果数
        format_json: 是否返回JSON格式
        language: 结果语言
    
    Returns:
        搜索结果字典
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # 构建URL
            params = {
                'q': query,
                'format': 'json' if format_json else 'html',
                'max_results': max_results,
                'language': language
            }
            
            if engines:
                params['engines'] = ','.join(engines)
            
            url = f"{SEARXNG_BASE_URL}/search?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠️ 搜索失败 (尝试 {attempt+1}/{MAX_RETRIES}): {e}", file=sys.stderr)
                time.sleep(RETRY_DELAY)
            continue
    
    return {'error': last_error, 'results': []}


# 兼容旧接口
def search(query, engines=None, max_results=10, format_json=True, language="zh"):
    """兼容旧接口，实际调用带重试的版本"""
    return search_with_retry(query, engines, max_results, format_json, language)


def print_results(results: Dict, verbose: bool = False):
    """打印搜索结果"""
    if 'error' in results:
        print(f"错误: {results['error']}")
        return
    
    results_list = results.get('results', [])
    print(f"找到 {len(results_list)} 个结果:\n")
    
    for i, r in enumerate(results_list, 1):
        title = r.get('title', '无标题')
        url = r.get('url', '')
        content = r.get('content', '')[:200]
        engine = r.get('engine', '')
        
        print(f"{i}. {title}")
        print(f"   来源: {engine}")
        print(f"   URL: {url}")
        if verbose and content:
            print(f"   摘要: {content}...")
        print()


def main():
    parser = argparse.ArgumentParser(description='SearXNG 搜索工具')
    parser.add_argument('query', nargs='?', help='搜索关键词')
    parser.add_argument('--engines', '-e', help='指定搜索引擎 (逗号分隔)')
    parser.add_argument('--max', '-m', type=int, default=10, help='最大结果数')
    parser.add_argument('--lang', '-l', default='zh', help='语言')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if not args.query:
        parser.print_help()
        return
    
    # 解析引擎
    engines = None
    if args.engines:
        engines = [e.strip() for e in args.engines.split(',')]
    
    # 执行搜索（带重试）
    results = search_with_retry(
        query=args.query,
        engines=engines,
        max_results=args.max,
        language=args.lang
    )
    
    # 输出结果
    print_results(results, verbose=args.verbose)


if __name__ == '__main__':
    main()
