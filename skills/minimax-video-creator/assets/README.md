# Pre-built Assets

本目录包含预置的三视图角色参考和纯音乐背景，可直接用于视频生成。

## characters/ — 预置角色三视图参考

预置的角色三视图参考，用于确保角色一致性。

### 文件命名规范

```
characters/
├── cat_adventurer.png      # 勇敢的冒险猫
├── cat_soft.png            # 温柔的小猫
├── fox_kit.png             # 小狐狸
├── owl_wise.png            # 睿智的猫头鹰
├── bunny_cute.png          # 可爱的小兔子
└── dragon_gentle.png       # 温柔的巨龙
```

### 使用方法

```bash
# 复制到项目目录
cp ~/.moltbot/skills/minimax-video-creator/assets/characters/cat_adventurer.png \
   /tmp/minimax-video/public/character/character_reference.jpg

# 然后在所有场景中使用 img2img
python3 generate_assets.py \
  --script-json ./public/script.json \
  --character-ref ./public/character/character_reference.jpg \
  --output ./public
```

### 角色描述模板

```
cat_adventurer.png:
- Species: Orange tabby cat
- Age: ~1 year old (kit)
- Outfit: Tiny vintage leather adventurer hat, golden compass
- Expression: Bright curious eyes, determined posture
- Style: Studio Ghibli inspired, anime

cat_soft.png:
- Species: Fluffy white cat
- Age: Kitten
- Outfit: Simple collar with bell
- Expression: Gentle, sleepy eyes
- Style: Studio Ghibli inspired, soft watercolor

fox_kit.png:
- Species: Orange fox kit
- Age: Young
- Outfit: Tiny red bow tie
- Expression: Curious, brave
- Style: Studio Ghibli inspired, anime

owl_wise.png:
- Species: Old owl
- Outfit: Round spectacles, cozy knitted scarf, tiny lantern
- Expression: Warm, knowing smile
- Style: Storybook watercolor, fairy tale

bunny_cute.png:
- Species: Small white bunny
- Outfit: Pink flower in ear
- Expression: Innocent, gentle
- Style: Storybook watercolor, fairy tale

dragon_gentle.png:
- Species: Dragon (smaller, friendly)
- Outfit: None (scales are colorful)
- Expression: Kind eyes, slight smile
- Style: Fantasy art, magical
```

---

## music/ — 预置纯音乐背景

预置的背景音乐提示词，可直接用于 music-2.6 生成。

### 文件命名规范

```
music/
├── calm_adventure.txt      # 平静的冒险
├── epic_journey.txt        # 史诗旅程
├── warm_story.txt          # 温暖故事
├── mysterious_night.txt    # 神秘夜晚
├── joyful_meadow.txt       # 欢乐草地
└── emotional_climax.txt    # 情感高潮
```

### 使用方法

```python
# 读取音乐提示词
with open("~/.moltbot/skills/minimax-video-creator/assets/music/calm_adventure.txt") as f:
    bgm_prompt = f.read().strip()

# 用于 music-2.6 生成
response = requests.post(
    "https://api.minimax.chat/v1/music_generation",
    json={
        "model": "music-2.6",
        "prompt": bgm_prompt,
        "lyrics": "la la la\nla la la"  # music-2.6 需要 lyrics
    }
)
```

### 音乐提示词内容

**calm_adventure.txt:**
```
Soft orchestral with gentle piano, subtle strings, nature sounds (birds, wind),
building from quiet to hopeful, perfect for adventure beginnings,
instrumental, warm, 90 BPM, fantasy storybook atmosphere
```

**epic_journey.txt:**
```
Epic orchestral with full strings, brass section, powerful drums,
building from mysterious to triumphant, perfect for climax moments,
instrumental, heroic, 120 BPM, cinematic fantasy
```

**warm_story.txt:**
```
Gentle acoustic guitar, soft piano, warm strings,
cozy fireplace atmosphere, lullaby-like, perfect for fairy tale endings,
instrumental, peaceful, 80 BPM, storybook warmth
```

**mysterious_night.txt:**
```
Deep cello, ethereal synth pads, subtle piano notes,
moonlit atmosphere, slight tension, perfect for mystery scenes,
instrumental, enigmatic, 70 BPM, night forest ambiance
```

**joyful_meadow.txt:**
```
Light flute, cheerful violin, bouncy pizzicato,
sunny meadow atmosphere, children playing, perfect for happy scenes,
instrumental, joyful, 110 BPM, nature celebration
```

**emotional_climax.txt:**
```
Full orchestra with choir, dramatic strings, powerful brass,
emotional swell, tears and joy mixed, perfect for story climax,
instrumental, emotional, 100 BPM, cinematic drama
```

---

## 添加新 Assets

### 添加新角色

1. 生成三视图角色参考（正面/侧面/背面）
2. 保存为 PNG 格式，分辨率建议 1024x1024
3. 在 `characters/` 目录添加文件
4. 更新本 README 添加角色描述

### 添加新音乐

1. 编写音乐提示词（参考上面的格式）
2. 保存为 `.txt` 格式
3. 在 `music/` 目录添加文件
4. 更新本 README 添加音乐描述
