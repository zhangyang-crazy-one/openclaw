#!/usr/bin/env python3
"""
Tavily Web Search Script
Usage: python3 tavily_search.py <query> [max_results] [include_answer]
"""

import sys
import os
import json
import urllib.request
import urllib.error
from urllib.parse import quote

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")
TAVILY_API_URL = "https://api.tavily.com/search"


def search_tavily(query, max_results=5, include_answer=True, search_depth="basic"):
    """
    Perform a web search using Tavily API.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-20)
        include_answer: Whether to include AI-generated answer
        search_depth: "basic" or "advanced"
    
    Returns:
        dict: Search results with answer and sources
    """
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": min(max_results, 20),
        "include_answer": include_answer,
        "search_depth": search_depth,
        "include_raw_content": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            TAVILY_API_URL,
            data=data,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
            
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error {e.code}: {e.reason}", "details": e.read().decode('utf-8')}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def format_results(result):
    """Format search results for human-readable output."""
    if "error" in result:
        return f"Search failed: {result['error']}"
    
    output = []
    
    # Add AI answer if available
    if result.get("answer"):
        output.append("=" * 60)
        output.append("AI ANSWER")
        output.append("=" * 60)
        output.append(result["answer"])
        output.append("")
    
    # Add sources
    results = result.get("results", [])
    if results:
        output.append("=" * 60)
        output.append(f"SOURCES ({len(results)} results)")
        output.append("=" * 60)
        
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            content = r.get("content", "No content available")
            score = r.get("score", 0)
            
            output.append(f"\n[{i}] {title}")
            output.append(f"    URL: {url}")
            output.append(f"    Relevance: {score:.2f}")
            output.append(f"    {content[:300]}..." if len(content) > 300 else f"    {content}")
    
    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tavily_search.py <query> [max_results] [include_answer]")
        print("Example: python3 tavily_search.py 'Python programming' 5 true")
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    include_answer = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else True
    
    result = search_tavily(query, max_results, include_answer)
    
    # Output as formatted text
    print(format_results(result))
    
    # Also output JSON to stderr for programmatic use
    print("\n--- JSON OUTPUT ---", file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()
