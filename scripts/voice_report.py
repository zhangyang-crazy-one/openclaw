#!/usr/bin/env python3
"""
语音播报脚本
生成市场分析语音并发送到QQ
"""
import asyncio
import edge_tts
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path.home() / ".logs" / "tts"

async def generate_voice_report(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """生成语音文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(datetime.now().timestamp())
    output_file = str(OUTPUT_DIR / f"report_{timestamp}.mp3")
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    
    return output_file

def generate_report_text() -> str:
    """生成播报文本"""
    # 这里可以调用行为分析脚本获取最新数据
    return """今日市场播报：根据行为金融学分析，当前市场综合评分43分，情绪状态为中性偏恐惧。资金面主力净流出690亿元，板块普跌，84%的概念板块出现下跌。建议投资者保持谨慎，控制仓位，采用逆向投资策略。投资需谨慎，风险自担。"""

async def main():
    print(f"生成语音播报...")
    
    # 生成播报文本
    text = generate_report_text()
    print(f"播报内容: {text}")
    
    # 生成语音
    voice_file = await generate_voice_report(text)
    
    size = os.path.getsize(voice_file)
    print(f"生成成功: {voice_file} ({size} bytes)")
    
    return voice_file, text

if __name__ == "__main__":
    file, text = asyncio.run(main())
    print(f"\n文件: {file}")
