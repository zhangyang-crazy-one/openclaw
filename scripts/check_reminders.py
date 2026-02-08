#!/usr/bin/env python3
"""
日程提醒检查脚本
检查待发送的提醒并输出 JSON 格式结果
"""

import json
import os
from datetime import datetime

# 提醒数据文件路径
REMINDERS_FILE = os.path.expanduser("~/.openclaw/reminders.json")

def load_reminders():
    """加载提醒数据"""
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('reminders', [])
    except Exception:
        return []

def check_pending_reminders():
    """检查待发送的提醒"""
    reminders = load_reminders()
    now = datetime.now()
    
    pending = []
    for reminder in reminders:
        # 检查提醒是否已发送
        if reminder.get('sent', False):
            continue
        pending.append(reminder)
    
    return pending

def main():
    """主函数"""
    pending = check_pending_reminders()
    pending_count = len(pending)
    
    if pending_count == 0:
        result = {
            "status": "ok",
            "pending_count": 0,
            "message": "暂无待发送的提醒"
        }
    else:
        # 构建消息
        messages = []
        for i, reminder in enumerate(pending, 1):
            title = reminder.get('title', '提醒')
            time = reminder.get('time', '')
            if time:
                messages.append(f"{i}. {title} ({time})")
            else:
                messages.append(f"{i}. {title}")
        
        message_text = f"你有 {pending_count} 个待发送的提醒：\n" + "\n".join(messages)
        result = {
            "status": "ok",
            "pending_count": pending_count,
            "message": message_text
        }
    
    # 输出 JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

if __name__ == "__main__":
    main()
