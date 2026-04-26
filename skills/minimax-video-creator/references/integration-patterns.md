# GSAP + Remotion Integration Patterns

Three patterns for combining GSAP's animation engine with Remotion's frame-based rendering. Choose based on complexity.

---

## Pattern 1: gsap.parseEase() + interpolate() (Simple)

**When to use:** Simple easing on individual properties, one-element animations, particle effects.

**How it works:** Extract GSAP's easing function via `gsap.parseEase()`, then pass it to Remotion's `interpolate()` as the `easing` parameter.

### Complete Example

```jsx
import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill, interpolate } from "remotion";
import gsap from "gsap";

const SimpleEaseDemo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Parse GSAP easing functions
  const elasticEase = gsap.parseEase("elastic.out(1, 0.3)");
  const backEase = gsap.parseEase("back.out(2)");

  // Animate X with elastic ease
  const x = interpolate(frame, [0, 60], [0, 800], {
    extrapolateRight: "clamp",
    easing: elasticEase,
  });

  // Animate rotation with back ease
  const rotation = interpolate(frame, [0, 90], [0, 360], {
    extrapolateRight: "clamp",
    easing: backEase,
  });

  // Fade in with power ease
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
    easing: gsap.parseEase("power3.out"),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e" }}>
      <div
        style={{
          width: 120,
          height: 120,
          borderRadius: 16,
          backgroundColor: "#e94560",
          opacity,
          transform: `translateX(${x}px) rotate(${rotation}deg)`,
        }}
      />
    </AbsoluteFill>
  );
};

export default SimpleEaseDemo;
```

### With Stagger (Multiple Elements)

GSAP's `stagger` doesn't work directly in Remotion. Instead, compute per-element local frames:

```jsx
const StaggerDemo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const items = ["A", "B", "C", "D", "E"];
  const staggerDelay = 3; // frames between each item

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        display: "flex",
        gap: 16,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {items.map((item, i) => {
        const localFrame = Math.max(0, frame - i * staggerDelay);
        const progress = Math.min(1, localFrame / 30);

        const ease = gsap.parseEase("back.out(2)");
        const eased = ease(progress);

        return (
          <div
            key={i}
            style={{
              width: 80,
              height: 80,
              borderRadius: 12,
              backgroundColor: `hsl(${i * 60 + 180}, 70%, 60%)`,
              opacity: eased,
              transform: `translateY(${(1 - eased) * 50}px) scale(${eased})`,
            }}
          >
            {item}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
```

---

## Pattern 2: Proxy Object + GSAP Timeline (Complex)

**When to use:** Multi-step sequences, overlapping animations, choreography with precise timing control.

**How it works:** Create a GSAP timeline on a plain JS object (proxy). Each frame, set the timeline's time to `frame / fps`, then read the proxy object's values. GSAP updates the proxy values, and you use those in React rendering.

### Complete Example

```jsx
import React, { useEffect, useRef, useState } from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from "remotion";
import gsap from "gsap";

const TimelineDemo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [s, setState] = useState({ x: 100, y: 400, rotation: 0, scale: 0, opacity: 0 });
  const tlRef = useRef(null);

  useEffect(() => {
    const proxy = { x: 100, y: 400, rotation: 0, scale: 0, opacity: 0 };

    const tl = gsap.timeline({ paused: true });

    // Phase 1: Scale up and fade in (0-1s)
    tl.to(
      proxy,
      {
        scale: 1,
        opacity: 1,
        duration: 1,
        ease: "elastic.out(1, 0.5)",
      },
      0,
    );

    // Phase 2: Move right with rotation (0.5-2.5s)
    tl.to(
      proxy,
      {
        x: 800,
        rotation: 360,
        duration: 2,
        ease: "power2.inOut",
      },
      0.5,
    );

    // Phase 3: Move up (1.5-3s)
    tl.to(
      proxy,
      {
        y: 100,
        duration: 1.5,
        ease: "back.out(1.7)",
      },
      1.5,
    );

    // Phase 4: Scale down (3-4s)
    tl.to(
      proxy,
      {
        scale: 0.5,
        opacity: 0,
        duration: 1,
        ease: "power3.in",
      },
      3,
    );

    tlRef.current = { tl, proxy };
  }, []);

  useEffect(() => {
    if (tlRef.current) {
      const { tl, proxy } = tlRef.current;
      tl.time(frame / fps);
      // Must create new object to trigger React re-render
      setState({ ...proxy });
    }
  }, [frame, fps]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f0f23" }}>
      <div
        style={{
          position: "absolute",
          left: state.x,
          top: state.y,
          width: 120,
          height: 120,
          borderRadius: 16,
          backgroundColor: "#e94560",
          opacity: state.opacity,
          transform: `rotate(${state.rotation}deg) scale(${state.scale})`,
        }}
      />
    </AbsoluteFill>
  );
};

export default TimelineDemo;
```

### Multi-Element Proxy Timeline

For multiple animated elements, use separate proxies or a nested object:

```jsx
useEffect(() => {
  const proxies = {
    title: { y: -100, opacity: 0 },
    box1: { x: 0, y: 0, scale: 0, rotation: 0 },
    box2: { x: 0, y: 0, scale: 0, rotation: 0 },
  };

  const tl = gsap.timeline({ paused: true });

  tl.to(proxies.title, { y: 0, opacity: 1, duration: 0.8, ease: "power3.out" }, 0)
    .to(
      proxies.box1,
      { x: 300, scale: 1, rotation: 180, duration: 1.5, ease: "elastic.out(1,0.5)" },
      0.3,
    )
    .to(proxies.box2, { x: 500, y: 200, scale: 1, duration: 1.2, ease: "back.out(2)" }, "<0.3");

  tlRef.current = { tl, proxies };
}, []);

useEffect(() => {
  if (tlRef.current) {
    const { tl, proxies } = tlRef.current;
    tl.time(frame / fps);
    setState({
      title: { ...proxies.title },
      box1: { ...proxies.box1 },
      box2: { ...proxies.box2 },
    });
  }
}, [frame]);
```

---

## Pattern 3: Pure Functional (Particles and Lists)

**When to use:** Many elements (>20) with parameterized animations, no side effects needed.

**How it works:** Compute all animation values as pure functions of `frame`. No refs, no state, no timeline. Each element's properties are calculated from its index and the current frame.

### Helper Function

```jsx
function gsapEase(t, easeName) {
  return gsap.parseEase(easeName)(Math.max(0, Math.min(1, t)));
}
```

### Complete Particle Example

```jsx
import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from "remotion";
import gsap from "gsap";

const COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"];

function gsapEase(t, easeName) {
  return gsap.parseEase(easeName)(Math.max(0, Math.min(1, t)));
}

const Particle = ({ index, total, frame, fps }) => {
  const angle = (index / total) * Math.PI * 2;
  const delay = Math.floor((index / total) * 15);

  const localFrame = Math.max(0, frame - delay);
  const progress = Math.min(1, localFrame / (fps * 1.5));

  const distEase = gsapEase(progress, "elastic.out(1,0.5)");
  const fadeEase = gsapEase(Math.min(1, localFrame / (fps * 0.4)), "power3.out");

  const dist = distEase * 350;
  const x = 540 + Math.cos(angle) * dist;
  const y = 540 + Math.sin(angle) * dist;
  const size = 6 + Math.sin(index * 1.7) * 4;

  return (
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        borderRadius: index % 2 === 0 ? "50%" : "2px",
        backgroundColor: COLORS[index % COLORS.length],
        opacity: Math.max(0, fadeEase * (1 - progress * 0.7)),
        transform: `rotate(${distEase * 180}deg)`,
        boxShadow: `0 0 ${size * 2}px ${COLORS[index % COLORS.length]}66`,
      }}
    />
  );
};

const ParticleExplosion = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const count = 50;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a1a" }}>
      {Array.from({ length: count }).map((_, i) => (
        <Particle key={i} index={i} total={count} frame={frame} fps={fps} />
      ))}
    </AbsoluteFill>
  );
};

export default ParticleExplosion;
```

---

## Decision Guide

| Scenario                           | Pattern                  | Why                                           |
| ---------------------------------- | ------------------------ | --------------------------------------------- |
| Single element with nice easing    | 1 (parseEase)            | Simplest, direct                              |
| Text character stagger             | 3 (Pure)                 | Many elements, parameterized                  |
| Particle explosion                 | 3 (Pure)                 | Performance with many DOM nodes               |
| Multi-step choreography            | 2 (Proxy Timeline)       | Timeline features: overlap, labels            |
| Logo reveal sequence               | 2 (Proxy Timeline)       | Precise timing control                        |
| Loading animation                  | 1 (parseEase)            | Single progress value                         |
| Background effect                  | 3 (Pure)                 | Reusable, side-effect free                    |
| Complex scene with 5+ elements     | 2 (Proxy Timeline)       | All elements managed in one timeline          |
| Kinetic typography                 | 3 (Pure)                 | Per-character blur/explosion, no side effects |
| Multi-scene video with transitions | 3 (Pure) + scene manager | Frame-based scene switching                   |
