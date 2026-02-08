#!/usr/bin/env python3
"""
发送消息到QQ
"""
import json
import sys
from datetime import datetime


def send_qq_message(target, message):
    """发送QQ消息"""
    import subprocess
    
    cmd = [
        "openclaw", "message", "send",
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


def email_report_to_qq():
    """邮箱报告并发送到QQ"""
    # 先获取邮件分析
    os.chdir("/home/liujerry/moltbot")
    
    # 设置环境变量
    os.environ["QQ_IMAP_PASSWORD"] = "auoopvlygaoybbci"
    
    # 导入并运行分析
    sys.path.insert(0, "/home/liujerry/moltbot/scripts")
    from email_stat import get_emails
    from collections import Counter
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("📧 获取邮件分析...")
    emails, error = get_emails(limit=50)
    
    if error:
        msg = f"❌ 邮箱分析失败: {error}"
        print(msg)
        return
    
    if not emails:
        msg = "📭 邮箱为空"
        print(msg)
        send_qq_message("740884666", msg)
        return
    
    # 统计
    categories = Counter([e["category"] for e in emails])
    important = [e for e in emails if e["important"]]
    
    # 格式化消息
    lines = [
        f"📧 邮箱每日报告",
        f"⏰ {timestamp}",
        "",
        f"📊 统计 (50封):",
    ]
    
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
        lines.append(f"  • {cat}: {count}封")
    
    if important:
        lines.extend(["", f"🔔 重点: {len(important)}封"])
        for e in important[:3]:
            subject = e.get("subject", "")[:25]
            lines.append(f"  🔴 {subject}...")
    
    lines.extend(["", f"💡 {len(important)}封需处理"])
    
    message = "\n".join(lines)
    
    print(f"\n📤 发送消息到 QQ 740884666...")
    print("-" * 50)
    print(message)
    print("-" * 50)
    
    # 发送到QQ
    success, result = send_qq_message("740884666", message)
    
    if success:
        print("✅ 消息已发送")
    else:
        print(f"❌ 发送失败: {result}")
    
    return message


if __name__ == "__main__":
    import os
    email_report_to_qq()
