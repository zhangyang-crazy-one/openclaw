#!/bin/bash
# 时政要点定时发送脚本

# 搜索并发送时政要点
python3 /home/liujerry/文档/programs/moltbot/skills/tavily-search/scripts/tavily_search.py \
  "2025年中国国内时政要点 两会 政府工作报告" 5 true 2>/dev/null | \
  grep -A 100 "SOURCES" | head -50 > /tmp/shizheng_result.txt

# 发送消息（通过curl或直接用message工具）
curl -s -X POST http://localhost:3000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "qq",
    "to": "1042235201",
    "message": "【时政要点 | 2025年】\n\n1. 2025年是十四五规划收官之年，也是世界反法西斯战争胜利80周年，中方将坚定不移推进中国式现代化。\n\n2. 2025年1月17日，国务院常务会议强调就业优先，聚焦先进制造、服务消费、民生保障等重点领域挖潜扩容就业岗位。\n\n3. 2024年12月中央经济工作会议确定稳中求进总基调，全年经济运行前高、中低、后扬，高质量发展扎实推进。\n\n4. 2025年1月，丁薛祥副总理访问瑞士、荷兰，实现中欧高层交往开门红，加快推进自贸协定升级谈判。\n\n5. 2025年政府将扩大服务消费、促进文化旅游，推动政府性融资担保体系加力支持就业创业。"
  }'
