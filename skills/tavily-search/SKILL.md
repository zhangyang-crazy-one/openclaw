---
name: tavily-search
description: Web search using Tavily API - an alternative to Brave Search with AI-generated answers. Use when the user needs to search the web for information, research topics, find current news, or gather sources. Supports both basic and advanced search modes with relevance scoring.
---

# Tavily Search

Web search powered by Tavily API. Provides AI-generated answers alongside traditional search results with relevance scoring.

## Quick Start

### Basic Search

```bash
python3 skills/tavily-search/scripts/tavily_search.py "your search query"
```

### Advanced Search (More Comprehensive)

Use `search_depth=advanced` for more thorough research:

```python
import subprocess
import json

result = subprocess.run([
    "python3", "skills/tavily-search/scripts/tavily_search.py",
    "your query", "10", "true"
], capture_output=True, text=True)
```

## Features

- **AI-Generated Answers**: Tavily can synthesize an answer from search results
- **Relevance Scoring**: Each result includes a relevance score (0-1)
- **Source Attribution**: All answers include source URLs
- **No API Key Required**: Uses pre-configured key

## Output Format

Results include:
- `answer`: AI-synthesized answer (if requested)
- `results`: Array of search results with title, URL, content, and score
- `query`: Original search query
- `response_time`: Search duration in seconds

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_results | 5 | Number of results (1-20) |
| include_answer | true | Include AI-generated answer |
| search_depth | basic | "basic" or "advanced" |

## Comparison with Brave Search

| Feature | Tavily | Brave |
|---------|--------|-------|
| AI Answer | ✅ Built-in | ❌ No |
| Relevance Scores | ✅ Yes | ❌ No |
| Freshness Filter | ❌ Limited | ✅ Yes |
| Region/Language | ❌ Limited | ✅ Yes |
| Cost | Free tier | Free |

**When to use Tavily over Brave:**
- Need AI-synthesized answers
- Want relevance scores for results
- Research tasks requiring source synthesis

**When to use Brave over Tavily:**
- Need region-specific results
- Want freshness filters (past day/week/month)
- Prefer more traditional search results
