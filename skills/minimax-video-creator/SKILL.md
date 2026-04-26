---
name: minimax-video-creator
description: "End-to-end AI video production pipeline: Script writing → Character Reference → Storyboard → MiniMax (image-01 + speech-2.8-hd + music-2.6) → GSAP-powered Remotion composition → MP4. Use when user asks to create a video, make a short film, generate a promotional clip, or mentions 视频制作/做视频/生成视频. For fairy tale / storybook style videos, ALSO use the narrator character workflow (Phase 0.5 + Step 6.5) with consistent characters across all scenes. Includes complete script generation, character consistency (img2img), GSAP kinetic typography, and WeChat delivery."
metadata:
  tags:
    [
      video,
      minimax,
      remotion,
      gsap,
      image-generation,
      tts,
      text-to-video,
      kinetic-typography,
      scramble-text,
      script-generation,
      storyboard,
      fairy-tale,
      narrator-overlay,
      character-consistency,
    ]
  created: 2026-04-20
  updated: 2026-04-21
  updated_by: character-consistency-and-refactoring
---

# MiniMax Video Creator v4 — 完整视频制作工作流

**Pipeline:** Idea → Script → **Character Reference** → Scene Images → Audio → Remotion Composition → MP4

> **核心原则：角色一致性是一切的前提。** 每个视频项目必须先生成角色参考图，后续所有场景图都必须使用 img2img 基于参考图生成。

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Phase 0: Character Reference Generation](#2-phase-0-character-reference-generation) ⭐
3. [Phase 0.5: Fairy Tale Story Arc Design](#3-phase-05-fairy-tale-story-arc-design)
4. [Phase 1: Script Generation](#4-phase-1-script-generation)
5. [Phase 2: Asset Generation](#5-phase-2-asset-generation)
6. [Phase 3: Remotion Composition](#6-phase-3-remotion-composition)
   - [6.5 Fairy Tale Narrator Overlay](#65-fairy-tale-narrator-overlay)
7. [Phase 4: Rendering & Delivery](#7-phase-4-rendering--delivery)
8. [Common Issues](#8-common-issues)

---

## 1. Quick Start

> ⚠️ **重要：角色参考（Step 2）必须先做！** 跳过此步骤会导致每场景角色不一致。

```bash
# 1. 创建项目目录
mkdir -p /tmp/minimax-video/public/{scenes,audio,character,narrator}

# 2. ⭐ 生成角色参考（必须先做！所有场景图都将使用这个参考）
python3 ~/.moltbot/skills/minimax-video-creator/scripts/generate_assets.py \
  --generate-character \
  --character-prompt "你的角色描述，英文，越详细越好" \
  --output ./public
# 输出：public/character/character_reference.jpg

# 3. 生成完整脚本（编辑 script.json）
python3 generate_assets.py --script "场景1|场景2|场景3" --output ./public

# 4. ⭐ 生成所有素材（图片+语音）- 使用角色参考确保一致性
python3 generate_assets.py \
  --script-json ./public/script.json \
  --character-ref ./public/character/character_reference.jpg \
  --output ./public

# 5. 构建 Remotion 项目
python3 generate_assets.py --script-json ./public/script.json --generate-tsx --output ./public

# 6. 渲染
bash ~/.moltbot/skills/minimax-video-creator/scripts/render_gsap_remotion.sh \
  /tmp/minimax-video MyVideo out/video.mp4 1920 1080 30 h264
```

> **为什么 Step 2 必须先做？** 没有角色参考，AI 会在每个场景生成不同的角色外观（颜色、品种、服装都可能变化）。

---

## 2. Phase 0: Character Reference Generation ⭐

**这是最关键的步骤！必须在生成任何场景图之前完成！**

### 为什么重要？

没有角色参考 → 每个场景生成不同的角色：

- 场景0：橙色小猫，戴小帽子，站在山顶
- 场景1：灰色猫在森林里走（品种变了！）
- 场景3：白猫面对巨龙（颜色变了！）

**解决方案：先生成角色参考图，后续所有场景图都使用 img2img 基于参考图生成。**

### Step 0.1: 编写角色描述

```
A small brave orange tabby cat, approximately 1 year old, fluffy fur with darker orange stripes,
wearing a tiny vintage leather adventurer hat with a small golden compass pinned to it,
bright curious eyes with golden amber color, small pink nose, whiskers slightly perked forward,
small but determined posture, friendly and adventurous expression,
Studio Ghibli inspired, anime style, vibrant colors, detailed illustration, character turnaround view
```

### Step 0.2: 生成三视图角色参考

**方案 A：使用预置角色资产（推荐）**

技能提供了预置的三视图角色参考，直接复制使用：

```bash
# 预置角色列表：cat_adventurer, cat_soft, fox_kit, owl_wise, bunny_cute, dragon_gentle
cp ~/.moltbot/skills/minimax-video-creator/assets/characters/cat_adventurer.png \
   /tmp/minimax-video/public/character/character_reference.jpg
```

**预置角色说明：** `assets/README.md`

**方案 B：自定义生成角色参考**

```python
response = requests.post(
    "https://api.minimax.chat/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "Character turnaround reference sheet: front view, side view, back view of a small brave orange tabby cat wearing a tiny adventurer hat, clean white background, anime style, Studio Ghibli inspired, detailed illustration, vibrant colors, showing all angles clearly",
        "aspect_ratio": "3:2"
    }
)
# 保存为: public/character/character_reference.jpg
```

### Step 0.3: 后续所有场景图都必须使用 img2img

```python
response = requests.post(
    "https://api.minimax.chat/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "The orange tabby cat (from reference) standing on a grassy hilltop at sunset...",
        "aspect_ratio": "16:9",
        "image_url": "https://example.com/character_reference.jpg"  # 关键！
    }
)
```

### 角色一致性规则

1. **必须先生成角色参考，再生成任何场景图**
2. **所有场景图必须使用 img2img（image_url 参数）**
3. **角色描述必须包含：** 物种、颜色、服装、配饰、表情、体型/年龄
4. **场景提示词格式：** `[参考图中的角色] + [动作/姿态] + [场景] + [风格关键词]`
5. **不要在场景间改变角色外观** — 如需不同服装，更新角色提示词并重新生成参考图

**详细文档：** `references/character-consistency.md`

---

## 3. Phase 0.5: Fairy Tale Story Arc Design

**童话/故事书风格视频必须先完成故事设计，再生成任何素材。**

### 童话故事模板

```markdown
## Story Title

[TITLE — e.g. "The Fox and the Little Lantern"]

## Narrator Character ⭐ 必须生成

- Name: [NARRATOR_NAME — e.g. "Mr. Owlington"]
- Visual Description: [KEY TRAITS — e.g. "Wise old owl with round spectacles, cozy scarf, tiny lantern"]
- Personality: [2-3 keywords — e.g. "Warm, curious, gentle"]
- Role: Guides the audience through the story; appears in each scene as overlay

## Protagonist Character ⭐ 必须生成角色参考

- Name: [NAME]
- Visual Description: [PHYSICAL DESCRIPTION — for AI image generation]
- Personality: [2-3 personality keywords]

## World/Setting

[DESCRIPTION — e.g. "Enchanted forest with bioluminescent mushrooms, twilight sky"]

## Narrative Arc (3-Act Fairy Tale Structure)

### Act 1 — Once Upon a Time [0-30%]

INTRODUCE THE WORLD AND CHARACTERS

### Act 2 — The Journey [30-70%]

CHALLENGE OR MISHAP OCCURS
PROTAGONIST LEARNS SOMETHING ALONG THE WAY

### Act 3 — And They Lived Happily Ever After [70-100%]

RESOLUTION — obstacle overcome or lesson learned

## Tone & Mood

[E.g. "Warm and cozy, like a bedtime story read by firelight."]

## Target Duration

[45-90s recommended for complete fairy tale arc]
```

### 童话视频角色一致性

童话视频需要保证**两个**角色的一致性：

1. **旁白角色** — 生成一次作为头像，用于 `FairyTaleNarrator` 组件
2. **主角角色** — 必须生成三视图参考表，用于所有包含主角的场景图

**示例：猫冒险童话**

```
旁白: "睿智的老猫头鹰，圆眼镜，舒适围巾，小灯笼"
主角: "勇敢的小橙猫，冒险家帽子"
```

**必须先生成两个角色参考，再生成场景图！**

### 生成旁白角色

```bash
# 生成旁白头像
python3 ~/.moltbot/skills/minimax-video-creator/scripts/generate_assets.py \
  --generate-character \
  --character-prompt "Wise illustrated owl, round spectacles, cozy knitted scarf, holding a tiny glowing lantern, storybook watercolor style, warm expression, fairy tale aesthetic" \
  --output ./public/narrator
```

**详细文档：** `references/story-arc.md`

---

## 4. Phase 1: Script Generation

### 脚本结构

```typescript
VideoScript = {
  title: string,          // 视频标题
  theme: string,          // 主题关键词
  style: string,          // 视觉风格: cinematic | anime | documentary | scifi | fantasy | minimalist
  total_duration: number, // 总时长（秒），建议 30-120 秒
  scenes: Scene[],        // 场景列表，通常 4-8 个场景
  bgm_prompt: string,     // 背景音乐描述（可使用预置：assets/music/*.txt）
  character: string,      // ⭐ 角色描述（用于生成参考图）
  narrator?: string,       // ⭐ 旁白角色描述（童话风格）
}

Scene = {
  id: number,
  type: "narration" | "title" | "transition" | "climax" | "ending",
  image_prompt: string,    // 英文，给 image-01 用
  narration: string,       // 中文旁白
  caption: string,         // 屏幕字幕
  duration_seconds: number, // 3-10 秒
  animation: string,       // 动画效果: fade | slide | zoom | kinetic | blur_reveal | char_explode | scramble
  transition: string,      // 与下一场景的过渡: fade | crossfade | wipe | none
  camera_move: string,     // 镜头运动: pan_left | pan_right | zoom_in | zoom_out | static | tilt_up
  mood: string,            // 情绪标签: calm | dramatic | mysterious | joyful | tense | epic
}
```

### 旁白规则（故事连贯性）

**关键：旁白文本必须形成连贯的故事，而不仅仅是场景描述。**

- 使用场景间的连接词："于是", "但是", "没想到", "最后"
- 每个场景的旁白应该从前一个场景自然过渡
- 保持故事弧线（起承转合）
- 总计：60秒视频约 200-300 中文字符（约3-4字/秒）

**示例 — 猫冒险故事（正确的故事流程）：**

```
Scene 0: "在一片神奇的土地上，住着一只勇敢的小猫咪。它叫小白。"
Scene 1: "有一天，它在山顶看星星时，发现远处有一道神秘的光。"
Scene 2: "那道光似乎在召唤它。小白决定踏上冒险之旅。"
Scene 3: "它穿过森林，越过河流，来到一个黑暗的洞穴前。"
Scene 4: "洞穴深处，一条巨龙突然出现！小白害怕得后退了几步。"
Scene 5: "但它想起了奶奶的话：'善良的心，比任何力量都强大。'"
Scene 6: "小白鼓起勇气，向巨龙展示了自己的友谊。"
Scene 7: "巨龙被感动了，它给了小白一颗星星的种子。"
Scene 8: "小白回到家乡，种下了种子，那颗种子长成了天上最亮的星星。"
```

### 故事结构（起承转合）

| Phase            | Chinese | Purpose                             | % of Duration |
| ---------------- | ------- | ----------------------------------- | ------------- |
| 起 (Beginning)   | 引入    | Hook the viewer, set the scene      | 15-20%        |
| 承 (Development) | 铺陈    | Build the story, add detail         | 30-40%        |
| 转 (Turn)        | 转折    | Create contrast, surprise, conflict | 20-25%        |
| 合 (Conclusion)  | 总结    | Resolve, call to action, end        | 15-20%        |

### 图片提示词公式

```
[Subject] + [Setting/Background] + [Lighting] + [Mood/Atmosphere] + [Style keywords]
```

**重要：图片提示词必须用英文！**

| Style       | Keywords                                                                     |
| ----------- | ---------------------------------------------------------------------------- |
| cinematic   | `cinematic, dramatic lighting, film grain, 4K, movie still`                  |
| anime       | `anime style, Studio Ghibli inspired, vibrant colors, detailed illustration` |
| documentary | `documentary photography, natural lighting, authentic, National Geographic`  |
| scifi       | `sci-fi, futuristic, neon glow, cyberpunk, holographic, 4K render`           |
| fantasy     | `fantasy art, ethereal, magical, mystical atmosphere, detailed painting`     |
| minimalist  | `minimalist, clean composition, soft light, simple geometry, modern design`  |

---

## 5. Phase 2: Asset Generation

### 命令

```bash
cd /tmp/minimax-video

# 重要：必须传入角色参考图路径
python3 ~/.moltbot/skills/minimax-video-creator/scripts/generate_assets.py \
  --script-json ./public/script.json \
  --character-ref ./public/character/character_reference.jpg \
  --output ./public
```

这会生成：

- `public/scenes/scene_0.jpg` 到 `scene_N.jpg`（使用 img2img 基于角色参考）
- `public/audio/speech_XXXXX.mp3` 每个旁白
- `public/audio/music_*.mp3` 背景音乐（可选）

### 背景音乐资产

**使用预置音乐（推荐）：**

```
# 预置音乐列表：calm_adventure, epic_journey, warm_story, mysterious_night, joyful_meadow, emotional_climax
cat ~/.moltbot/skills/minimax-video-creator/assets/music/calm_adventure.txt
```

**预置音乐说明：** `assets/README.md`

**音乐与故事情绪匹配：**

| 场景情绪  | 推荐音乐         | 说明                 |
| --------- | ---------------- | -------------------- |
| 开场/引入 | calm_adventure   | 平静、有希望         |
| 冒险/旅程 | epic_journey     | 史诗感、逐渐推向高潮 |
| 温暖/结局 | warm_story       | 温馨、故事书感觉     |
| 神秘/夜晚 | mysterious_night | 深沉、神秘           |
| 欢乐/草地 | joyful_meadow    | 轻快、跳跃           |
| 高潮/转折 | emotional_climax | 情感充沛、戏剧性     |

### MiniMax API 详情

**参考文档：** `references/minimax-api.md`

| 能力     | 端点                        | 模型            | 状态    |
| -------- | --------------------------- | --------------- | ------- |
| 图片生成 | `POST /v1/image_generation` | `image-01`      | Working |
| 语音合成 | `POST /v1/t2a_v2`           | `speech-2.8-hd` | Working |
| 背景音乐 | `POST /v1/music_generation` | `music-2.6`     | Async   |

---

## 6. Phase 3: Remotion Composition

### 关键：图片加载 — 使用 CSS backgroundImage 而不是 `<Img>` 组件

**Remotion `<Img>` 组件在 `<Sequence>` 内部不能正常工作。** 会渲染黑帧。

**错误（黑屏）：**

```tsx
// ❌ 这在 <Sequence> 内会崩溃
<Sequence from={0} durationInFrames={300}>
  <AbsoluteFill>
    <Img src={staticFile("scenes/cat.jpg")} style={{ width: "100%", height: "100%" }} />
  </AbsoluteFill>
</Sequence>
```

**正确（可用）：**

```tsx
// ✅ CSS backgroundImage 在 <Sequence> 内完美工作
<Sequence from={0} durationInFrames={300}>
  <AbsoluteFill>
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: `url(${staticFile("scenes/cat.jpg")})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    />
  </AbsoluteFill>
</Sequence>
```

### GSAP 动画引擎

**参考文档：** `references/gsap-animations.md`

**关键规则：**

1. **不要** 使用 `useGSAP()` from `@gsap/react` — 使用 `useCurrentFrame()`
2. **不要** 创建没有 `paused: true` 的 GSAP 补间 — 不会与 Remotion 帧同步
3. **不要** 使用 `ScrollTrigger` — 视频没有滚动
4. **不要** 使用 CSS `transition` — Remotion 每帧独立渲染
5. **不要** 忘记 `Math.max(0, Math.min(1, progress))` clamp

### 场景组件架构

```
VideoComposition
├── BackgroundMusic (optional, loops)
├── Scene[0] ── Sequence
│   ├── Background Image (with camera movement)
│   ├── Text Animation (blur_reveal / char_explode / scramble / kinetic)
│   ├── Caption (bottom-center, fade in/out)
│   └── Audio (TTS narration)
├── Scene[1] ── Sequence
│   └── ...
└── FairyTaleNarrator ── (if narratorAvatar provided)
```

### 动画效果

| 效果           | 组件           | 最适合         |
| -------------- | -------------- | -------------- |
| 字符错落入场   | `TextReveal`   | 场景标题，开场 |
| 字符爆发飞入   | `CharsExplode` | 戏剧性入场     |
| 模糊转清晰     | `CharsBlur`    | 神秘揭示       |
| 动力学旋转网格 | `KineticGrid`  | 最大视觉冲击   |
| 字符乱码重组   | `ScrambleText` | 科技/黑客美学  |

**完整模板：** `references/animation-templates.md`

---

## 6.5 Fairy Tale Narrator Overlay

对于童话/故事书风格视频，添加**浮动旁白角色**叠加层。

### 旁白角色设计要求

- 与童话风格一致的插画风格（水彩、故事书艺术、柔和线条）
- 轻柔浮动动画（3-7px 垂直移动，5秒周期）
- 清晰的轮廓，在任何场景背景下都可见
- 温暖、亲切的存在，引导观众

### Remotion 旁白组件

```tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface NarratorProps {
  avatarUrl: string;
  narration: string;
  username?: string;
  wordTimings?: Array<{ word: string; start: number; end: number }>;
}

export const FairyTaleNarrator: React.FC<NarratorProps> = ({
  avatarUrl,
  narration,
  username = "Storyteller",
  wordTimings,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 浮动动画：5秒周期，7px范围
  const floatOffset = Math.sin((frame / fps) * ((2 * Math.PI) / 5)) * 7;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* 旁白角色 — 右下角，浮动 */}
      <div
        style={{
          position: "absolute",
          right: 280,
          bottom: 51 + floatOffset,
          height: 180,
          width: 200,
        }}
      >
        <img
          src={staticFile(avatarUrl)}
          style={{
            height: "100%",
            width: "100%",
            objectFit: "contain",
            filter: "drop-shadow(0px 0px 5px rgba(0,0,0,0.5))",
          }}
        />
      </div>

      {/* 旁白文本框 — 右下角 */}
      <div
        style={{
          position: "absolute",
          right: 250,
          bottom: 50,
          maxWidth: 750,
          maxHeight: 120,
          background: "rgba(0,0,0,0.6)",
          borderRadius: 30,
          padding: "1.5rem 2rem",
          backdropFilter: "blur(8px)",
        }}
      >
        {wordTimings ? (
          <WordByWordText fps={fps} frame={frame} timings={wordTimings} />
        ) : (
          <>
            Hello, I&apos;m <b>{username}</b>!
            <br />
            {narration}
          </>
        )}
      </div>
    </AbsoluteFill>
  );
};

const WordByWordText: React.FC<{
  fps: number;
  frame: number;
  timings: Array<{ word: string; start: number; end: number }>;
}> = ({ fps, frame, timings }) => {
  const currentTime = frame / fps;
  const activeIdx = timings.findIndex((t, i) => currentTime >= t.start && currentTime < t.end);

  return (
    <span>
      {timings.map((t, i) => (
        <span
          key={i}
          style={{
            opacity: i <= activeIdx ? 1 : 0.35,
            color: i === activeIdx ? "#ffd54f" : "white",
            transition: "opacity 0.08s ease, color 0.08s ease",
          }}
        >
          {t.word}{" "}
        </span>
      ))}
    </span>
  );
};
```

### 集成到 VideoComposition

```tsx
export const VideoComposition: React.FC<VideoProps> = ({
  scenes,
  musicPath,
  title,
  narratorAvatar,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* 背景音乐 */}
      {musicPath && <Audio src={staticFile(musicPath)} loop volume={0.3} />}

      {/* 场景 */}
      {safeScenes.map((scene, i) => (
        <Sequence key={i} from={sceneStartFrames[i]} durationInFrames={scene.durationInFrames}>
          <Scene {...scene} />
        </Sequence>
      ))}

      {/* 童话旁白叠加层 — 贯穿所有场景 */}
      {narratorAvatar && (
        <FairyTaleNarrator
          avatarUrl={narratorAvatar}
          narration={narrations.join(" ")}
          username="Mr. Owlington"
          wordTimings={wordTimings}
        />
      )}
    </AbsoluteFill>
  );
};
```

### 布局图示

```
┌─────────────────────────────────────────┐
│                                         │
│         视频场景（全宽）                │
│                                         │
│                           ┌──────────┐  │
│                           │  头像    │  │
│                           └──────────┘  │
│                           ┌──────────┐  │
│                           │ 旁白框   │  │
│                           └──────────┘  │
└─────────────────────────────────────────┘
```

- 视频场景：填充整个画面
- 旁白头像：固定右下（right: 280px, bottom: 51px）
- 旁白框：同行，头像左侧（right: 250px, bottom: 50px）
- 两个元素都有轻微浮动动画（7px范围，5秒周期）

---

## 7. Phase 4: Rendering & Delivery

### 渲染命令

```bash
bash ~/.moltbot/skills/minimax-video-creator/scripts/render_gsap_remotion.sh \
  <project_dir> <composition_id> [output_path] [width] [height] [fps] [codec]
```

Defaults: 1080x1080, 30fps, h264, output to `out/<id>.mp4`.

- 横屏视频（微信/YouTube）: `1920 1080`
- 竖屏视频（TikTok/Reels）: `1080 1920`

### 微信送达

```python
import asyncio, os, sys, json
sys.path.insert(0, '/home/liujerry/hermes-agent')
from dotenv import load_dotenv
load_dotenv('/home/liujerry/.hermes/.env')

from gateway.config import PlatformConfig
from tools.send_message_tool import _send_weixin

async def send_video(video_path, chat_id, message="视频已生成"):
    pconfig = PlatformConfig(
        enabled=True,
        token=os.getenv('WEIXIN_TOKEN'),
        extra={
            'account_id': os.getenv('WEIXIN_ACCOUNT_ID'),
            'base_url': os.getenv('WEIXIN_BASE_URL'),
            'cdn_base_url': os.getenv('WEIXIN_CDN_BASE_URL'),
        }
    )
    return await _send_weixin(
        pconfig=pconfig,
        chat_id=chat_id,
        message=message,
        media_files=[(video_path, 'video/mp4')],
    )

# Jerry's WeChat: o9cq803mUpxrwKgnNDyogPfpkSDY@im.wechat
result = asyncio.run(send_video(
    '/tmp/minimax-video/out/video.mp4',
    'o9cq803mUpxrwKgnNDyogPfpkSDY@im.wechat',
    '视频已完成'
))
```

### 必需的环境变量

均在 `~/.hermes/.env`:

- `MINIMAX_API_KEY` — MiniMax API key (125 chars)
- `WEIXIN_TOKEN` — WeChat bot token
- `WEIXIN_ACCOUNT_ID` — e.g. `d6297f02f9c6@im.bot`
- `WEIXIN_BASE_URL` — e.g. `https://ilinkai.weixin.qq.com`
- `WEIXIN_CDN_BASE_URL` — e.g. `https://novac2c.cdn.weixin.qq.com/c2c`

---

## 8. Common Issues

| Problem                               | Solution                                                            |
| ------------------------------------- | ------------------------------------------------------------------- |
| `Could not find composition with ID`  | 使用 `src/index.tsx` 而不是 `src/index.ts` 作为入口                 |
| `No target found for targetId`        | Puppeteer 清理警告 — 视频仍然渲染                                   |
| TTS 空音频                            | 使用 `speech-2.8-hd` 而不是 `music-2.6-tts`                         |
| 图片 URL 404                          | 立即下载 — URL 很快过期                                             |
| 渲染超时                              | 使用 720p 加速: `npx remotion render ... --width=1280 --height=720` |
| CORS 错误                             | 从 `public/` 通过 `staticFile()` 提供，不要用远程 URL               |
| `Cannot read properties of undefined` | 在 `.map()` 前添加 `const safeScenes = scenes ?? []`                |
| Chars misaligned                      | 内部字符 span: `display: "inline"`（不是 `inline-block`）           |
| 视频送达失败                          | 检查 `.env` 中的 WEIXIN_TOKEN + CDN_BASE_URL                        |
| 音乐生成超时                          | 默认 180s 轮询；长音乐增加超时                                      |

### 高优先级问题

| 问题                         | 解决方案                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| **场景旁白没有故事连贯性**   | **在场景间使用连接词；构建故事弧线（起承转合）；每个旁白必须与前一个相连**                                |
| **角色在每个场景看起来不同** | **先生成角色参考（三视图），然后对所有场景图使用 img2img（image_url）**                                   |
| **音乐不符合故事情绪**       | **匹配 bgm_prompt 到情感弧线：悲伤/神秘情绪的场景需要先有平静音乐，再构建到高潮**                         |
| **相机/过渡动画不工作**      | **确保 script.json 中的 animation/transition 字段与 SceneComposition.tsx 支持的值匹配**                   |
| **童话旁白不显示**           | **传递 narratorAvatar prop 给 VideoComposition；确保头像图片在 public/ 文件夹中并通过 staticFile() 引用** |
| **逐字字幕不同步**           | **确保 wordTimings 数组使用秒（不是帧），格式为 {word, start, end}；frame = fps \* time**                 |

---

## References

```
~/.moltbot/skills/minimax-video-creator/
├── references/
│   ├── animation-templates.md          ← 8 ready-to-use GSAP animation templates
│   ├── integration-patterns.md         ← 3 GSAP+Remotion integration patterns
│   ├── minimax-api.md                  ← MiniMax API 完整参考
│   ├── gsap-animations.md              ← GSAP 动画引擎详细文档
│   ├── character-consistency.md        ← 角色一致性完整指南
│   ├── story-arc.md                    ← 故事弧线和旁白设计
│   ├── gsap-animated-sections-codepen.md ← GSAP 滚动场景切换动画
│   └── gsap-scramble-text-codepen-XWzRraJ.md ← ScrambleText 原始代码
├── scripts/
│   ├── minimax_api.py                  ← MiniMax API wrapper (image, TTS, music)
│   ├── generate_assets.py              ← Batch asset generation + TSX generation
│   └── render_gsap_remotion.sh         ← One-command render script
├── templates/
│   └── SceneComposition.tsx            ← Full composition with GSAP animations
└── assets/                            ← ⭐ 预置资产
    ├── characters/                    ← 预置三视图角色参考
    │   ├── cat_adventurer.png
    │   ├── cat_soft.png
    │   ├── fox_kit.png
    │   ├── owl_wise.png
    │   ├── bunny_cute.png
    │   └── dragon_gentle.png
    └── music/                         ← 预置纯音乐背景
        ├── calm_adventure.txt
        ├── epic_journey.txt
        ├── warm_story.txt
        ├── mysterious_night.txt
        ├── joyful_meadow.txt
        └── emotional_climax.txt
```

---

## Key Do-Not-Do Rules

1. **DO NOT** use `useGSAP()` from `@gsap/react` in Remotion — use `useCurrentFrame()`
2. **DO NOT** create GSAP tweens without `paused: true` — they won't sync with Remotion frames
3. **DO NOT** use `ScrollTrigger` in video compositions — no scroll in video
4. **DO NOT** use CSS `transition` — Remotion renders each frame independently
5. **DO NOT** forget `Math.max(0, Math.min(1, progress))` clamp before passing to GSAP ease
6. **DO NOT** hardcode `~/.hermes` paths — use `get_hermes_home()` in Python
7. **DO NOT** use `inline-block` for character spans — use `display: "inline"` to preserve baseline
8. **DO NOT** generate image prompts in Chinese — English prompts produce better results with image-01
9. **DO NOT** write narration longer than 4 chars/second — TTS pacing will be off
10. **DO NOT** forget to download image URLs immediately — they expire within minutes
11. **DO NOT** use `<Img>` component for narrator avatar — use CSS `backgroundImage` or `<img>` with `staticFile()` inside scene sequences
12. **DO NOT** generate scene images before generating character reference — all scenes will have inconsistent characters
