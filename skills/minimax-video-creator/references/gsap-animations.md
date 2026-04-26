# GSAP Animation Engine

## Three Integration Patterns

GSAP and Remotion have different execution models. Choose the right pattern:

| Pattern                     | Best For                             | Complexity |
| --------------------------- | ------------------------------------ | ---------- |
| **parseEase + interpolate** | Simple easing, single properties     | Low        |
| **Proxy + Timeline**        | Multi-step choreography, overlapping | Medium     |
| **Pure Functional**         | Particles, many elements, stagger    | Low        |

## Pattern 1: parseEase + interpolate

```jsx
import gsap from "gsap";
import { useCurrentFrame, interpolate } from "remotion";

const ease = gsap.parseEase("elastic.out(1, 0.3)");
const x = interpolate(frame, [0, 60], [0, 800], {
  extrapolateRight: "clamp",
  easing: ease,
});
```

## Pattern 2: Proxy + GSAP Timeline (Complex Choreography)

```jsx
const proxyRef = useRef({ x: 0, y: 0, rotation: 0, opacity: 0 });
const tlRef = useRef(null);

useEffect(() => {
  const tl = gsap.timeline({ paused: true });
  tl.to(proxyRef.current, { x: 500, duration: 2, ease: "power2.out" }).to(
    proxyRef.current,
    { y: 300, rotation: 360, duration: 1, ease: "elastic.out(1,0.5)" },
    "-=1",
  );
  tlRef.current = tl;
}, []);

useEffect(() => {
  if (tlRef.current) tlRef.current.time(frame / fps);
}, [frame]);
```

## Pattern 3: Pure Functional (Particles, Lists, Typography)

```jsx
function gsapEase(t, easeName) {
  return gsap.parseEase(easeName)(Math.max(0, Math.min(1, t)));
}
const progress = Math.min(1, localFrame / (fps * duration));
const eased = gsapEase(progress, "back.out(2)");
```

## Easing Guide for Video

| Effect           | Ease                                   | Why                          |
| ---------------- | -------------------------------------- | ---------------------------- |
| Entrance         | `back.out(2)` or `elastic.out(1, 0.5)` | Overshoot = dynamic          |
| Exit             | `power3.in`                            | Accelerating out = natural   |
| Slide/move       | `power2.inOut` or `expo.out`           | Smooth deceleration          |
| Scale pulse      | `elastic.out(1, 0.3)`                  | Springy feel                 |
| Stagger reveal   | per-char `back.out(1.7)`               | Each element has personality |
| Kinetic rotation | custom `cubic-bezier(0.86,0,0.07,1)`   | Snappy, dramatic             |

## Ready-to-Use Animation Components

All animation components are in the SceneComposition template. Key effects:

| Component           | Effect                                                 | Best For               |
| ------------------- | ------------------------------------------------------ | ---------------------- |
| `TextReveal`        | Character stagger, slides up with back easing          | Scene titles, opening  |
| `CharsExplode`      | Characters fly in from random Y with back.out          | Dramatic entrances     |
| `CharsBlur`         | Characters transition from blur(12px) to sharp         | Mysterious reveals     |
| `KineticGrid`       | Large text grid scales up + rotates, lines split apart | Maximum visual impact  |
| `ScrambleText`      | Characters cycle through random symbols then settle    | Tech/hacker aesthetic  |
| `SweepLine`         | Colored bar sweeps left to right                       | Highlight, accent      |
| `ScatterBg`         | Small keywords scattered with pulsing opacity          | Atmospheric background |
| `ProgressBar`       | Animated progress with elastic easing                  | Data/stats scenes      |
| `ParticleExplosion` | Burst of colored particles with elastic easing         | Openers, transitions   |

**Full templates:** `references/animation-templates.md`

## Critical Remotion Rules

1. **DO NOT** use `useGSAP()` from `@gsap/react` in Remotion — use `useCurrentFrame()`
2. **DO NOT** create GSAP tweens without `paused: true` — they won't sync with Remotion frames
3. **DO NOT** use `ScrollTrigger` in video compositions — no scroll in video
4. **DO NOT** use CSS `transition` — Remotion renders each frame independently
5. **DO NOT** forget `Math.max(0, Math.min(1, progress))` clamp before passing to GSAP ease
6. **DO NOT** use `inline-block` for character spans — use `display: "inline"` to preserve baseline
