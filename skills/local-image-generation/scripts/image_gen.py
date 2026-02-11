#!/usr/bin/env python3
"""
Local Image Generation Script

使用本地 Antigravity 反向代理生成图片
API 格式: OpenAI Chat Completions + extra_body
"""
import os
import sys
import base64
import io
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from PIL import Image
except ImportError:
    print("❌ 请安装依赖: uv pip install pillow")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("❌ 请安装依赖: uv pip install openai")
    sys.exit(1)


# 默认配置
DEFAULT_API_KEY = os.environ.get("LOCAL_IMAGE_API_KEY", "sk-c9f03255f1764b0ea72f8d54cd325550")
DEFAULT_BASE_URL = os.environ.get("LOCAL_IMAGE_BASE_URL", "http://127.0.0.1:8045/v1")
DEFAULT_MODEL = "gemini-3-pro-image"
DEFAULT_SIZE = "1024x1024"

# 预设宽高比 -> 尺寸映射
SIZE_MAP = {
    # 1:1
    "1:1": "1024x1024",
    "1x1": "1024x1024",
    # 4:3
    "4:3": "1216x896",
    "4x3": "1216x896",
    "3:4": "896x1216",
    "3x4": "896x1216",
    # 16:9
    "16:9": "1280x720",
    "16x9": "1280x720",
    "9:16": "720x1280",
    "9x16": "720x1280",
    # 21:9
    "21:9": "1440x616",
    "21x9": "1440x616",
    # 3:2
    "3:2": "1344x896",
    "3x2": "1344x896",
    # 2:3
    "2:3": "896x1344",
    "2x3": "896x1344",
}

# 标准分辨率
RESOLUTIONS = {
    "sd": "640x360",
    "hd": "1280x720",
    "fhd": "1920x1080",
    "2k": "2048x1152",
    "4k": "3840x2160",
    "8k": "7680x4320",
}

# 最大尺寸限制
MAX_SIZE = 4096


class LocalImageGenerator:
    """本地图片生成器"""
    
    def __init__(
        self,
        api_key: str = DEFAULT_API_KEY,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
    
    def _parse_size(self, size: str) -> str:
        """解析尺寸参数"""
        # 预处理：移除空格
        size = size.strip().replace(" ", "")
        
        # 宽高比映射
        if size.lower() in SIZE_MAP:
            return SIZE_MAP[size.lower()]
        
        # 分辨率映射
        if size.lower() in RESOLUTIONS:
            return RESOLUTIONS[size.lower()]
        
        # WxH 格式
        if "x" in size.lower():
            parts = size.lower().split("x")
            if len(parts) == 2:
                try:
                    width = int(parts[0])
                    height = int(parts[1])
                    # 检查最大限制
                    width = min(width, MAX_SIZE)
                    height = min(height, MAX_SIZE)
                    return f"{width}x{height}"
                except ValueError:
                    pass
        
        return size
    
    def generate(
        self,
        prompt: str,
        size: str = DEFAULT_SIZE,
        quality: str = "hd"
    ) -> Image.Image:
        """生成单张图片"""
        size = self._parse_size(size)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"size": size}
        )
        
        # 解析 base64 图片
        content = response.choices[0].message.content
        
        # 查找 base64 数据
        if "base64" in content:
            # 提取 base64 字符串
            import re
            match = re.search(r'base64,([A-Za-z0-9+/=]+)', content)
            if match:
                image_data = base64.b64decode(match.group(1))
                image = Image.open(io.BytesIO(image_data))
                return image
        
        raise ValueError(f"无法解析图片响应: {content[:200]}")
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: str,
        size: str = DEFAULT_SIZE,
        quality: str = "hd"
    ) -> None:
        """生成并保存图片"""
        image = self.generate(prompt, size, quality)
        output_format = Path(output_path).suffix[1:].upper() or "PNG"
        image.save(output_path, format=output_format)
    
    def batch_generate(
        self,
        prompts: list[str],
        size: str = DEFAULT_SIZE,
        output_dir: str = "output",
        output_format: str = "PNG"
    ) -> None:
        """批量生成图片"""
        size = self._parse_size(size)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        success = 0
        failed = 0
        
        for i, prompt in enumerate(prompts, 1):
            try:
                print(f"[{i}/{len(prompts)}] 生成中...")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    extra_body={"size": size}
                )
                
                content = response.choices[0].message.content
                
                # 提取 base64
                import re
                match = re.search(r'base64,([A-Za-z0-9+/=]+)', content)
                if match:
                    image_data = base64.b64decode(match.group(1))
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"image_{timestamp}_{i}.{output_format.lower()}"
                    file_path = output_path / filename
                    
                    with open(file_path, "wb") as f:
                        f.write(image_data)
                    
                    print(f"   ✅ {file_path.name}")
                    success += 1
                else:
                    print(f"   ❌ 无法解析响应")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ 失败: {str(e)[:50]}")
                failed += 1
        
        print()
        print(f"🎉 完成! 成功: {success}, 失败: {failed}")


def interactive_mode():
    """交互模式"""
    print("🎨 Local Image Generator - 交互模式")
    print("输入 'quit' 退出")
    
    generator = LocalImageGenerator()
    
    while True:
        try:
            prompt = input("\n请输入图片描述: ").strip()
            if prompt.lower() in ["quit", "exit", "q"]:
                print("👋 再见!")
                break
            
            if not prompt:
                continue
            
            size = input("尺寸 (默认 1024x1024): ").strip() or DEFAULT_SIZE
            
            image = generator.generate(prompt, size)
            
            output_path = input("保存路径: ").strip() or "output.png"
            image.save(output_path)
            
            print(f"✅ 已保存: {output_path}")
            print(f"🖼️ 尺寸: {image.size}")
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Local Image Generation - 使用本地 Antigravity 代理生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--prompt", "-p",
        help="生成图片的提示词"
    )
    
    parser.add_argument(
        "--prompts", "-P",
        nargs="+",
        help="批量提示词列表"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output.png",
        help="输出文件路径 (默认: output.png)"
    )
    
    parser.add_argument(
        "--output_dir", "-d",
        default="output",
        help="批量输出目录 (默认: output)"
    )
    
    parser.add_argument(
        "--size", "-s",
        default=DEFAULT_SIZE,
        help=f"图片尺寸，支持 WxH 格式或预设 (默认: {DEFAULT_SIZE})"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        help="图片宽度 (与 --height 一起使用)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        help="图片高度 (与 --width 一起使用)"
    )
    
    parser.add_argument(
        "--aspect_ratio", "-a",
        choices=list(SIZE_MAP.keys()),
        help=f"预设宽高比"
    )
    
    parser.add_argument(
        "--resolution", "-r",
        choices=list(RESOLUTIONS.keys()),
        help=f"标准分辨率: {', '.join(RESOLUTIONS.keys())}"
    )
    
    parser.add_argument(
        "--quality", "-q",
        choices=["standard", "hd", "medium"],
        default="hd",
        help="图片质量 (默认: hd)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["png", "jpeg", "jpg", "webp"],
        default="png",
        help="输出格式 (默认: png)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互模式"
    )
    
    parser.add_argument(
        "--api_key",
        default=DEFAULT_API_KEY,
        help="API密钥"
    )
    
    parser.add_argument(
        "--base_url",
        default=DEFAULT_BASE_URL,
        help="API地址"
    )
    
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help="模型名称 (默认: gemini-3-pro-image)"
    )
    
    args = parser.parse_args()
    
    # 计算尺寸
    if args.width and args.height:
        size = f"{args.width}x{args.height}"
    elif args.aspect_ratio:
        size = args.aspect_ratio
    elif args.resolution:
        size = args.resolution
    else:
        size = args.size
    
    # 初始化客户端
    generator = LocalImageGenerator(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model
    )
    
    # 格式
    output_format = args.format.upper()
    
    if args.interactive:
        interactive_mode()
        return
    
    if args.prompts:
        # 批量生成
        print(f"📦 批量生成 {len(args.prompts)} 张图片...")
        print(f"📁 输出目录: {args.output_dir}")
        print(f"📐 尺寸: {size}")
        
        generator.batch_generate(
            prompts=args.prompts,
            size=size,
            output_dir=args.output_dir,
            output_format=output_format
        )
        print(f"\n🎉 完成! 输出目录: {args.output_dir}")
        return
    
    if args.prompt:
        # 单张生成
        print(f"🎨 生成图片...")
        print(f"📝 提示词: {args.prompt}")
        print(f"📐 尺寸: {size}")
        print(f"✨ 质量: {args.quality}")
        
        generator.generate_and_save(
            prompt=args.prompt,
            output_path=args.output,
            size=size,
            quality=args.quality
        )
        
        print(f"\n✅ 已保存: {args.output}")
        return
    
    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
