#!/usr/bin/env python3
"""
Knowledge Graph Full Ingest - 全部对话纳入知识图谱
Karpathy LLM Wiki 模式的 Raw 层 Ingest 操作

功能:
1. 扫描所有会话文件
2. 提取关键事实、洞察、决策
3. 批量发送到 Graphiti
4. 运行 Lint 检查重复/矛盾

用法:
    python3 knowledge_graph_ingest_all.py --dry-run    # 预览
    python3 knowledge_graph_ingest_all.py --ingest    # 开始摄入
    python3 knowledge_graph_ingest_all.py --lint      # 检查重复矛盾
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
import urllib.request
import time

# 配置
SESSIONS_DIR = Path("/home/liujerry/.openclaw/agents/main/sessions")
GRAPHITI_URL = "http://localhost:8000"
BATCH_SIZE = 5  # 每批发送的消息数

class ConversationIngestor:
    def __init__(self):
        self.sessions = []
        self.entities = []
        self.duplicates = []
        self.errors = []
        
    def scan_sessions(self):
        """扫描所有会话文件"""
        print("📂 扫描会话文件...")
        session_files = sorted(SESSIONS_DIR.glob("*.jsonl"), 
                              key=lambda x: x.stat().st_mtime)
        print(f"   找到 {len(session_files)} 个会话文件")
        return session_files
    
    def extract_messages(self, session_file):
        """从会话文件提取消息"""
        messages = []
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get('type') == 'message':
                            msg = data.get('message', {})
                            role = msg.get('role', '')
                            content = msg.get('content', [])
                            
                            if isinstance(content, list) and content:
                                text = content[0].get('text', '')
                                if text and role in ['user', 'assistant']:
                                    # 提取时间戳
                                    ts = data.get('timestamp', '')
                                    if ts:
                                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                        date = dt.strftime('%Y-%m-%d')
                                    else:
                                        date = 'unknown'
                                    
                                    messages.append({
                                        'role': role,
                                        'content': text[:500],  # 限制长度
                                        'date': date,
                                        'session': session_file.name
                                    })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"   ⚠️ 读取失败 {session_file.name}: {e}")
        
        return messages
    
    def extract_key_facts(self, messages):
        """从消息中提取关键事实"""
        facts = []
        
        # 关键模式匹配
        patterns = {
            'decision': [
                r'决定(.+)',
                r'已确定(.+)',
                r'方案.*[:：](.+)',
                r'修复.*[:：](.+)',
            ],
            'insight': [
                r'发现[:：](.+)',
                r'根因[:：](.+)',
                r'关键[:：](.+)',
                r'重要[:：](.+)',
            ],
            'learning': [
                r'学到(.+)',
                r'认识到(.+)',
                r'理解到(.+)',
            ],
            'task': [
                r'已完成[:：](.+)',
                r'完成了(.+)',
                r'任务[:：](.+)',
            ]
        }
        
        for msg in messages:
            text = msg['content']
            
            # 提取QQ号
            qq_matches = re.findall(r'\b(\d{9,10})\b', text)
            if qq_matches:
                for qq in qq_matches:
                    facts.append({
                        'type': 'qq_id',
                        'value': qq,
                        'context': text[:100],
                        'date': msg['date']
                    })
            
            # 提取关键概念
            concept_patterns = [
                r'RSI', r'Buffett', r'Graphiti', r'Moltbook', 
                r'cron', r'API', r'知识图谱', r'筛选', r'采集'
            ]
            for concept in concept_patterns:
                if concept in text:
                    facts.append({
                        'type': 'concept',
                        'value': concept,
                        'context': text[:100],
                        'date': msg['date']
                    })
        
        return facts
    
    def create_entity_prompt(self, session_messages, session_name):
        """为会话创建 Graphiti 实体"""
        
        # 提取关键信息
        dates = set(m['date'] for m in session_messages if m['date'] != 'unknown')
        date_range = f"{min(dates)}~{max(dates)}" if dates else "unknown"
        
        # 统计
        user_msgs = [m for m in session_messages if m['role'] == 'user']
        assistant_msgs = [m for m in session_messages if m['role'] == 'assistant']
        
        # 提取关键内容摘要
        contents = [m['content'][:200] for m in session_messages[:10]]
        
        prompt = f"""【会话归档 - 批量 Ingest】

会话文件: {session_name}
日期范围: {date_range}
消息数: {len(session_messages)} (用户: {len(user_msgs)}, 助手: {len(assistant_msgs)})

内容摘要:
{chr(10).join(contents)}

请为该会话创建 Entity，提取:
1. 主要话题/主题
2. 关键决策
3. 重要发现
4. 涉及的概念

Entity group_id: "conversations"
"""
        return prompt
    
    def send_to_graphiti(self, prompts):
        """批量发送到 Graphiti"""
        print(f"\n📤 发送 {len(prompts)} 批到 Graphiti...")
        
        for i, prompt in enumerate(prompts):
            messages = [{
                "role": "system",
                "role_type": "system",
                "content": prompt
            }]
            
            data = json.dumps({
                "group_id": "conversations",
                "messages": messages
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f'{GRAPHITI_URL}/messages',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"   ✅ 批次 {i+1}/{len(prompts)}: 已发送")
            except Exception as e:
                print(f"   ❌ 批次 {i+1} 失败: {e}")
                self.errors.append({'batch': i, 'error': str(e)})
            
            # 避免限流
            time.sleep(0.5)
        
        print(f"\n📊 发送完成: {len(prompts) - len(self.errors)} 成功, {len(self.errors)} 失败")
    
    def run_lint_check(self):
        """运行 Lint 健康检查"""
        print("\n🔍 运行 Lint 健康检查...")
        os.system("python3 /home/liujerry/moltbot/scripts/knowledge_graph_lint.py 2>&1 | head -50")
    
    def run(self, dry_run=False, ingest=False, lint=False):
        """主流程"""
        print("=" * 60)
        print("📚 知识图谱全量摄入 - Karpathy LLM Wiki Ingest")
        print("=" * 60)
        
        # Step 1: 扫描会话
        session_files = self.scan_sessions()
        
        # Step 2: 提取消息 (只处理最近的100个文件)
        print("\n📖 提取消息...")
        all_messages = []
        for sf in session_files[-100:]:  # 最近100个会话
            msgs = self.extract_messages(sf)
            if msgs:
                all_messages.append({
                    'file': sf.name,
                    'messages': msgs
                })
        
        print(f"   提取了 {len(all_messages)} 个会话的消息")
        
        if dry_run:
            print("\n📋 预览 (前3个会话):")
            for item in all_messages[:3]:
                print(f"\n   {item['file']}:")
                print(f"   - {len(item['messages'])} 条消息")
                if item['messages']:
                    print(f"   - 首条: {item['messages'][0]['content'][:80]}...")
            return
        
        if ingest:
            # Step 3: 创建 prompts
            prompts = []
            for item in all_messages:
                prompt = self.create_entity_prompt(item['messages'], item['file'])
                prompts.append(prompt)
            
            print(f"\n📝 准备发送 {len(prompts)} 个会话到 Graphiti")
            
            # 确认
            confirm = input("   继续? (y/n): ")
            if confirm.lower() != 'y':
                print("   已取消")
                return
            
            # Step 4: 发送
            self.send_to_graphiti(prompts)
        
        if lint:
            # Step 5: Lint 检查
            self.run_lint_check()

def main():
    import sys
    
    ingestor = ConversationIngestor()
    
    if '--dry-run' in sys.argv:
        ingestor.run(dry_run=True)
    elif '--ingest' in sys.argv:
        ingestor.run(ingest=True)
    elif '--lint' in sys.argv:
        ingestor.run(lint=True)
    else:
        print(__doc__)
        print("\n用法:")
        print("  --dry-run  预览要摄入的内容")
        print("  --ingest   开始摄入到知识图谱")
        print("  --lint     运行 Lint 检查")

if __name__ == "__main__":
    main()
