# Character Consistency Pipeline

## Why Character Consistency Matters

**Critical problem:** Without character reference, each scene generates a different-looking character. Example:

- Scene 0: Orange cat with small hat, standing on hill
- Scene 1: Gray cat walking through forest (different breed!)
- Scene 3: White cat facing dragon (different color!)

**Solution:** Generate character reference first, then use img2img (reference image) for all subsequent scene images.

## Character Reference Generation

### Step 1: Create Character Prompt

Based on the script, write a detailed character description:

```
A small brave orange tabby cat, approximately 1 year old, fluffy fur with darker orange stripes,
wearing a tiny vintage leather adventurer hat with a small golden compass pinned to it,
bright curious eyes with golden amber color, small pink nose, whiskers slightly perked forward,
small but determined posture, friendly and adventurous expression,
Studio Ghibli inspired, anime style, vibrant colors, detailed illustration, character turnaround view
```

### Step 2: Generate 3-View Reference Image (front/side/back)

Use MiniMax image-01 with the detailed character prompt:

```python
# Generate 3-view character sheet
response = requests.post(
    "https://api.minimax.chat/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "Character turnaround reference sheet: front view, side view, back view of a small brave orange tabby cat wearing a tiny adventurer hat, clean white background, anime style, Studio Ghibli inspired, detailed illustration, vibrant colors, showing all angles clearly",
        "aspect_ratio": "3:2"
    }
)
image_url = response.json()["data"]["image_urls"][0]
# Download and save as: public/character/character_reference.jpg
```

### Step 3: Use as Reference for All Scene Images

For EVERY subsequent scene image generation, include the character reference:

```python
# For EACH scene image, use img2img with reference
response = requests.post(
    "https://api.minimax.chat/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "The orange tabby cat (from reference) standing on a grassy hilltop at sunset, wearing adventurer hat, vast fantasy landscape with floating islands in the distance, magical golden sky with stars, Studio Ghibli inspired, anime style",
        "aspect_ratio": "16:9",
        "image_url": "https://example.com/character_reference.jpg"  # Reference!
    }
)
```

## Character Consistency Rules

1. **ALWAYS generate character reference BEFORE any scene images**
2. **Use img2img (image_url parameter) for ALL scene images**
3. **Character description must include:** species, color, clothing, accessories, expression, size/age
4. **Scene prompt format:** `[Character from reference] + [Action/Pose] + [Setting] + [Style keywords]`
5. **Do NOT change character appearance between scenes** — if scene requires different outfit, update character prompt and regenerate reference

## Fairy Tale Character Consistency

For fairy tale videos with narrator overlay, TWO characters need consistency:

### Narrator Character

- Generated once as avatar image
- Used in `FairyTaleNarrator` component
- Design: illustrated style, soft lines, warm presence

### Protagonist Character (if different from narrator)

- Generated as 3-view reference sheet
- Used via img2img for ALL scene images featuring the protagonist
- Must appear consistent across all scenes

### Example: Cat Adventure Fairy Tale

```
Narrator: "Wise old owl with round spectacles, cozy scarf, tiny lantern"
Protagonist: "Small orange tabby cat, brave, wearing adventurer hat"
```

Both character references must be generated BEFORE scene images.

## Workflow Integration

```python
# In generate_assets.py, before generating scene images:

def generate_character_reference(character_prompt, output_dir):
    """Generate and save character reference image (3-views)."""
    # ... generate image ...
    save_path = f"{output_dir}/character/character_reference.jpg"
    return save_path

def generate_scene_with_character_ref(scene_prompt, character_ref_path):
    """Generate scene image using character reference (img2img)."""
    # ... generate image with reference ...
    pass

# Script generation phase:
# 1. Generate character reference FIRST
char_ref = generate_character_reference(script["character"], output_dir)

# 2. Generate scene images WITH character reference
for scene in script["scenes"]:
    scene_img = generate_scene_with_character_ref(
        scene["image_prompt"],
        char_ref
    )
```
