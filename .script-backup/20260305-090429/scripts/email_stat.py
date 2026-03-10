#!/usr/bin/env python3
"""
邮箱分析脚本
统计、分类、摘要、提醒应该阅读的邮件
"""
import json
import os
import email
from datetime import datetime
from collections import Counter

# QQ邮箱配置
EMAIL_ADDRESS = "740884666@qq.com"
IMAP_SERVER = "imap.qq.com"

# 发件人关键词分类
CATEGORIES = {
    "工作": ["hr@", "hr@", "hr@", "boss@", "manager@", "猎头", "招聘", "HR", "HRBP", "面试", "offer"],
    "技术": ["github", "gitlab", "stackoverflow", "juejin", "掘金", "v2ex", "segmentfault", "CSDN", "开源", "代码", "技术"],
    "金融": ["雪球", "东方财富", "同花顺", "券商", "基金", "股票", "理财", "银行", "财报", "年报"],
    "购物": ["京东", "淘宝", "天猫", "拼多多", "亚马逊", "当当", "唯品会", "优惠券", "促销", "双11"],
    "社交": ["微信", "QQ", "微博", "知乎", "豆瓣", "小红书", "B站", "抖音", "脉脉", "领英"],
    "账单": ["账单", "发票", "缴费", "还款", "账单日", "账单明细", "银行流水"],
}

# 重要发件人模式
IMPORTANT_PATTERNS = [
    "hr@", "boss@", "manager@", "面试", "offer",
    "雪球", "投资", "理财", "账单", "发票",
    "github", "issue", "pull request",
]


def parse_email_date(date_str):
    """解析邮件日期"""
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except:
        return "未知时间"


def categorize_email(subject, from_name):
    """分类邮件"""
    text = (subject + " " + from_name).lower()
    
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                return category
    
    return "其他"


def is_important(subject, from_name):
    """判断是否重要"""
    text = (subject + " " + from_name).lower()
    
    for pattern in IMPORTANT_PATTERNS:
        if pattern.lower() in text:
            return True
    
    # 检查是否包含"紧急"、"重要"、"提醒"等词
    urgent_words = ["紧急", "重要", "提醒", "提醒", "必须", "尽快", " deadline"]
    for word in urgent_words:
        if word.lower() in text:
            return True
    
    return False


def extract_from_name(from_str):
    """提取发件人名称"""
    try:
        name, addr = email.utils.parseaddr(from_str)
        if name:
            return name
        return addr.split("@")[0]
    except:
        return from_str


def analyze_email(email_msg):
    """分析单封邮件"""
    subject = email_msg.get("Subject", "(无主题)")
    from_str = email_msg.get("From", "(未知)")
    from_name = extract_from_name(from_str)
    date = parse_email_date(email_msg.get("Date", ""))
    
    # 分类
    category = categorize_email(subject, from_name)
    
    # 是否重要
    is_important_mail = is_important(subject, from_name)
    
    # 提取正文摘要
    body = ""
    try:
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    break
        else:
            body = email_msg.get_payload(decode=True)
        
        if body:
            body = body.decode("utf-8", errors="ignore")[:200]
    except:
        body = ""
    
    return {
        "subject": subject,
        "from": from_name,
        "date": date,
        "category": category,
        "important": is_important_mail,
        "preview": body.strip() if body else "(无正文)",
    }


def get_emails(limit=50):
    """获取邮件列表"""
    password = os.environ.get("QQ_IMAP_PASSWORD")
    if not password:
        return None, "QQ_IMAP_PASSWORD not set"
    
    try:
        import imaplib
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, password)
        mail.select("INBOX")
        
        # 获取最新邮件
        typ, msgs = mail.search(None, "ALL")
        email_ids = msgs[0].split()
        
        # 只取最近的limit封
        recent_ids = email_ids[-limit:]
        
        emails = []
        for eid in reversed(recent_ids):
            try:
                typ, msg_data = mail.fetch(eid, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        email_msg = email.message_from_bytes(response_part[1])
                        emails.append(analyze_email(email_msg))
            except:
                continue
        
        mail.logout()
        return emails, None
        
    except Exception as e:
        return None, str(e)


def email_analysis():
    """邮箱分析主函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 70)
    print("📧 QQ邮箱深度分析")
    print(f"📬 {EMAIL_ADDRESS}")
    print(f"⏰ {timestamp}")
    print("=" * 70)
    
    password = os.environ.get("QQ_IMAP_PASSWORD")
    if not password:
        print("\n❌ 错误: 未设置 QQ_IMAP_PASSWORD")
        return
    
    print("\n🔗 正在获取邮件...")
    emails, error = get_emails(limit=50)
    
    if error:
        print(f"❌ 错误: {error}")
        return
    
    if not emails:
        print("📭 邮件箱为空")
        return
    
    # 统计分类
    categories = Counter([e["category"] for e in emails])
    important_emails = [e for e in emails if e["important"]]
    
    print(f"\n📊 邮件统计 (最近 {len(emails)} 封)")
    print("-" * 40)
    
    for cat, count in categories.most_common():
        bar = "█" * min(count, 30)
        print(f"  {cat:8s}: {count:3d} {bar}")
    
    # 重要邮件提醒
    if important_emails:
        print(f"\n" + "=" * 70)
        print("🔔 需要重点关注的邮件")
        print("=" * 70)
        
        for i, e in enumerate(important_emails[:10], 1):
            print(f"\n{i}. 【{e['category']}】{e['subject'][:50]}...")
            print(f"   发件人: {e['from']} | 时间: {e['date']}")
            print(f"   摘要: {e['preview'][:80]}...")
    
    # 最近邮件列表
    print(f"\n" + "=" * 70)
    print("📬 最近邮件")
    print("=" * 70)
    
    for i, e in enumerate(emails[:15], 1):
        icon = "🔴" if e["important"] else "⚪"
        marker = "❗" if e["important"] else "  "
        print(f"{marker} {icon} [{e['category']:4s}] {e['subject'][:40]}...")
    
    # 建议
    print(f"\n" + "=" * 70)
    print("💡 建议")
    print("=" * 70)
    
    if important_emails:
        print(f"  • 您有 {len(important_emails)} 封重要邮件需要处理")
    
    work_count = categories.get("工作", 0)
    if work_count > 0:
        print(f"  • 工作邮件: {work_count} 封")
    
    finance_count = categories.get("金融", 0)
    if finance_count > 0:
        print(f"  • 金融相关: {finance_count} 封")
    
    # JSON 输出
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "email": EMAIL_ADDRESS,
        "total_analyzed": len(emails),
        "timestamp": timestamp,
        "categories": dict(categories),
        "important_count": len(important_emails),
        "important_emails": important_emails[:5],
        "recent_emails": emails[:10],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")


if __name__ == "__main__":
    email_analysis()
