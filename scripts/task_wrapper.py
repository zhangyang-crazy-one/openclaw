#!/usr/bin/env python3
"""
任务包装器 - 支持上下文继承的任务执行
"""
import argparse
import subprocess
import sys
import json
import os
from datetime import datetime

def load_state():
    """加载上次状态"""
    state_file = os.path.expanduser("~/.openclaw/task_state.json")
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存状态"""
    state_file = os.path.expanduser("~/.openclaw/task_state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def run_task(task_name, command, description):
    """执行任务"""
    print(f"[{datetime.now()}] 执行任务: {task_name}")
    print(f"命令: {command}")
    
    # 加载状态
    state = load_state()
    
    # 添加上下文
    env = os.environ.copy()
    if 'CONTEXT' in state:
        env['TASK_CONTEXT'] = json.dumps(state.get('context', {}))
    
    # 执行命令
    result = subprocess.run(
        command,
        shell=True,
        env=env,
        capture_output=True,
        text=True,
        timeout=600
    )
    
    # 保存结果
    state[task_name] = {
        'last_run': datetime.now().isoformat(),
        'status': 'success' if result.returncode == 0 else 'failed',
        'output': result.stdout[-5000:] if result.stdout else '',
        'error': result.stderr[-1000:] if result.stderr else ''
    }
    save_state(state)
    
    print(f"状态: {'成功' if result.returncode == 0 else '失败'}")
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='任务包装器')
    parser.add_argument('task_name', help='任务名称')
    parser.add_argument('command', help='要执行的命令')
    parser.add_argument('--description', default='', help='任务描述')
    
    args = parser.parse_args()
    
    success = run_task(args.task_name, args.command, args.description)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
