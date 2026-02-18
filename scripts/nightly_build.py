#!/usr/bin/env python3
"""
夜间构建模式 - 主动式工作流
在人类休息时执行主动任务
"""
import os
import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / "moltbot" / "memory"
LOG_DIR = Path.home() / ".logs"

def save_state():
    """保存当前状态，防止上下文压缩丢失"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 读取今日记忆
    memory_file = MEMORY_DIR / f"{today}.md"
    
    if memory_file.exists():
        with open(memory_file) as f:
            content = f.read()
        
        # 保存到备份
        backup_file = LOG_DIR / f"state_backup_{today}.txt"
        with open(backup_file, "w") as f:
            f.write(content)
            f.write(f"\n\n# Auto-saved at {datetime.now().isoformat()}\n")
        
        print(f"✅ 状态已备份: {backup_file}")
    else:
        print("⚠️ 今日记忆文件不存在")

def generate_todo():
    """生成次日待办"""
    today = datetime.now().strftime('%Y-%m-%d')
    todo_file = LOG_DIR / f"todo_{today}.txt"
    
    todos = []
    
    # 检查cron任务
    todos.append("📋 每日cron任务:")
    todos.append("   - 9:00 每日股票分析")
    todos.append("   - 15:00 行为金融分析")
    todos.append("   - 20:00 Moltbook发帖")
    
    # 检查持仓
    todos.append("\n📊 持仓关注:")
    todos.append("   - 光线传媒 (成本10.376, 现价~27)")
    todos.append("   - 三丰智能 (成本10.376, 现价~8.68)")
    
    # 检查待办
    todos.append("\n🔔 待办事项:")
    todos.append("   - [ ] 优化选股策略")
    todos.append("   - [ ] 增加舆情数据源")
    todos.append("   - [ ] 完善行为金融模型")
    
    with open(todo_file, "w") as f:
        f.write(f"# 次日待办 - {today}\n")
        f.write("\n".join(todos))
    
    print(f"✅ 待办已生成: {todo_file}")

def data_cleanup():
    """清理临时数据"""
    import glob
    
    # 清理临时CSV
    temp_files = glob.glob("/tmp/chuangye_*.csv")
    for f in temp_files:
        try:
            os.remove(f)
            print(f"🗑️ 清理: {f}")
        except:
            pass

def main():
    print(f"\n{'='*50}")
    print(f"🌙 夜间构建模式 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    
    # 1. 保存状态
    print("\n📦 保存状态...")
    save_state()
    
    # 2. 清理临时文件
    print("\n🧹 清理临时文件...")
    data_cleanup()
    
    # 3. 生成待办
    print("\n📝 生成待办...")
    generate_todo()
    
    print(f"\n{'='*50}")
    print("✅ 夜间构建完成")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
