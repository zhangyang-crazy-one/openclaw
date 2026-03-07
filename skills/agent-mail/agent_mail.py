#!/usr/bin/env python3
"""
AgentMail - AI邮件助手
支持两种方式：SMTP/IMAP (工作正常) 和 官方SDK (测试中)
"""
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# AgentMail SMTP/IMAP 配置
SMTP_CONFIG = {
    'email': 'deepseeker@agentmail.to',
    'smtp_host': 'smtp.agentmail.to',
    'smtp_port': 465,
    'imap_host': 'imap.agentmail.to',
    'imap_port': 993,
    'password': 'am_us_952cede447d6e92843f52d255478747afeaed1b55cf3023ea52321b586648fd4'
}


class AgentMail:
    """AgentMail 邮件客户端"""
    
    def __init__(self, use_smtp=True):
        self.use_smtp = use_smtp
        self.smtp_config = SMTP_CONFIG
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> dict:
        """发送邮件"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['email']
            msg['To'] = to
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP_SSL(
                self.smtp_config['smtp_host'],
                self.smtp_config['smtp_port']
            )
            server.login(self.smtp_config['email'], self.smtp_config['password'])
            server.sendmail(self.smtp_config['email'], to, msg.as_string())
            server.quit()
            
            return {'success': True, 'message': f'Email sent to {to}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_emails(self, folder='INBOX', limit=10) -> list:
        """获取邮件列表"""
        try:
            mail = imaplib.IMAP4_SSL(
                self.smtp_config['imap_host'],
                self.smtp_config['imap_port']
            )
            mail.login(self.smtp_config['email'], self.smtp_config['password'])
            mail.select(folder)
            
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()[-limit:]
            
            emails = []
            for eid in email_ids:
                status, msg_data = mail.fetch(eid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                emails.append({
                    'id': eid.decode() if isinstance(eid, bytes) else eid,
                    'from': msg.get('From'),
                    'subject': msg.get('Subject'),
                    'date': msg.get('Date')
                })
            
            mail.logout()
            return emails
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_latest_email(self) -> dict:
        """获取最新邮件"""
        emails = self.get_emails(limit=1)
        return emails[0] if emails else None


# ============== 官方SDK (测试中) ==============
def get_sdk_client():
    """获取官方SDK客户端"""
    try:
        import agentmail
        return agentmail.AgentMail(
            api_key='am_us_952cede447d6e92843f52d255478747afeaed1b55cf3023ea52321b586648fd4'
        )
    except Exception as e:
        print(f"SDK Error: {e}")
        return None


def send_via_sdk(to: str, subject: str, body: str) -> dict:
    """通过官方SDK发送 (测试中)"""
    try:
        client = get_sdk_client()
        if not client:
            return {'success': False, 'error': 'SDK not available'}
        
        # 尝试通过draft发送
        draft = client.drafts.create(draft={
            'to': to,
            'from': 'deepseeker@agentmail.to',
            'subject': subject,
            'text': body
        })
        
        if draft.draft:
            result = client.drafts.send(draft_id=draft.draft.draft_id)
            return {'success': True, 'result': result}
        
        return {'success': False, 'error': 'Failed to create draft'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============== 便捷函数 ==============
def send(to: str, subject: str, body: str) -> dict:
    """发送邮件 (默认使用SMTP)"""
    mail = AgentMail()
    return mail.send_email(to, subject, body)


def receive(limit: int = 10) -> list:
    """接收邮件"""
    mail = AgentMail()
    return mail.get_emails(limit=limit)


if __name__ == '__main__':
    mail = AgentMail()
    
    print("=== AgentMail Test ===")
    
    # 获取邮件
    print("\n1. Recent Emails:")
    emails = mail.get_emails(limit=3)
    for e in emails:
        print(f"   - {e.get('subject', 'No subject')}")
    
    # 发送测试
    print("\n2. Send Test (SMTP):")
    result = mail.send_email("test@example.com", "Test SMTP", "Hello via SMTP!")
    print(f"   Result: {result}")
