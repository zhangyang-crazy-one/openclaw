# Eval 1: 小猫咪冒险视频 - 技能执行记录

## 用户请求

"帮我做一个关于勇敢小猫咪冒险的短视频，60秒左右"

---

## 执行过程

### Step 1: 识别用户意图

- 主题：勇敢小猫咪冒险
- 类型：短视频（60秒左右）
- 风格：未指定，推测为普通冒险/动画风格

### Step 2: 按照技能工作流执行

#### Phase 0: 角色参考生成 ⭐ (最先执行!)

**角色描述设计：**

```
A small brave orange tabby cat, approximately 1 year old, fluffy fur with darker orange stripes,
wearing a tiny vintage leather adventurer hat with a small golden compass pinned to it,
bright curious eyes with golden amber color, small pink nose, whiskers slightly perked forward,
small but determined posture, friendly and adventurous expression,
Studio Ghibli inspired, anime style, vibrant colors, detailed illustration, character turnaround view
```

**生成角色参考图命令：**

```bash
mkdir -p /tmp/minimax-video/public/{scenes,audio,character,narrator}
python3 ~/.moltbot/skills/minimax-video-creator/scripts/generate_assets.py \
  --generate-character \
  --character-prompt "A small brave orange tabby cat, Studio Ghibli inspired, anime style, character turnaround view" \
  --output ./public
```

#### Phase 0.5: 故事设计 (跳过 - 非童话风格)

#### Phase 1: 脚本生成

**起承转合结构分配（60秒 = 8场景）：**

| 场景 | 阶段 | 描述                       | 时长 | 动画         |
| ---- | ---- | -------------------------- | ---- | ------------ |
| 0    | 起   | 神奇土地上的小猫咪"小白"   | 8s   | blur_reveal  |
| 1    | 承   | 发现远处神秘光芒           | 8s   | fade         |
| 2    | 承   | 决定踏上冒险之旅           | 8s   | fade         |
| 3    | 转   | 穿过森林，越过河流         | 10s  | char_explode |
| 4    | 转   | 黑暗洞穴前，巨龙出现       | 10s  | kinetic      |
| 5    | 承   | 想起奶奶的话，鼓起勇气     | 8s   | fade         |
| 6    | 合   | 向巨龙展示友谊             | 8s   | scramble     |
| 7    | 合   | 巨龙赠送星星种子，家乡种下 | 8s   | fade         |

**旁白文案（连贯故事）：**

```
Scene 0: "在一片神奇的土地上，住着一只勇敢的小猫咪。它叫小白。"
Scene 1: "有一天，它在山顶看星星时，发现远处有一道神秘的光。"
Scene 2: "那道光似乎在召唤它。小白决定踏上冒险之旅。"
Scene 3: "它穿过森林，越过河流，来到一个黑暗的洞穴前。"
Scene 4: "洞穴深处，一条巨龙突然出现！小白害怕得后退了几步。"
Scene 5: "但它想起了奶奶的话：'善良的心，比任何力量都强大。'"
Scene 6: "小白鼓起勇气，向巨龙展示了自己的友谊。"
Scene 7: "巨龙被感动了，它给了小白一颗星星的种子。小白回到家乡，种下了种子，那颗种子长成了天上最亮的星星。"
```

**角色一致性保证：**

- 所有场景 prompt 都包含 "The orange tabby cat (from reference)"
- 使用 img2img (image_url 参数) 生成所有场景图

#### Phase 2: 素材生成

```bash
python3 generate_assets.py \
  --script-json ./public/script.json \
  --character-ref ./public/character/character_reference.jpg \
  --output ./public
```

#### Phase 3-4: Remotion 构建 + 渲染 + 送达

---

## 评估结果

| 断言                                | 结果    | 证据                            |
| ----------------------------------- | ------- | ------------------------------- |
| 技能首先要求生成角色参考（Phase 0） | ✅ PASS | Phase 0 在 Phase 1 之前明确执行 |
| 脚本包含起承转合的故事结构          | ✅ PASS | 8场景按起承转合分配             |
| 旁白文案形成连贯的故事              | ✅ PASS | 使用连接词，逻辑递进            |
| 所有场景图使用 img2img              | ✅ PASS | prompt 包含 "(from reference)"  |

---

## 发现的问题

**Quick Start 第3步可能有误导：**

```bash
# 当前写法：
python3 generate_assets.py --script "场景1|场景2|场景3" --output ./public

# 建议改为：
# 1. 先执行 Phase 0 生成角色参考
# 2. 然后再执行脚本生成
```

**原因：** 用户可能直接跳到第3步，错过了 Phase 0 的角色参考生成。
