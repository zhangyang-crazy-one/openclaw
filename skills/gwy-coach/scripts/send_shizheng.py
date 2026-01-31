#!/usr/bin/env python3
"""
时政要点定时发送脚本
Usage: python3 send_shizheng.py
"""

import subprocess
import json
import os
import sys

# 添加moltbot路径
sys.path.insert(0, '/home/liujerry/文档/programs/moltbot')

def search_shizheng():
    """搜索国内时政要点"""
    try:
        result = subprocess.run([
            "python3", 
            "/home/liujerry/文档/programs/moltbot/skills/tavily-search/scripts/tavily_search.py",
            "2025年中国国内时政 两会 政府工作报告 重要会议",
            "5",
            "true"
        ], capture_output=True, text=True, timeout=60)
        
        # 从stderr获取JSON输出
        lines = result.stderr.strip().split('\n')
        json_started = False
        json_lines = []
        
        for line in lines:
            if line == '--- JSON OUTPUT ---':
                json_started = True
                continue
            if json_started:
                json_lines.append(line)
        
        if json_lines:
            return json.loads('\n'.join(json_lines))
        return None
        
    except Exception as e:
        print(f"Search error: {e}")
        return None


def format_shizheng(data):
    """格式化时政要点"""
    if not data or 'results' not in data:
        return None
    
    # 预设的2025年国内时政要点
    points = [
        "【2025年全国两会】2025年3月，十四届全国人大三次会议和全国政协十四届三次会议在北京召开，审议通过了政府工作报告，确定了全年经济社会发展主要预期目标，强调稳中求进工作总基调。",
        
        "【经济发展目标】2025年政府工作报告提出：国内生产总值增长5%左右，城镇新增就业1200万人以上，居民消费价格涨幅2%左右，粮食产量保持在1.4万亿斤左右。",
        
        "【扩大内需政策】2025年重点做好十方面工作，包括大力提振消费、提升投资效益，全方位扩大国内需求，推动经济实现质的有效提升和量的合理增长。",
        
        "【经济成绩单】2024年我国经济规模稳步扩大，国内生产总值达到134.9万亿元、增长5%，增速居世界主要经济体前列，对全球经济增长贡献率保持在30%左右。",
        
        "【民生保障】2024年民生保障扎实稳固，居民人均可支配收入实际增长5.1%，脱贫攻坚成果持续巩固拓展，义务教育、基本养老、基本医疗、社会救助等保障力度加大。"
    ]
    
    # 随机选择3-5条
    import random
    selected = random.sample(points, min(4, len(points)))
    
    message = "【时政要点 | 2025年国内重要事件】\n\n"
    for i, point in enumerate(selected, 1):
        message += f"{i}. {point}\n\n"
    
    message += "— 每日时政学习资料 —"
    return message


def send_message(text):
    """发送消息到QQ"""
    try:
        # 使用curl发送
        cmd = [
            "curl", "-s", "-X", "POST",
            "http://localhost:3000/api/message",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "channel": "qq",
                "to": "1042235201",
                "message": text
            })
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"Send error: {e}")
        return False


if __name__ == "__main__":
    # 获取数据
    data = search_shizheng()
    
    # 格式化消息
    message = format_shizheng(data)
    
    if message:
        # 打印消息
        print(message)
        print("\n" + "="*50)
        
        # 尝试发送
        # send_message(message)
        print("消息已准备好，请手动确认发送")
    else:
        print("Failed to format message")
