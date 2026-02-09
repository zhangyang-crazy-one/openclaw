#!/usr/bin/env python3
"""
邮箱每日报告 - 发送到QQ
"""
import subprocess
import json
import sys
import os
from datetime import datetime

# 设置环境变量
os.environ['QQ_IMAP_PASSWORD'] = 'auoopvlygaoybbci'

# OpenClaw命令路径
OPENCLAW_CMD = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"

# 导入模块
sys.path.insert(0, '/home/liujerry/moltbot/scripts')
from email_stat import get_emails
from collections import Counter

def send_qq_message(target, message):
    """发送QQ消息"""
    cmd = [
        OPENCLAW_CMD, "message", "send",
        "--target", target,
        "--message", message
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("📧 获取邮件分析...")
    emails, error = get_emails(limit=50)
    
    if error:
        msg = f"Error: {error}"
        print(msg)
        return
    
    if not emails:
        msg = "Mailbox is empty"
        print(msg)
        return
    
    # 统计
    categories = Counter([e["category"] for e in emails])
    important = [e for e in emails if e["important"]]
    
    # 构建消息
    lines = [
        f"Daily Mail Report",
        f"Time: {timestamp}",
        "",
        f"Stats (50 emails):",
    ]
    
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
        lines.append(f"  - {cat}: {count}")
    
    if important:
        lines.extend(["", f"Important: {len(important)}"])
        for e in important[:3]:
            subject = e.get("subject", "")[:25]
            lines.append(f"  ! {subject}...")
    
    lines.extend(["", f"Action: {len(important)} need attention"])
    
    message = "\n".join(lines)
    
    # 发送到QQ
    print(f"\nSending to QQ 740884666...")
    success, result = send_qq_message("740884666", message)
    
    if success:
        print("Sent successfully!")
        try:
            data = json.loads(result)
            if data.get("result", {}).get("messageId"):
                print(f"   MessageID: {data['result']['messageId']}")
        except:
            pass
    else:
        print(f"Failed: {result}")
    
    print("-" * 50)
    print(message)
    print("-" * 50)
    
    return message

if __name__ == "__main__":
    main()
