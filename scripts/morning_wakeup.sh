#!/bin/bash
# 早晨唤醒脚本：先生成知识图谱周回顾，再发送给用户
cd /home/liujerry/moltbot
./openclaw_py/bin/python scripts/wakeup_memory_loader.py 2>&1
echo "---CONTEXT_END---"
cat /tmp/wakeup_kg_context.txt 2>/dev/null
