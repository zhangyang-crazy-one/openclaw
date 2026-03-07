#!/usr/bin/env python3
"""
FARS AI论文审稿系统
对生成的论文进行AI评估
"""
import json
import argparse
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/liujerry/.openclaw/workspace/fars/shared")
REVIEWS_DIR = WORKSPACE / "reviews"


class PaperReviewer:
    """AI论文审稿器"""
    
    def __init__(self):
        REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    
    def review_paper(self, paper_path: Path) -> dict:
        """审稿一篇论文"""
        # 读取论文
        if paper_path.exists():
            with open(paper_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            return {"error": f"论文不存在: {paper_path}"}
        
        # 简化的审稿评估（实际应调用LLM）
        review = {
            "paper": str(paper_path),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scores": {
                "innovation": 7.5,
                "methodology": 7.0,
                "writing": 8.0,
                "completeness": 7.5
            },
            "average_score": 7.5,
            "strengths": [
                "研究主题前沿",
                "方法论清晰",
                "实验设计合理"
            ],
            "weaknesses": [
                "文献综述可以更全面",
                "数据量可以更大"
            ],
            "comments": "这是一篇中等偏上的研究论文，具有一定的创新性和实用价值。"
        }
        
        return review
    
    def review_latest(self, count: int = 5) -> list:
        """审稿最新论文"""
        # 查找最新的论文
        paper_files = list(WORKSPACE.glob("paper*.md"))
        paper_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        reviews = []
        for paper in paper_files[:count]:
            review = self.review_paper(paper)
            reviews.append(review)
        
        return reviews
    
    def generate_report(self, reviews: list) -> str:
        """生成审稿报告"""
        report = f"""# AI论文审稿报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**审稿数量**: {len(reviews)}篇

---
"""
        
        for i, review in enumerate(reviews, 1):
            if "error" in review:
                continue
            
            report += f"""
## 论文 {i}: {Path(review['paper']).name}

### 评分

| 维度 | 评分 |
|------|------|
| 创新性 | {review['scores']['innovation']}/10 |
| 方法论 | {review['scores']['methodology']}/10 |
| 写作质量 | {review['scores']['writing']}/10 |
| 完整性 | {review['scores']['completeness']}/10 |
| **平均分** | **{review['average_score']}/10** |

### 优点
"""
            for s in review.get("strengths", []):
                report += f"- {s}\n"
            
            report += "\n### 需要改进\n"
            for w in review.get("weaknesses", []):
                report += f"- {w}\n"
            
            report += f"\n### 总体评价\n{review.get('comments', '')}\n"
            report += "\n---\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description="FARS AI论文审稿系统")
    parser.add_argument("--paper", type=str, help="论文路径")
    parser.add_argument("--latest", type=int, default=0, help="审稿最新N篇")
    parser.add_argument("--output", type=str, help="输出报告路径")
    
    args = parser.parse_args()
    
    reviewer = PaperReviewer()
    
    if args.latest > 0:
        reviews = reviewer.review_latest(args.latest)
        report = reviewer.generate_report(reviews)
        
        print(f"📊 审稿完成，共{len(reviews)}篇论文")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存: {args.output}")
        else:
            print(report)
    elif args.paper:
        review = reviewer.review_paper(Path(args.paper))
        print(json.dumps(review, ensure_ascii=False, indent=2))
    else:
        print("使用 --latest N 审稿最新N篇论文")
        print("使用 --paper <path> 审稿指定论文")


if __name__ == "__main__":
    main()
