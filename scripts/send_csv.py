#!/usr/bin/env python3
"""
发送CSV数据到QQ - 发送完整内容
"""
import sys
import os
import subprocess

def send_csv_content(target: str, file_path: str, max_rows: int = 50, caption: str = ""):
    """发送CSV完整内容到QQ"""
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # 构建消息
        lines = []
        lines.append(f"📊 {file_name}")
        lines.append(f"📊 大小: {file_size:,} bytes")
        lines.append(f"📊 行数: {len(df):,}")
        lines.append(f"📊 列: {', '.join(df.columns)}")
        
        if caption:
            lines.append(f"\n{caption}")
        
        message = "\n".join(lines)
        
        # 发送文件信息
        openclaw_cmd = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"
        
        result = subprocess.run(
            [openclaw_cmd, "message", "send", "--target", target, "--message", message],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ 发送失败: {result.stderr}")
            return False
        
        print("✅ 文件信息已发送")
        
        # 发送数据内容（分块发送）
        print(f"📤 发送数据内容...")
        
        total_rows = len(df)
        sent = 0
        
        for start in range(0, total_rows, max_rows):
            end = min(start + max_rows, total_rows)
            chunk = df.iloc[start:end]
            
            # 格式化表格
            table = chunk.to_string(index=False)
            
            # 限制长度
            if len(table) > 1800:
                table = table[:1800] + "\n... (内容过长已截断)"
            
            chunk_msg = f"```\n{table}\n```"
            
            chunk_result = subprocess.run(
                [openclaw_cmd, "message", "send", "--target", target, "--message", chunk_msg],
                capture_output=True,
                text=True
            )
            
            if chunk_result.returncode == 0:
                sent += (end - start)
                print(f"   发送 {start+1}-{end}/{total_rows}")
            else:
                print(f"   ❌ 发送失败")
                break
        
        print(f"\n✅ 完成! 共发送 {sent}/{total_rows} 行数据")
        return True
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def send_csv_markdown(target: str, file_path: str, caption: str = ""):
    """发送CSV为Markdown表格"""
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        
        file_name = os.path.basename(file_path)
        
        # 发送Markdown表格
        markdown = f"## {file_name}\n\n"
        markdown += f"**行数**: {len(df):,} | **列**: {len(df.columns)}\n\n"
        
        # 表头
        headers = " | ".join(df.columns)
        separator = " | ".join(["---"] * len(df.columns))
        
        markdown += f"| {headers} |\n| {separator} |\n"
        
        # 前10行
        for _, row in df.head(10).iterrows():
            values = " | ".join(str(v)[:15] for v in row.values)
            markdown += f"| {values} |\n"
        
        markdown += f"\n*共 {len(df):,} 行，数据完整版请下载文件*"
        
        if caption:
            markdown = f"{caption}\n\n{markdown}"
        
        # 发送
        openclaw_cmd = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"
        
        result = subprocess.run(
            [openclaw_cmd, "message", "send", "--target", target, "--message", markdown],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Markdown表格已发送")
            return True
        else:
            print(f"❌ 发送失败: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python3 send_csv.py content <target> <file> [行数] [caption]")
        print("  python3 send_csv.py table <target> <file> [caption]")
        print()
        print("示例:")
        print("  python3 send_csv.py content 740884666 /home/liujerry/金融数据/stocks/600519.csv 20")
        print("  python3 send_csv.py table 740884666 /home/liujerry/金融数据/stocks/600519.csv")
        sys.exit(1)
    
    mode = sys.argv[1]
    target = sys.argv[2]
    file_path = sys.argv[3]
    
    if mode == "content":
        max_rows = int(sys.argv[4]) if len(sys.argv) > 4 else 50
        caption = sys.argv[5] if len(sys.argv) > 5 else ""
        send_csv_content(target, file_path, max_rows, caption)
    elif mode == "table":
        caption = sys.argv[4] if len(sys.argv) > 4 else ""
        send_csv_markdown(target, file_path, caption)
    else:
        print(f"未知模式: {mode}")


if __name__ == "__main__":
    main()
