# Agent Mail - AI邮件助手

通过 AgentMail 为 AI 智能体配置专属邮箱，实现安全收发邮件功能。

## 配置

| 配置项      | 值                                                                     |
| ----------- | ---------------------------------------------------------------------- |
| **邮箱**    | deepseeker@agentmail.to                                                |
| **SMTP**    | smtp.agentmail.to:465                                                  |
| **IMAP**    | imap.agentmail.to:993                                                  |
| **API Key** | am_us_952cede447d6e92843f52d255478747afeaed1b55cf3023ea52321b586648fd4 |

## 安装依赖

```bash
pip install requests imaplib-smtplib
```

## 使用方法

### 发送邮件

```python
from agent_mail import send

result = send(
    to="recipient@example.com",
    subject="邮件主题",
    body="邮件内容"
)
print(result)
# {'success': True, 'message': 'Email sent to ...'}
```

### 接收邮件

```python
from agent_mail import receive

emails = receive(limit=10)
for email in emails:
    print(email['subject'], email['from'])
```

### 完整功能

```python
from agent_mail import AgentMail

mail = AgentMail()

# 发送邮件
mail.send_email(
    to="test@example.com",
    subject="Test",
    body="Hello"
)

# 获取邮件
emails = mail.get_emails(limit=10)

# 获取最新邮件
latest = mail.get_latest_email()
```

## 状态

✅ **SMTP发送**: 正常工作
✅ **IMAP接收**: 正常
⚠️ **官方SDK**: 测试中 (API端点返回404)

## 触发词

- "发送邮件"
- "查看邮箱"
- "邮件测试"
