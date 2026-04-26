# Animation Templates

Ready-to-use GSAP + Remotion composition templates. Copy and customize for the user's needs.

---

## 1. Text Reveal (Character Stagger)

Each character slides up with back easing, creating a cinematic text entrance.

```jsx
import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from "remotion";
import gsap from "gsap";

const COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"];

const TextReveal = ({
  text,
  frame,
  fps,
  y = 490,
  fontSize = 64,
  staggerFrames = 2,
  startFrame = 10,
}) => {
  const chars = text.split("");

  return (
    <div
      style={{
        position: "absolute",
        display: "flex",
        justifyContent: "center",
        width: "100%",
        top: y,
      }}
    >
      {chars.map((char, i) => {
        const charDelay = startFrame + i * staggerFrames;
        const localFrame = Math.max(0, frame - charDelay);
        const progress = Math.min(1, localFrame / (fps * 0.5));

        const yEase = gsap.parseEase("back.out(2)")(progress);
        const opacityEase = gsap.parseEase("power2.out")(progress);
        const rotEase = gsap.parseEase("elastic.out(1,0.6)")(progress);

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              color: COLORS[i % COLORS.length],
              fontSize,
              fontWeight: 900,
              fontFamily: "system-ui, sans-serif",
              opacity: opacityEase,
              transform: `translateY(${(1 - yEase) * 60}px) rotate(${(1 - rotEase) * 30}deg)`,
              textShadow: `0 0 20px ${COLORS[i % COLORS.length]}66`,
              letterSpacing: char === " " ? 16 : 2,
            }}
          >
            {char === " " ? "\u00A0" : char}
          </span>
        );
      })}
    </div>
  );
};

export default TextReveal;
```

---

## 2. Logo Reveal (Scale + Rotation + Fade)

Professional logo entrance with elastic bounce, glow pulse, and subtitle fade-in.

```jsx
import React, { useEffect, useRef, useState } from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from "remotion";
import gsap from "gsap";

const LogoReveal = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [s, setState] = useState({
    scale: 0,
    rotation: -45,
    opacity: 0,
    glowSize: 0,
    subtitleY: 30,
    subtitleOpacity: 0,
  });
  const tlRef = useRef(null);

  useEffect(() => {
    const proxy = {
      scale: 0,
      rotation: -45,
      opacity: 0,
      glowSize: 0,
      subtitleY: 30,
      subtitleOpacity: 0,
    };
    const tl = gsap.timeline({ paused: true });

    tl.to(
      proxy,
      { scale: 1.2, opacity: 1, rotation: 0, duration: 0.8, ease: "elastic.out(1,0.4)" },
      0,
    )
      .to(proxy, { glowSize: 100, duration: 0.6, ease: "power2.out" }, 0.2)
      .to(proxy, { scale: 1, duration: 0.4, ease: "back.out(2)" }, 0.8)
      .to(proxy, { subtitleY: 0, subtitleOpacity: 1, duration: 0.6, ease: "power3.out" }, 1.0);

    tlRef.current = { tl, proxy };
  }, []);

  useEffect(() => {
    if (tlRef.current) {
      const { tl, proxy } = tlRef.current;
      tl.time(frame / fps);
      setState({ ...proxy });
    }
  }, [frame, fps]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a1a",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
      }}
    >
      {/* Glow */}
      <div
        style={{
          position: "absolute",
          width: s.glowSize * 4,
          height: s.glowSize * 4,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(78,205,196,0.3) 0%, transparent 70%)",
          filter: "blur(30px)",
          opacity: s.opacity,
        }}
      />
      {/* Logo placeholder */}
      <div
        style={{
          width: 160,
          height: 160,
          borderRadius: 24,
          background: "linear-gradient(135deg, #4ECDC4, #44CF6C)",
          opacity: s.opacity,
          transform: `rotate(${s.rotation}deg) scale(${s.scale})`,
          boxShadow: "0 0 60px rgba(78,205,196,0.4)",
        }}
      />
      {/* Subtitle */}
      <div
        style={{
          marginTop: 40,
          color: "#ffffff",
          fontSize: 28,
          fontFamily: "system-ui, sans-serif",
          letterSpacing: 8,
          opacity: s.subtitleOpacity,
          transform: `translateY(${s.subtitleY}px)`,
        }}
      >
        YOUR BRAND
      </div>
    </AbsoluteFill>
  );
};

export default LogoReveal;
```

---

## 3. Progress Bar

Animated progress with elastic easing and percentage counter.

```jsx
import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from "remotion";
import gsap from "gsap";

const ProgressBar = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const progress = Math.min(1, frame / (durationInFrames * 0.8));
  const easedWidth = gsap.parseEase("power3.out")(progress) * 100;
  const percent = Math.round(easedWidth);

  // Pulse effect near completion
  const pulseFrame = Math.max(0, frame - durationInFrames * 0.7);
  const pulseProgress = Math.min(1, pulseFrame / (fps * 0.3));
  const pulseEase = gsap.parseEase("elastic.out(1,0.3)")(pulseProgress);
  const glowIntensity = easedWidth > 90 ? pulseEase * 20 : 5;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f0f23",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ width: "70%" }}>
        <div
          style={{
            width: "100%",
            height: 12,
            borderRadius: 6,
            backgroundColor: "#1a1a3e",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${easedWidth}%`,
              height: "100%",
              borderRadius: 6,
              background: "linear-gradient(90deg, #4ECDC4, #45B7D1, #96CEB4)",
              boxShadow: `0 0 ${glowIntensity}px rgba(78,205,196,0.6)`,
            }}
          />
        </div>
        <div
          style={{
            marginTop: 20,
            textAlign: "center",
            color: "#4ECDC4",
            fontSize: 48,
            fontFamily: "monospace",
            fontWeight: 700,
            textShadow: `0 0 ${glowIntensity}px rgba(78,205,196,0.4)`,
          }}
        >
          {percent}%
        </div>
      </div>
    </AbsoluteFill>
  );
};

export default ProgressBar;
```

---

## 4. Morphing Shapes

Shape transitions using GSAP easing with clip-path morphing.

```jsx
import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill, interpolate } from "remotion";
import gsap from "gsap";

const shapes = [
  "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
  "circle(50% at 50% 50%)",
  "polygon(50% 0%, 100% 100%, 0% 100%)",
  "polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)",
];

const colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFEAA7"];

const MorphingShapes = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const totalShapes = shapes.length;
  const framesPerShape = durationInFrames / totalShapes;

  const currentShapeIndex = Math.min(Math.floor(frame / framesPerShape), totalShapes - 1);
  const shapeProgress = (frame % framesPerShape) / framesPerShape;
  const ease = gsap.parseEase("power3.inOut");

  const isTransitioning = shapeProgress < 0.3;
  const scaleEase = gsap.parseEase("elastic.out(1,0.5)");
  const scale = isTransitioning ? 0.8 + scaleEase(shapeProgress / 0.3) * 0.2 : 1;

  const rotation = interpolate(frame, [0, durationInFrames], [0, 360], {
    extrapolateRight: "clamp",
    easing: gsap.parseEase("none"),
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a1a",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: 300,
          height: 300,
          clipPath: shapes[currentShapeIndex],
          backgroundColor: colors[currentShapeIndex],
          transform: `rotate(${rotation}deg) scale(${scale})`,
          boxShadow: `0 0 60px ${colors[currentShapeIndex]}44`,
        }}
      />
    </AbsoluteFill>
  );
};

export default MorphingShapes;
```

---

## 5. Floating Elements with Loop

Elements floating in a continuous sine-wave loop with GSAP entrance easing.

```jsx
import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from "remotion";
import gsap from "gsap";

const FloatingElements = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const elements = [
    { x: 200, y: 300, size: 60, color: "#FF6B6B", speed: 1.2, phase: 0 },
    { x: 500, y: 200, size: 40, color: "#4ECDC4", speed: 0.8, phase: 1.5 },
    { x: 800, y: 400, size: 50, color: "#45B7D1", speed: 1.0, phase: 3 },
    { x: 350, y: 600, size: 35, color: "#FFEAA7", speed: 1.4, phase: 0.8 },
    { x: 700, y: 500, size: 45, color: "#DDA0DD", speed: 0.9, phase: 2.2 },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f0f23" }}>
      {elements.map((el, i) => {
        const entranceEase = gsap.parseEase("elastic.out(1,0.4)")(
          Math.max(0, Math.min(1, (frame - i * 5) / (fps * 0.6))),
        );
        const floatY = Math.sin((frame / fps) * el.speed * Math.PI + el.phase) * 20;
        const floatX = Math.cos((frame / fps) * el.speed * Math.PI * 0.7 + el.phase) * 10;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: el.x + floatX,
              top: el.y + floatY,
              width: el.size,
              height: el.size,
              borderRadius: "50%",
              backgroundColor: el.color,
              opacity: entranceEase * 0.7,
              transform: `scale(${entranceEase})`,
              boxShadow: `0 0 ${el.size}px ${el.color}44`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export default FloatingElements;
```

---

## 6. Kinetic Grid Rotation (kinetic typography style)

Large text grid that scales up and rotates with odd/even lines splitting apart. The signature "wow" effect from GSAP kinetic typography demos.

```jsx
import React from "react";
import { useCurrentFrame, AbsoluteFill } from "remotion";

// Custom cubic-bezier (0.86, 0, 0.07, 1) — snappy ease from kinetic demo
function customEase(t) {
  const [p1x, p1y, p2x, p2y] = [0.86, 0, 0.07, 1];
  const cx = 3 * p1x,
    bx = 3 * (p2x - p1x) - cx,
    ax = 1 - cx - bx;
  const cy = 3 * p1y,
    by = 3 * (p2y - p1y) - cy,
    ay = 1 - cy - by;
  const sX = (t) => ((ax * t + bx) * t + cx) * t;
  const sY = (t) => ((ay * t + by) * t + cy) * t;
  const dX = (t) => (3 * ax * t + 2 * bx) * t + cx;
  let t2 = t;
  for (let i = 0; i < 8; i++) {
    const x = sX(t2) - t;
    if (Math.abs(x) < 1e-6) return sY(t2);
    const d = dX(t2);
    if (Math.abs(d) < 1e-6) break;
    t2 -= x / d;
  }
  let a = 0,
    b = 1;
  t2 = t;
  for (let i = 0; i < 20; i++) {
    const x = sX(t2);
    if (Math.abs(x - t) < 1e-6) return sY(t2);
    if (t > x) a = t2;
    else b = t2;
    t2 = (b - a) * 0.5 + a;
  }
  return sY(t2);
}

const KineticGrid = ({ frame, startFrame, durationFrames, text, gridOpacity = 0.05 }) => {
  const lf = frame - startFrame;
  if (lf < 0 || lf > durationFrames) return null;
  const t = Math.min(1, lf / durationFrames);

  const scaleP = customEase(t);
  const scale = 1 + scaleP * 1.7;
  const rot = -scaleP * 90;
  const lineOff = scaleP * 200;

  // Opacity curve: fade in → peak → fade out
  const op = t < 0.25 ? t / 0.25 : t < 0.55 ? 1 : 1 - (t - 0.55) / 0.45;

  const rows = 12;
  const rep = `${text}  ${text}  ${text}`;

  return (
    <div
      style={{
        position: "absolute",
        width: 5000,
        height: 2400,
        top: "50%",
        left: "50%",
        marginTop: -1200,
        marginLeft: -2500,
        display: "grid",
        justifyContent: "center",
        alignContent: "center",
        transform: `scale(${scale}) rotate(${rot}deg)`,
        opacity: op * gridOpacity,
      }}
    >
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          style={{
            whiteSpace: "nowrap",
            fontSize: 150,
            lineHeight: 0.78,
            fontWeight: 900,
            color: i % 2 === 0 ? "#ffffff" : "#ffcc00",
            transform: `translateX(${i % 2 === 0 ? lineOff : -lineOff}%)`,
          }}
        >
          {rep}
        </div>
      ))}
    </div>
  );
};

export default KineticGrid;
```

---

## 7. Character Explosion (containeranimation SplitText style)

Characters fly in from random Y positions with `back.out(1.2)` easing. Inspired by GSAP's SplitText + ScrollTrigger horizontal scroll demo.

```jsx
import React from "react";
import { useCurrentFrame } from "remotion";
import gsap from "gsap";

const FPS = 30;

function seededRandom(seed) {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

function gsapEase(t, name) {
  return gsap.parseEase(name)(Math.max(0, Math.min(1, t)));
}

const CharsExplode = ({
  frame,
  startFrame,
  text,
  size = 80,
  weight = 900,
  color = "#ffcc00",
  gap = 4,
  seed = 100,
  entranceSec = 1.8,
}) => {
  const lf = frame - startFrame;
  if (lf < 0) return null;

  const charAnim = FPS * 0.35;
  const entranceFrames = FPS * entranceSec;
  const stagger = entranceFrames / (text.length + 2);

  return (
    <div style={{ display: "flex", gap, justifyContent: "center", flexWrap: "wrap" }}>
      {text.split("").map((ch, i) => {
        const cf = Math.max(0, lf - i * stagger);
        const p = Math.min(1, cf / charAnim);
        const rY = (seededRandom(seed + i) - 0.5) * 400;
        const rR = (seededRandom(seed + i + 999) - 0.5) * 40;

        const y = (1 - gsapEase(p, "back.out(1.2)")) * rY;
        const r = (1 - gsapEase(p, "back.out(1.5)")) * rR;
        const o = gsapEase(p, "power3.out");
        const s = 0.3 + gsapEase(Math.min(1, cf / (FPS * 0.15)), "power2.out") * 0.7;

        // Post-landing breathing
        const breathe =
          Math.sin((Math.max(0, cf - charAnim) / FPS) * Math.PI * 1.5 + i * 0.3) * 1.5;

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontSize: size,
              fontWeight: weight,
              color,
              opacity: o,
              transform: `translateY(${y + breathe}px) rotate(${r}deg) scale(${s})`,
              textShadow: `0 0 30px ${color}44, 0 0 60px ${color}22`,
            }}
          >
            {ch === " " ? "\u00A0" : ch}
          </span>
        );
      })}
    </div>
  );
};

export default CharsExplode;
```

---

## 8. Blur Reveal (kinetic typography SplitText style)

Characters transition from `blur(12px)` to sharp with custom easing stagger. Inspired by GSAP's SplitText mask animation.

```jsx
import React from "react";
import { useCurrentFrame } from "remotion";

// See template 6 for customEase implementation
function customEase(t) {
  /* ... */
}

const FPS = 30;

const CharsBlur = ({
  frame,
  startFrame,
  text,
  size = 48,
  weight = 700,
  color = "#ffcc00",
  gap = 2,
  stagger = 0.07,
  align = "center",
}) => {
  const lf = frame - startFrame;
  if (lf < 0) return null;
  const st = FPS * stagger;

  return (
    <div style={{ display: "flex", gap, justifyContent: align, flexWrap: "wrap" }}>
      {text.split("").map((ch, i) => {
        const cf = Math.max(0, lf - i * st);
        const p = Math.min(1, cf / (FPS * 0.7));
        const e = customEase(p);
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontSize: size,
              fontWeight: weight,
              color,
              opacity: e,
              filter: `blur(${(1 - e) * 12}px)`,
              willChange: "filter, opacity",
            }}
          >
            {ch === " " ? "\u00A0" : ch}
          </span>
        );
      })}
    </div>
  );
};

export default CharsBlur;
```
