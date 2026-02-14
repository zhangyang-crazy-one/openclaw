
## 2026-02-14
- **Graphiti 知识图谱工作**
  - Neo4j GDS 插件版本不兼容（2.5.0 ≠ 5.26.0）
  - 用户修改版 Graphiti 源码可用（/home/liujerry/graphiti/）
  - DeepSeek LLM + Ollama Embedder 测试通过
  - 技能文档更新到 v2.0
  - 详情: [memory/2026-02-14.md](/home/liujerry/moltbot/memory/2026-02-14.md)

## 2026-02-13

- **股票分析系统重大升级**
  - A股数据: 4,247/5,501 (77.2%)
  - 创业板数据: 969/977 (99.2%) ✅
  - 100只股票预测模型测试完成
  - 凯利仓位优化策略最佳（夏普比率=9.330）
  - 详情: [memory/2026-02-13.md](/home/liujerry/moltbot/memory/2026-02-13.md)

## 2026-02-13
- **上游同步完成**: 自动合并 upstream/main 到 fork
  - 143 个文件更改，+4186/-2064 行
  - 新增：飞书媒体测试、ZAI 端点检测脚本、heartbeat-wake 测试等
  - 删除：soul-evil hook 相关文件、一些测试文件重构
  - 新增脚本：label-open-issues.ts、vitest-slowest.mjs
- **上游同步完成**: 自动合并 upstream/main 到 fork
  - 71 个文件更改，+2173/-150 行
  - 新增音频预检、HTTP认证测试、Telegram检测测试等功能
  - Discord 消息处理预检增强，命令队列重构
- **上游同步完成**: 自动合并 upstream/main 到 fork
  - 新分支: codex/subagent-improvements, feat/system-prompt-subagents-guidance
  - 49 个文件更改，+1679/-893 行
  - 包含飞书扩展测试、cron 服务回归测试、WhatsApp markdown 支持等更新

## 2026-02-11
- **系统启动与任务补做**
  - 启动 Neo4j 数据库（从 Created 状态）
  - 修复 Graphiti 知识图谱服务（改用 OpenAI embedder 替代 Ollama）
  - 补做今日股票分析并发送给两个QQ用户
  - 修复邮箱统计 cron 配置（添加 delivery target）
  - 执行知识图谱同步（Moltbook 社区数据分析）
  - 生成10个中英双语日常场景学习卡片并发送

## 2026-02-09
- **上游同步完成**: moltbot/moltbot 上游更新合并
  - 合并 15 个上游提交
  - 新增技能：macro-sentiment, quant-finance, searxng-search, stock-analyzer, stagehand, tavily-search, graphiti-memory, auto-office
  - 新增 Soul-inject Hook
  - 推送到 fork: zhangyang-crazy-one/openclaw

## 2026-02-07
- **Stagehand V3 完成**: 浏览器自动化技能 + Cookie/Session 持久化
- 详情: [memory/2026-02-07.md](/home/liujerry/moltbot/memory/2026-02-07.md)
✅ 已记录
