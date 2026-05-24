#!/bin/bash
# AgentMail 检查包装脚本 - 确保环境变量可靠传递
# 用法: bash run_agentmail_check.sh <inbox> [limit]

INBOX="${1:-deepseeker@agentmail.to}"
LIMIT="${2:-20}"
export AGENTMAIL_API_KEY="am_us_952cede447d6e92843f52d255478747afeaed1b55cf3023ea52321b586648fd4"
export HTTP_PROXY="http://127.0.0.1:7897"
export HTTPS_PROXY="http://127.0.0.1:7897"

cd ~/.openclaw/skills/agentmail
~/moltbot/openclaw_py/bin/python3 scripts/check_inbox.py --inbox "$INBOX" --limit "$LIMIT"
