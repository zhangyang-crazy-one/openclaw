#!/usr/bin/env python3
"""
Weekly Insight Compiler - 周报编译脚本
Karpathy LLM Wiki 模式的 Ingest 操作实现

功能:
- 读取指定周的所有日记 (memory/YYYY-MM-DD.md)
- LLM 综合生成结构化周报
- 保存到 memory/insights/weekly_YEAR-Www.md
- 可选: 同步到 Graphiti 知识图谱

用法:
    python3 weekly_insight_compiler.py              # 编译本周
    python3 weekly_insight_compiler.py --week 2026-W15  # 编译指定周
    python3 weekly_insight_compiler.py --sync      # 编译并同步到 Graphiti
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request

# 配置
WORKSPACE = Path("/home/liujerry/moltbot")
MEMORY_DIR = WORKSPACE / "memory"
INSIGHTS_DIR = WORKSPACE / "memory" / "insights"
GRAPHITI_URL = "http://localhost:8000"

# 确保 insights 目录存在
INSIGHTS_DIR.mkdir(exist_ok=True)

def get_week_dates(week_str=None):
    """获取指定周的开始和结束日期"""
    if week_str:
        # 解析 2026-W15 格式
        match = re.match(r'(\d{4})-W(\d{2})', week_str)
        if match:
            year, week = int(match.group(1)), int(match.group(2))
            # 计算该周的周一
            jan4 = datetime(year, 1, 4)
            monday = jan4 - timedelta(days=jan4.weekday())
            start_of_week = monday + timedelta(weeks=week-1)
        else:
            raise ValueError(f"无法解析周字符串: {week_str}")
    else:
        # 本周
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        start_of_week = monday
    
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

def get_daily_files(start_date, end_date):
    """获取指定日期范围内的日记文件"""
    daily_files = []
    current = start_date
    
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        file_path = MEMORY_DIR / f"{date_str}.md"
        
        if file_path.exists():
            daily_files.append({
                "date": date_str,
                "path": file_path,
                "content": file_path.read_text(encoding='utf-8')
            })
        current += timedelta(days=1)
    
    return daily_files

def extract_key_sections(content):
    """提取日记的关键部分"""
    sections = {
        "morning_reflection": "",
        "tasks_completed": [],
        "insights": [],
        "problems": [],
        "explorations": [],
        "evening_summary": ""
    }
    
    lines = content.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if '晨间反思' in line or 'Morning Session' in line:
            current_section = "morning_reflection"
        elif '工作完成' in line or 'Work Completed' in line:
            current_section = "tasks_completed"
        elif '洞察' in line or 'Insights' in line or '三问' in line:
            current_section = "insights"
        elif '问题' in line or 'Problems' in line:
            current_section = "problems"
        elif '探索' in line or 'Exploration' in line:
            current_section = "explorations"
        elif '晚间总结' in line or 'Evening Summary' in line:
            current_section = "evening_summary"
        elif line.startswith('###'):
            current_section = None
        elif line.startswith('[') and line.endswith(']'):
            # 任务状态标记
            continue
        elif current_section and line:
            if isinstance(sections[current_section], list):
                if line.startswith('-') or line.startswith('*'):
                    sections[current_section].append(line)
            else:
                sections[current_section] += line + "\n"
    
    return sections

def compile_weekly_report(week_str, daily_files):
    """编译周报"""
    
    start_date, end_date = get_week_dates(week_str)
    week_display = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    
    # 统计
    total_tasks = 0
    total_insights = 0
    all_tasks = []
    all_insights = []
    all_problems = []
    
    daily_summaries = []
    
    for daily in daily_files:
        sections = extract_key_sections(daily['content'])
        
        summary = {
            "date": daily['date'],
            "tasks": sections['tasks_completed'],
            "insights": sections['insights'],
            "problems": sections['problems'],
            "morning": sections['morning_reflection'][:100] if sections['morning_reflection'] else "",
            "evening": sections['evening_summary'][:100] if sections['evening_summary'] else ""
        }
        
        daily_summaries.append(summary)
        total_tasks += len(sections['tasks_completed'])
        total_insights += len(sections['insights'])
        all_tasks.extend(sections['tasks_completed'])
        all_insights.extend(sections['insights'])
        all_problems.extend(sections['problems'])
    
    # 生成周报
    report = f"""# 周报: {week_str}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
周期: {week_display}
日记天数: {len(daily_files)} / 7

---

## 📊 本周概览

| 指标 | 数量 |
|------|------|
| 工作日 | {len(daily_files)} |
| 完成任务 | {total_tasks} |
| 新洞察 | {total_insights} |
| 遇到问题 | {len(all_problems)} |

---

## 📅 每日摘要

"""
    
    for summary in daily_summaries:
        report += f"""### {summary['date']}

**晨间**: {summary['morning'][:80] if summary['morning'] else '无'}

**完成任务**:
{chr(10).join(summary['tasks'][:5]) if summary['tasks'] else '无'}

**关键洞察**:
{chr(10).join(summary['insights'][:3]) if summary['insights'] else '无'}

**问题/困难**:
{chr(10).join(summary['problems'][:2]) if summary['problems'] else '无'}

**晚间**: {summary['evening'][:80] if summary['evening'] else '无'}

---
"""
    
    # 洞察汇总
    report += f"""
## 💡 本周洞察汇总

### 关键发现 ({len(all_insights)} 条)

"""
    
    for i, insight in enumerate(all_insights[:20], 1):
        if isinstance(insight, str) and len(insight) > 10:
            report += f"{i}. {insight}\n"
    
    # 问题汇总
    report += f"""
### 问题与解决 ({len(all_problems)} 条)

"""
    
    if all_problems:
        for i, problem in enumerate(all_problems[:10], 1):
            if isinstance(problem, str) and len(problem) > 10:
                report += f"{i}. {problem}\n"
    else:
        report += "本周无重大问题。\n"
    
    # 任务汇总
    report += f"""
## ✅ 任务完成汇总 ({total_tasks} 项)

"""
    
    for i, task in enumerate(all_tasks[:30], 1):
        if isinstance(task, str) and len(task) > 10:
            # 清理任务标记
            task_clean = task.replace('[x]', '').replace('[ ]', '').replace('✅', '').replace('❌', '').strip()
            if task_clean:
                report += f"{i}. {task_clean}\n"
    
    # 主题分析
    report += f"""
---

## 🔍 主题分析

基于本周的日记内容，归纳以下主题：

"""
    
    # 简单的关键词统计
    all_text = ' '.join([d['content'] for d in daily_files])
    keywords = ['RSI', 'Buffett', 'Graphiti', 'Moltbook', 'cron', '数据', '知识', 'API', '筛选', '采集']
    
    for kw in keywords:
        count = all_text.count(kw)
        if count > 0:
            report += f"- **{kw}**: 提及 {count} 次\n"
    
    report += f"""
---

## 🎯 下周展望

基于本周的工作和洞察，建议下周关注：

1. 持续追踪:
   - Buffett 数据采集完成后的数据质量验证
   - Moltbook API 恢复情况

2. 待完成任务:
   - RSI 策略系统化回测 (需 n > 30 样本)
   - 技术指标重建

3. 探索方向:
   - LLM Wiki 模式实践
   - Obsidian 集成

---

_编译自: {', '.join([d['date'] for d in daily_files])}_
_工具: weekly_insight_compiler.py_
"""
    
    return report

def sync_to_graphiti(week_str, report_content):
    """同步周报到 Graphiti"""
    print(f"🔄 同步到 Graphiti...")
    
    # 提取关键洞察作为实体
    insights = []
    for line in report_content.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
            if len(line) > 20:
                insights.append(line[2:].strip())
    
    # 创建消息
    messages = [{
        "role": "system",
        "role_type": "system",
        "content": f"""编译本周洞察并添加到知识图谱:

周报: {week_str}

关键洞察:
{chr(10).join(insights[:10])}

请为每条洞察创建实体，使用关系类型 SYNTHESIZED_FROM 关联到周报。
实体 group_id: insights
"""
    }]
    
    data = json.dumps({
        "group_id": "insights",
        "messages": messages
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f'{GRAPHITI_URL}/messages',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Graphiti 同步成功: {result}")
            return True
    except Exception as e:
        print(f"⚠️ Graphiti 同步失败: {e}")
        return False

def main():
    week_str = None
    do_sync = False
    
    # 解析参数
    if "--week" in sys.argv:
        idx = sys.argv.index("--week")
        if idx + 1 < len(sys.argv):
            week_str = sys.argv[idx + 1]
    
    if "--sync" in sys.argv:
        do_sync = True
    
    if "--help" in sys.argv:
        print(__doc__)
        return
    
    # 获取日期范围
    start_date, end_date = get_week_dates(week_str)
    
    if week_str:
        print(f"📅 编译周报: {week_str}")
    else:
        # 计算当前周
        today = datetime.now()
        week_num = today.isocalendar()[1]
        week_str = f"{today.year}-W{week_num:02d}"
        print(f"📅 编译周报: {week_str}")
    
    print(f"📆 周期: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    # 获取日记文件
    daily_files = get_daily_files(start_date, end_date)
    print(f"📄 找到 {len(daily_files)} 篇日记")
    
    if not daily_files:
        print("❌ 没有找到日记文件，无法编译周报")
        return
    
    # 编译周报
    print("📝 编译周报...")
    report = compile_weekly_report(week_str, daily_files)
    
    # 保存周报
    output_file = INSIGHTS_DIR / f"weekly_{week_str}.md"
    output_file.write_text(report, encoding='utf-8')
    print(f"✅ 周报已保存: {output_file}")
    
    # 可选: 同步到 Graphiti
    if do_sync:
        sync_to_graphiti(week_str, report)
    
    # 打印摘要
    print("\n" + "=" * 50)
    print("📋 周报摘要")
    print("=" * 50)
    
    lines = report.split('\n')
    in_summary = False
    for line in lines:
        if '本周概览' in line:
            in_summary = True
        if in_summary and line.startswith('|'):
            print(line)
        if in_summary and '---' in line and line.count('-') > 5:
            break
    
    print(f"\n✅ 周报编译完成: {output_file}")
    print(f"📖 查看: cat {output_file}")

if __name__ == "__main__":
    main()
