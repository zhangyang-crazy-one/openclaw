#!/usr/bin/env python3
"""
generate_assets.py — MiniMax 素材生成 + Remotion 配置/TSX 输出

用法:
  # 从 JSON 脚本生成（推荐）
  python3 generate_assets.py --script-json ./public/script.json --output ./public

  # 快速模式：内联脚本
  python3 generate_assets.py --script "海滩日落|城市夜景|星空" --narration "第一段旁白|第二段旁白|第三段旁白" --output ./public

  # 仅生成 TSX（素材已存在）
  python3 generate_assets.py --script-json ./public/script.json --generate-tsx --output ./public
"""

import argparse
import json
import sys
import os
import re
from pathlib import Path

# 添加 skills 路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from minimax_api import generate_image, generate_speech, generate_scene_assets


# ============================================================
# 场景解析
# ============================================================
def parse_scenes(script: str, narrations: str = None) -> list:
    """
    将分镜脚本解析为场景列表。
    
    输入格式（用 | 分隔场景）:
      "场景1描述|场景2描述|场景3描述"
    """
    scene_texts = [s.strip() for s in script.split("|") if s.strip()]
    narration_list = [n.strip() for n in narrations.split("|")] if narrations else []

    scenes = []
    for i, text in enumerate(scene_texts):
        scenes.append({
            "scene_id": i,
            "image_prompt": _text_to_image_prompt(text),
            "narration": narration_list[i] if i < len(narration_list) else _text_to_narration(text),
            "duration_seconds": 5,
            "animation": _pick_animation(i, len(scene_texts)),
            "camera_move": _pick_camera(i),
            "transition": "crossfade",
        })
    return scenes


def _text_to_image_prompt(text: str) -> str:
    """将中文场景描述转化为英文 prompt"""
    mapping = {
        "海滩": "beautiful beach at sunset with golden sand and blue waves, cinematic, 4K",
        "日落": "golden sunset over the horizon, warm orange light, cinematic, 4K",
        "城市": "futuristic city skyline at night with neon lights, cinematic, 4K",
        "夜景": "city nightscape with glowing skyscrapers and traffic light trails, cinematic",
        "星空": "starry night sky with Milky Way, clear and bright, cinematic, 4K",
        "山": "majestic mountain range with snow peaks, dramatic clouds, cinematic, 4K",
        "森林": "dense green forest with sunlight filtering through trees, cinematic",
        "大海": "vast ocean with gentle waves, horizon view, cinematic, 4K",
        "樱花": "cherry blossom trees in full bloom, pink petals falling, cinematic",
        "雨": "rainy day with droplets on window, cozy atmosphere, cinematic",
        "雪": "snow-covered landscape with peaceful winter scenery, cinematic, 4K",
        "日出": "sunrise over mountains with golden morning light, cinematic, 4K",
    }
    prompt = text
    for cn, en in mapping.items():
        prompt = prompt.replace(cn, en)
    if prompt == text:
        prompt = f"Cinematic scene: {text}, professional photography, 4K, dramatic lighting"
    return prompt


def _text_to_narration(text: str) -> str:
    """将场景描述转化为默认旁白"""
    return f"这是第{len(text)}个场景，{text}。"


def _pick_animation(index: int, total: int) -> str:
    """根据场景位置选择动画类型"""
    if total <= 1:
        return "blur_reveal"
    if index == 0:
        return "blur_reveal"
    if index == total - 1:
        return "fade"
    ratio = index / (total - 1)
    if ratio < 0.4:
        return "fade"
    elif ratio < 0.7:
        return "char_explode"
    else:
        return "scramble"


def _pick_camera(index: int) -> str:
    """交替选择镜头运动"""
    moves = ["zoom_in", "pan_left", "zoom_out", "pan_right", "tilt_up", "static"]
    return moves[index % len(moves)]


# ============================================================
# JSON 脚本加载
# ============================================================
def load_script_json(path: str) -> dict:
    """加载 script.json 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def script_to_scenes(script_data: dict) -> list:
    """将完整脚本数据转换为场景列表（供素材生成用）"""
    scenes = []
    for s in script_data.get("scenes", []):
        scenes.append({
            "scene_id": s["id"],
            "image_prompt": s["image_prompt"],
            "narration": s["narration"],
            "duration_seconds": s.get("duration_seconds", 5),
        })
    return scenes


# ============================================================
# TSX 生成
# ============================================================
def generate_tsx(script_data: dict, assets: list, output_dir: str, fps: int = 30):
    """生成 src/index.tsx 和复制 SceneComposition.tsx"""
    project_dir = Path(output_dir).parent  # public/ → project root
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Build scene data for TSX
    scene_lines = []
    for i, s in enumerate(script_data.get("scenes", [])):
        # Find matching asset
        asset = next((a for a in assets if a.get("scene_id") == i), {})
        img_name = Path(asset.get("image_path", "")).name if asset.get("image_path") else ""
        audio_name = Path(asset.get("audio_path", "")).name if asset.get("audio_path") else ""
        dur = s.get("duration_seconds", 5) * fps

        # Escape quotes in text
        title = s.get("title", s.get("caption", "")).replace('"', '\\"')
        caption = s.get("caption", "").replace('"', '\\"')

        scene_lines.append(f"""      {{
        imagePath: "scenes/{img_name}",
        audioPath: "audio/{audio_name}",
        durationInFrames: {dur},
        animation: "{s.get('animation', 'fade')}",
        transition: "{s.get('transition', 'crossfade')}",
        cameraMove: "{s.get('camera_move', 'static')}",
        title: "{title}",
        caption: "{caption}",
        mood: "{s.get('mood', '')}",
      }}""")

    total_frames = sum(s.get("duration_seconds", 5) * fps for s in script_data.get("scenes", []))
    video_title = script_data.get("title", "My Video").replace('"', '\\"')

    index_content = f"""import React from 'react';
import {{ registerRoot, Composition }} from 'remotion';
import {{ VideoComposition, VideoProps, SceneData }} from './SceneComposition';

const scenes: SceneData[] = [
{",".join(scene_lines)}
];

registerRoot(function App() {{
  return (
    <Composition
      id="MyVideo"
      component={{VideoComposition}}
      props={{{{ scenes, title: "{video_title}" }} as VideoProps}}
      durationInFrames={{{total_frames}}}
      fps={{{fps}}}
      width={{1920}}
      height={{1080}}
    />
  );
}});
"""

    index_path = src_dir / "index.tsx"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    print(f"  Generated: {index_path}")

    # Copy SceneComposition.tsx template
    template_path = SKILL_DIR / "templates" / "SceneComposition.tsx"
    target_path = src_dir / "SceneComposition.tsx"
    if template_path.exists():
        import shutil
        shutil.copy2(template_path, target_path)
        print(f"  Copied: {target_path}")
    else:
        print(f"  WARNING: Template not found at {template_path}")

    return str(index_path)


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="MiniMax 素材生成 + TSX 输出")
    parser.add_argument("--script-json", type=str, help="完整脚本 JSON 文件路径")
    parser.add_argument("--script", type=str, help="快速模式：场景描述，用 | 分隔")
    parser.add_argument("--narration", type=str, help="快速模式：旁白文案，用 | 分隔")
    parser.add_argument("--output", type=str, default="./public", help="输出目录")
    parser.add_argument("--fps", type=int, default=30, help="帧率")
    parser.add_argument("--generate-tsx", action="store_true", help="同时生成 TSX 文件")
    parser.add_argument("--skip-assets", action="store_true", help="跳过素材生成（仅生成 TSX）")
    args = parser.parse_args()

    output_dir = Path(args.output)
    scenes_dir = output_dir / "scenes"
    audio_dir = output_dir / "audio"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Load or parse scenes
    script_data = None
    if args.script_json:
        print(f"📄 加载脚本: {args.script_json}")
        script_data = load_script_json(args.script_json)
        scene_list = script_to_scenes(script_data)
        print(f"   共 {len(scene_list)} 个场景")
    elif args.script:
        scene_list = parse_scenes(args.script, args.narration)
        script_data = {"title": "Video", "scenes": []}
        for i, s in enumerate(scene_list):
            script_data["scenes"].append({
                "id": i,
                "image_prompt": s["image_prompt"],
                "narration": s["narration"],
                "duration_seconds": s["duration_seconds"],
                "animation": s.get("animation", "fade"),
                "camera_move": s.get("camera_move", "static"),
                "transition": s.get("transition", "crossfade"),
                "caption": "",
                "mood": "",
            })
    else:
        print("❌ 请提供 --script-json 或 --script 参数")
        print(__doc__)
        sys.exit(1)

    # Generate assets
    if not args.skip_assets:
        print(f"\n🎨 生成 MiniMax 图片和旁白...")
        assets = generate_scene_assets(scene_list, str(output_dir))
        for a in assets:
            print(f"   Scene {a['scene_id']+1}: img={Path(a['image_path']).name}, audio={Path(a['audio_path']).name}")
    else:
        # Load existing asset info from remotion_scenes.json
        config_path = output_dir / "remotion_scenes.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            assets = config.get("scenes", [])
        else:
            print("❌ --skip-assets but no remotion_scenes.json found")
            sys.exit(1)

    # Save remotion config
    config = {
        "fps": args.fps,
        "width": 1920,
        "height": 1080,
        "scenes": [
            {
                "scene_id": a.get("scene_id", i),
                "imagePath": f"scenes/{Path(a.get('image_path', '')).name}",
                "audioPath": f"audio/{Path(a.get('audio_path', '')).name}",
                "durationInFrames": a.get("duration_frames", a.get("duration_seconds", 5) * args.fps),
            }
            for i, a in enumerate(assets)
        ],
    }
    config_path = output_dir / "remotion_scenes.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n📋 Remotion 配置: {config_path}")

    # Generate TSX
    if args.generate_tsx and script_data:
        print(f"\n🔧 生成 Remotion TSX...")
        tsx_path = generate_tsx(script_data, assets, str(output_dir), args.fps)
        print(f"   TSX: {tsx_path}")

    print(f"\n✅ 完成！")
    print(f"   图片: {scenes_dir}")
    print(f"   音频: {audio_dir}")
    print(f"\n🎬 渲染命令:")
    print(f"   cd /tmp/minimax-video && bash ~/.hermes/skills/minimax-video-creator/scripts/render_gsap_remotion.sh /tmp/minimax-video MyVideo out/video.mp4 1920 1080 30 h264")


if __name__ == "__main__":
    main()
