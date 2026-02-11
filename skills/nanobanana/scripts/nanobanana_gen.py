#!/usr/bin/env python3
"""
Nano Banana Image Generation Skill
使用 nanobanana 反向代理生成图片

使用方法:
    python3 nanobanana_gen.py --prompt "提示词" --output image.png
    python3 nanobanana_gen.py --interactive  # 交互模式
    python3 nanobanana_gen.py --prompts "词1" "词2" "词3"  # 批量生成
"""
import os
import sys
import base64
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("❌ 需要安装 openai: uv pip install openai")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("❌ 需要安装 pillow: uv pip install pillow")
    sys.exit(1)


# 预设宽高比
ASPECT_RATIOS = {
    "1:1": (1024, 1024),      # 正方形
    "4:3": (1024, 768),        # 标准
    "3:4": (768, 1024),        # 竖版标准
    "16:9": (1920, 1080),      # 宽屏
    "9:16": (1080, 1920),      # 竖屏
    "21:9": (1920, 820),       # 电影宽屏
    "9:21": (820, 1920),       # 竖版电影
    "3:2": (1536, 1024),       # 摄影标准
    "2:3": (1024, 1536),       # 竖版摄影
    "2:1": (2048, 1024),       # 宽幅
    "1:2": (1024, 2048),       # 竖版宽幅
}

# 标准分辨率
RESOLUTIONS = {
    "sd": (640, 360),          # 标清
    "hd": (1280, 720),         # 高清
    "fhd": (1920, 1080),       # 全高清
    "2k": (2560, 1440),        # 2K
    "4k": (3840, 2160),        # 4K
    "8k": (7680, 4320),        # 8K
}


class NanoBanana:
    """Nano Banana 图像生成客户端"""
    
    DEFAULT_API_KEY = "sk-antigravity"
    DEFAULT_BASE_URL = "http://127.0.0.1:8045/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gemini-3-pro-image"
    ):
        """初始化客户端
        
        Args:
            api_key: API密钥，默认 sk-antigravity
            base_url: API地址，默认 http://127.0.0.1:8045/v1
            model: 模型名称
        """
        self.api_key = api_key or os.environ.get("NANOBANANA_API_KEY", self.DEFAULT_API_KEY)
        self.base_url = base_url or os.environ.get("NANOBANANA_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = model
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _parse_size(self, size: str) -> Tuple[int, int]:
        """解析尺寸字符串 WxH 或预设"""
        size_lower = size.lower().strip()
        
        # 检查是否为预设
        if size_lower in ASPECT_RATIOS:
            return ASPECT_RATIOS[size_lower]
        
        # 检查是否为分辨率名称
        if size_lower in RESOLUTIONS:
            return RESOLUTIONS[size_lower]
        
        # 解析 WxH 格式
        if "x" in size_lower:
            parts = size_lower.split("x")
            if len(parts) == 2:
                try:
                    width = int(parts[0])
                    height = int(parts[1])
                    # 限制最大尺寸
                    width = min(width, 8192)
                    height = min(height, 8192)
                    return width, height
                except ValueError:
                    pass
        
        # 默认返回 1920x1080
        return 1920, 1080
    
    def _validate_size(self, width: int, height: int) -> Tuple[int, int]:
        """验证并限制尺寸"""
        # gemini-3-pro-image 支持的最大尺寸通常是 4096x4096
        max_size = 4096
        
        if width > max_size or height > max_size:
            # 按比例缩小
            if width > height:
                ratio = max_size / width
                width = max_size
                height = int(height * ratio)
            else:
                ratio = max_size / height
                height = max_size
                width = int(width * ratio)
        
        return width, height
    
    def _format_size_for_api(self, width: int, height: int) -> str:
        """格式化尺寸为 API 要求的格式"""
        return f"{width}x{height}"
    
    def generate(
        self,
        prompt: str,
        size: str = "1920x1080",
        quality: str = "hd",
        n: int = 1,
        output_format: str = "png"
    ) -> Image.Image:
        """生成图片
        
        Args:
            prompt: 提示词
            size: 尺寸，支持 WxH 格式或预设 (如 16:9, 4K)
            quality: 质量 standard | hd | medium
            n: 生成数量
            output_format: 输出格式 png | jpeg | jpg | webp
        
        Returns:
            PIL Image 对象
        """
        # 解析尺寸
        width, height = self._parse_size(size)
        
        # 验证尺寸
        width, height = self._validate_size(width, height)
        
        # 格式化尺寸
        size_str = self._format_size_for_api(width, height)
        
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size_str,
            quality=quality,
            n=n,
            response_format="b64_json"
        )
        
        # 解码 base64
        image_data = base64.b64decode(response.data[0].b64_json)
        
        # 返回 PIL Image
        from io import BytesIO
        img = Image.open(BytesIO(image_data))
        
        # 转换为指定格式
        if output_format.lower() in ["jpeg", "jpg"]:
            img = img.convert("RGB")
        
        return img
    
    def generate_b64(
        self,
        prompt: str,
        size: str = "1920x1080",
        quality: str = "hd",
        n: int = 1
    ) -> str:
        """生成图片并返回 base64 数据
        
        Args:
            prompt: 提示词
            size: 尺寸
            quality: 质量
            n: 生成数量
        
        Returns:
            base64 编码的图片数据
        """
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
            response_format="b64_json"
        )
        
        return response.data[0].b64_json
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: str,
        size: str = "1920x1080",
        quality: str = "hd",
        output_format: str = "png"
    ) -> str:
        """生成图片并保存
        
        Args:
            prompt: 提示词
            output_path: 输出文件路径
            size: 尺寸
            quality: 质量
            output_format: 输出格式
        
        Returns:
            保存的文件路径
        """
        img = self.generate(prompt, size, quality, output_format=output_format)
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 保存图片
        img.save(output_path, format=output_format.upper())
        return output_path
    
    def batch_generate(
        self,
        prompts: List[str],
        size: str = "1920x1080",
        quality: str = "hd",
        output_dir: str = "output",
        output_format: str = "png"
    ) -> List[str]:
        """批量生成图片
        
        Args:
            prompts: 提示词列表
            size: 尺寸
            quality: 质量
            output_dir: 输出目录
            output_format: 输出格式
        
        Returns:
            保存的文件路径列表
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        saved_paths = []
        
        for i, prompt in enumerate(prompts):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/image_{i+1}_{timestamp}.{output_format}"
            
            path = self.generate_and_save(
                prompt=prompt,
                output_path=filename,
                size=size,
                quality=quality,
                output_format=output_format
            )
            saved_paths.append(path)
            print(f"✅ 已保存: {filename}")
        
        return saved_paths


def save_image_from_b64(b64_data: str, output_path: str) -> str:
    """从 base64 数据保存图片"""
    image_data = base64.b64decode(b64_data)
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path


def interactive_mode():
    """交互模式"""
    print("🎨 Nano Banana 图像生成器")
    print("=" * 50)
    print("输入提示词生成图片，输入 q 退出")
    print()
    
    client = NanoBanana()
    
    while True:
        try:
            prompt = input("📝 提示词: ").strip()
            
            if not prompt:
                continue
            
            if prompt.lower() in ["q", "quit", "exit"]:
                print("👋 再见!")
                break
            
            # 生成并保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"output_{timestamp}.png"
            
            print("⏳ 生成中...")
            client.generate_and_save(
                prompt=prompt,
                output_path=output,
                size="1920x1080",
                quality="hd"
            )
            
            print(f"✅ 已保存: {output}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Nano Banana 图像生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --prompt "一座未来主义风格的城市"
  %(prog)s --prompt "赛博朋克城市" --output my_image.png --size 1024x1024
  %(prog)s --prompts "词1" "词2" "词3" --output_dir images
  %(prog)s --interactive
        """
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
        default="1920x1080",
        help="图片尺寸，支持 WxH 格式或预设 (16:9, 4:3, 1:1, 9:16, 4K, 2K 等) (默认: 1920x1080)"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        help="图片宽度 (与 --height 一起使用，覆盖 --size)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        help="图片高度 (与 --width 一起使用，覆盖 --size)"
    )
    
    parser.add_argument(
        "--aspect_ratio", "-a",
        choices=list(ASPECT_RATIOS.keys()),
        help=f"预设宽高比: {', '.join(ASPECT_RATIOS.keys())}"
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
        help="API密钥"
    )
    
    parser.add_argument(
        "--base_url",
        help="API地址"
    )
    
    parser.add_argument(
        "--model", "-m",
        default="gemini-3-pro-image",
        help="模型名称 (默认: gemini-3-pro-image)"
    )
    
    args = parser.parse_args()
    
    # 确定输出目录为项目目录
    project_dir = Path(__file__).parent.parent.parent
    output_dir = project_dir / "output" / "nanobanana"
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
    client = NanoBanana(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model
    )
    
    if args.interactive:
        interactive_mode()
        return
    
    if args.prompts:
        # 批量生成
        print(f"📦 批量生成 {len(args.prompts)} 张图片...")
        print(f"📁 输出目录: {output_dir}")
        
        client.batch_generate(
            prompts=args.prompts,
            size=size,
            quality=args.quality,
            output_dir=str(output_dir),
            output_format=args.format
        )
        print(f"\n🎉 完成! 输出目录: {output_dir}")
        return
    
    if args.prompt:
        # 单张生成
        print(f"🎨 生成图片...")
        print(f"📝 提示词: {args.prompt}")
        print(f"📐 尺寸: {size}")
        print(f"✨ 质量: {args.quality}")
        print(f"📁 格式: {args.format}")
        
        # 生成输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(output_dir / f"image_{timestamp}.{args.format}")
        
        client.generate_and_save(
            prompt=args.prompt,
            output_path=output_path,
            size=size,
            quality=args.quality,
            output_format=args.format
        )
        
        print(f"\n✅ 已保存: {output_path}")
        return
    
    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
