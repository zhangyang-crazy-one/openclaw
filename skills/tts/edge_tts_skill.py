#!/usr/bin/env python3
"""
Edge TTS 语音技能
生成中文语音
"""
import asyncio
import edge_tts
import os
from pathlib import Path

VOICE_DEFAULT = "zh-CN-XiaoxiaoNeural"
OUTPUT_DIR = Path.home() / ".logs" / "tts"

async def speak(text: str, voice: str = VOICE_DEFAULT, output_file: str = None) -> str:
    """
    生成语音文件
    
    Args:
        text: 要朗读的文本
        voice: 语音类型
        output_file: 输出文件路径
    
    Returns:
        生成的文件路径
    """
    if not output_file:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        import time
        output_file = str(OUTPUT_DIR / f"tts_{int(time.time())}.mp3")
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    
    return output_file

def speak_sync(text: str, voice: str = VOICE_DEFAULT, output_file: str = None) -> str:
    """同步版本"""
    return asyncio.run(speak(text, voice, output_file))

async def list_voices():
    """列出可用语音"""
    voices = await edge_tts.list_voices()
    
    # 中文语音
    zh = [v for v in voices if 'zh-CN' in v['ShortName']]
    
    return zh

if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "你好，我是DeepSeeker。语音技能测试成功！"
    
    print(f"生成语音: {text}")
    file = speak_sync(text)
    print(f"文件: {file}")
    print(f"大小: {os.path.getsize(file)} bytes")
