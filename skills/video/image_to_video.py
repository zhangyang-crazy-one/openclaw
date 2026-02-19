#!/usr/bin/env python3
"""
图像序列生成视频技能
用硅基流动生成连贯图像 + ffmpeg合成视频
完全免费，无需翻墙!
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
from image.siliconflow_image import generate_image, OUTPUT_DIR

def generate_video_from_images(image_paths: list, output_path: str, fps: int = 4) -> str:
    """用ffmpeg将图像合成为视频"""
    
    # 创建临时目录存放排序后的图片
    import shutil
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    
    # 复制并重命名图片以确保顺序正确
    for i, src_path in enumerate(image_paths):
        dst_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
        shutil.copy(src_path, dst_path)
    
    # 使用ffmpeg合成视频
    cmd = [
        "ffmpeg",
        "-y",  # 覆盖输出
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1024:1024",
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    
    # 清理临时目录
    shutil.rmtree(temp_dir)
    
    return output_path

def generate_image_sequence(prompt: str, num_frames: int = 8) -> list:
    """生成图像序列"""
    
    # 简化提示词，去掉时间相关词汇
    base_prompt = prompt
    
    image_paths = []
    
    for i in range(num_frames):
        print(f"生成第 {i+1}/{num_frames} 帧...")
        
        # 添加序号避免缓存
        frame_prompt = f"{base_prompt}, frame {i+1}"
        
        try:
            img_path = generate_image(frame_prompt)
            image_paths.append(img_path)
            print(f"  ✅ {img_path}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    return image_paths

def create_video(prompt: str, output_file: str = None, num_frames: int = 8, fps: int = 4) -> str:
    """生成视频的主函数"""
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = str(OUTPUT_DIR / f"video_{timestamp}.mp4")
    
    # 生成图像序列
    print(f"\n📷 生成图像序列 ({num_frames} 帧)...")
    image_paths = generate_image_sequence(prompt, num_frames)
    
    if not image_paths:
        raise Exception("未能生成任何图像")
    
    # 合成视频
    print(f"\n🎬 合成视频...")
    video_path = generate_video_from_images(image_paths, output_file, fps)
    
    return video_path

if __name__ == "__main__":
    # 测试
    prompt = "A cute orange cat running in a garden, sunny day, photorealistic"
    
    print(f"提示词: {prompt}")
    print(f"帧数: 8")
    
    video_path = create_video(prompt, num_frames=8)
    
    size = os.path.getsize(video_path)
    print(f"\n✅ 视频生成成功!")
    print(f"   文件: {video_path}")
    print(f"   大小: {size / 1024:.1f} KB")
