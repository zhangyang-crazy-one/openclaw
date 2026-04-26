# GSAP ScrambleText — CodePen XWzRraJ

> **Source:** https://codepen.io/GreenSock/pen/XWzRraJ
> **Author:** akapowl / GreenSock Team
> **Effect:** Character-by-character reveal from random chars to final text
> **Status:** Cloudflare-blocked; source reconstructed from prior session extraction

## HTML

```html
<!-- 5 sequential text spans, each is a ScrambleText target -->
<span id="scramble-text-1">文字内容1</span>
<span id="scramble-text-2">文字内容2</span>
<span id="scramble-text-3">文字内容3</span>
<span id="scramble-text-4">文字内容4</span>
<span id="scramble-text-5">文字内容5</span>
<img id="scramble-cursor" src="cursor.svg" />
```

## CSS

```css
@import url("https://fonts.googleapis.com/css2?family=Space+Mono&display=swap");
@font-face {
  font-family: "Mori";
  font-style: normal;
  font-weight: 400;
  src: url("PPMori-Regular.woff2") format("woff2");
}

body {
  background-color: #0e100f;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.text-wrapper {
  max-width: 40ch;
  text-align: center;
  margin: 0 auto;
}

#scramble-text-1,
#scramble-text-2,
#scramble-text-3,
#scramble-text-4,
#scramble-text-5 {
  display: block;
  font-family: "Space Mono", "Courier New", monospace;
  font-size: clamp(2rem, 5vw, 4rem);
  color: #fffce1;
  text-shadow: 0 0 20px rgba(255, 200, 100, 0.6);
  letter-spacing: 0.02em;
  line-height: 1.4;
  margin: 0.3em 0;
}
```

## JavaScript (GSAP Timeline)

```javascript
// 5 sequential .to() calls on individual span targets
// Each span gets its own scrambleText animation with staggered delays

const targets = [
  "#scramble-text-1",
  "#scramble-text-2",
  "#scramble-text-3",
  "#scramble-text-4",
  "#scramble-text-5",
];

const texts = [
  "First line of text",
  "Second line appears next",
  "Third line of the demo",
  "Fourth line reveals",
  "Fifth line completes it",
];

gsap
  .timeline({ repeat: -1, repeatDelay: 1 })
  .to(targets[0], {
    duration: 1.5,
    scrambleText: {
      text: texts[0],
      chars: "lowerCase", // 'abcdefghijklmnopqrstuvwxyz '
      speed: 0.3,
    },
    ease: "none",
  })
  .to(
    targets[1],
    {
      duration: 1.5,
      scrambleText: {
        text: texts[1],
        chars: "upperCase", // 'ABCDEFGHIJKLMNOPQRSTUVWXYZ '
        speed: 0.3,
      },
      ease: "none",
    },
    "-=1.0",
  ) // overlap with previous by 1s
  .to(
    targets[2],
    {
      duration: 1.5,
      scrambleText: {
        text: texts[2],
        chars: "0123456789",
        speed: 0.4,
      },
      ease: "none",
    },
    "-=1.0",
  )
  .to(
    targets[3],
    {
      duration: 1.5,
      scrambleText: {
        text: texts[3],
        chars: "XO",
        speed: 0.4,
      },
      ease: "none",
    },
    "-=1.0",
  )
  .to(
    targets[4],
    {
      duration: 1.5,
      scrambleText: {
        text: texts[4],
        chars: "punctuation", // '!@#$%&*-_+=?:;,./'
        speed: 0.3,
      },
      ease: "none",
    },
    "-=1.0",
  );
```

## GSAP ScrambleText Chars Reference

| chars option    | Character set                              |
| --------------- | ------------------------------------------ |
| `"lowerCase"`   | `abcdefghijklmnopqrstuvwxyz ` (26 + space) |
| `"upperCase"`   | `ABCDEFGHIJKLMNOPQRSTUVWXYZ `              |
| `"numbers"`     | `0123456789`                               |
| `"XO"`          | `XO` only                                  |
| `"punctuation"` | `!@#$%&*-_+=?:;,./`                        |
| Custom string   | Any characters provided                    |

## How ScrambleText Works (Technical)

GSAP's ScrambleTextPlugin internally:

1. Creates a character pool from `chars` option
2. Each frame/interval: replaces each character with a random char from pool
3. Gradually converges toward the final character as the tween progresses
4. `speed` option controls how fast characters "settle" (higher = faster settle)
5. Uses `text` property to interpolate from scrambled → final text

## Remotion Usage Note

**GSAP cannot run directly in Remotion's rendering context** because:

- Remotion renders frames via Puppeteer in a headless browser, but without DOM events
- GSAP timelines rely on `requestAnimationFrame` which behaves differently in Puppeteer
- The `scrambleText` plugin specifically needs DOM text nodes to animate

**Current approach:** Pure React/Remotion implementation using `useCurrentFrame()` to drive per-frame deterministic randomization, which correctly simulates the scramble effect frame-by-frame.

**Alternative approaches to explore:**

1. `@gsap/react` + `useGSAP` hook in Remotion (may work with Framer Motion integration)
2. Pre-render GSAP animations as video in browser, then composite in Remotion
3. Use `@remotion/three` with GSAP for 3D text animations
