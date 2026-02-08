#!/usr/bin/env bash
# 邮箱每日报告 - 发送到QQ
# 使用nvm切换Node版本，并设置完整PATH

# 设置环境变量
export NVM_DIR="$HOME/.nvm"
export PATH=/usr/local/bin:/home/liujerry/.local/bin:/home/liujerry/.local/share/pnpm:/usr/bin:/bin:/home/liujerry/.nvm/current/bin:/home/liujerry/.npm-global/bin:/home/liujerry/bin:/home/liujerry/.fnm/current/bin:/home/liujerry/.volta/bin:/home/liujerry/.asdf/shims:/home/liujerry/.bun/bin

# 加载 nvm
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 使用 Node 22
nvm use 22

cd /home/liujerry/moltbot

# 设置邮箱密码
export QQ_IMAP_PASSWORD="auoopvlygaoybbci"

# 获取邮件分析并发送到QQ
python3 scripts/email_stat.py 2>&1 | tee /tmp/email_report.txt

# 提取消息内容并发送
MESSAGE=$(cat << 'EOF'
📧 每日邮箱报告

查看详情: ~/.logs/email_stat.log
EOF
)

# 发送简短报告
/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw message send --target 740884666 --message "$MESSAGE"
