/**
 * SceneComposition.tsx — MiniMax Video Creator v2
 *
 * Complete Remotion composition with GSAP-powered animations:
 * - TextReveal (character stagger with back easing)
 * - CharsExplode (random Y explosion)
 * - CharsBlur (blur-to-sharp reveal)
 * - KineticGrid (large text grid zoom/rotate)
 * - ScrambleText (character scramble reveal)
 * - SweepLine (accent bar)
 * - ScatterBg (atmospheric background text)
 * - Camera movements (pan, zoom, tilt)
 * - Cross-fade scene transitions
 * - Caption overlay
 */

import gsap from "gsap";
import React, { useEffect, useRef, useState } from "react";
import {
  Sequence,
  useCurrentFrame,
  interpolate,
  AbsoluteFill,
  Easing,
  Audio,
  staticFile,
} from "remotion";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type AnimationType =
  | "fade"
  | "slide"
  | "zoom"
  | "blur_reveal"
  | "char_explode"
  | "scramble"
  | "kinetic"
  | "none";

export type Transition = "fade" | "crossfade" | "wipe" | "none";
export type CameraMove = "pan_left" | "pan_right" | "zoom_in" | "zoom_out" | "tilt_up" | "static";

export interface SceneData {
  imagePath?: string; // relative to public/, e.g. "scenes/img_xxx.jpg"
  audioPath?: string; // relative to public/, e.g. "audio/speech_xxxxx.mp3"
  durationInFrames: number;
  transition?: Transition;
  animation?: AnimationType;
  cameraMove?: CameraMove;

  // Text overlays
  title?: string; // Main text for animation effects
  caption?: string; // Bottom-center caption

  // Scene metadata
  mood?: string;
}

export interface VideoProps {
  scenes: SceneData[];
  musicPath?: string;
  title?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility: Deterministic random
// ─────────────────────────────────────────────────────────────────────────────

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

function gsapEase(t: number, easeName: string): number {
  return gsap.parseEase(easeName)(Math.max(0, Math.min(1, t)));
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility: Custom cubic bezier solver (0.86, 0, 0.07, 1)
// ─────────────────────────────────────────────────────────────────────────────

function customEase(t: number): number {
  const [p1x, p1y, p2x, p2y] = [0.86, 0, 0.07, 1];
  const cx = 3 * p1x,
    bx = 3 * (p2x - p1x) - cx,
    ax = 1 - cx - bx;
  const cy = 3 * p1y,
    by = 3 * (p2y - p1y) - cy,
    ay = 1 - cy - by;
  const sX = (t: number) => ((ax * t + bx) * t + cx) * t;
  const sY = (t: number) => ((ay * t + by) * t + cy) * t;
  const dX = (t: number) => (3 * ax * t + 2 * bx) * t + cx;
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

// ─────────────────────────────────────────────────────────────────────────────
// Animation Components
// ─────────────────────────────────────────────────────────────────────────────

const FPS = 30;
const COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"];

/**
 * TextReveal — Character stagger entrance with back easing
 */
const TextReveal: React.FC<{
  text: string;
  frame: number;
  fps: number;
  y?: number;
  fontSize?: number;
  staggerFrames?: number;
  startFrame?: number;
  color?: string;
}> = ({
  text,
  frame,
  fps,
  y = 490,
  fontSize = 64,
  staggerFrames = 2,
  startFrame = 10,
  color = "#ffcc00",
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
        const yEase = gsapEase(progress, "back.out(2)");
        const opacityEase = gsapEase(progress, "power2.out");
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              color,
              fontSize,
              fontWeight: 900,
              fontFamily: "system-ui, sans-serif",
              opacity: opacityEase,
              transform: `translateY(${(1 - yEase) * 60}px)`,
              textShadow: `0 0 20px ${color}66`,
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

/**
 * CharsExplode — Characters fly in from random Y positions with back.out
 */
const CharsExplode: React.FC<{
  text: string;
  frame: number;
  startFrame?: number;
  size?: number;
  color?: string;
  seed?: number;
}> = ({ text, frame, startFrame = 0, size = 80, color = "#ffcc00", seed = 100 }) => {
  const lf = frame - startFrame;
  if (lf < 0) return null;
  const charAnim = FPS * 0.35;
  const entranceFrames = FPS * 1.8;
  const stagger = entranceFrames / (text.length + 2);

  return (
    <div style={{ display: "flex", gap: 4, justifyContent: "center", flexWrap: "wrap" }}>
      {text.split("").map((ch, i) => {
        const cf = Math.max(0, lf - i * stagger);
        const p = Math.min(1, cf / charAnim);
        const rY = (seededRandom(seed + i) - 0.5) * 400;
        const rR = (seededRandom(seed + i + 999) - 0.5) * 40;
        const y = (1 - gsapEase(p, "back.out(1.2)")) * rY;
        const r = (1 - gsapEase(p, "back.out(1.5)")) * rR;
        const o = gsapEase(p, "power3.out");
        const s = 0.3 + gsapEase(Math.min(1, cf / (FPS * 0.15)), "power2.out") * 0.7;
        const breathe =
          Math.sin((Math.max(0, cf - charAnim) / FPS) * Math.PI * 1.5 + i * 0.3) * 1.5;

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontSize: size,
              fontWeight: 900,
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

/**
 * CharsBlur — Characters transition from blur(12px) to sharp
 */
const CharsBlur: React.FC<{
  text: string;
  frame: number;
  startFrame?: number;
  size?: number;
  color?: string;
  stagger?: number;
}> = ({ text, frame, startFrame = 0, size = 48, color = "#ffcc00", stagger = 0.07 }) => {
  const lf = frame - startFrame;
  if (lf < 0) return null;
  const st = FPS * stagger;

  return (
    <div style={{ display: "flex", gap: 2, justifyContent: "center", flexWrap: "wrap" }}>
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
              fontWeight: 700,
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

/**
 * KineticGrid — Large text grid that scales up and rotates
 */
const KineticGrid: React.FC<{
  frame: number;
  startFrame: number;
  durationFrames: number;
  text: string;
  gridOpacity?: number;
}> = ({ frame, startFrame, durationFrames, text, gridOpacity = 0.05 }) => {
  const lf = frame - startFrame;
  if (lf < 0 || lf > durationFrames) return null;
  const t = Math.min(1, lf / durationFrames);
  const scaleP = customEase(t);
  const scale = 1 + scaleP * 1.7;
  const rot = -scaleP * 90;
  const lineOff = scaleP * 200;
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

/**
 * ScrambleText — Characters cycle through symbols then settle
 */
const ScrambleText: React.FC<{
  text: string;
  frame: number;
  startFrame?: number;
  duration?: number;
  fontSize?: number;
  color?: string;
  y?: number;
}> = ({
  text,
  frame,
  startFrame = 0,
  duration = 60,
  fontSize = 48,
  color = "#ffcc00",
  y = 490,
}) => {
  const lf = frame - startFrame;
  if (lf < 0) return null;
  const syms = "■▪▌▐▬●◆★✦█▓";
  const progress = Math.min(1, lf / duration);
  let display = "";
  for (let i = 0; i < text.length; i++) {
    const cp = progress * (text.length + 4) - i;
    if (cp >= 1) {
      display += text[i];
    } else if (cp > 0) {
      display +=
        text[i] === " "
          ? " "
          : syms[Math.floor(seededRandom(42 + i + Math.floor(cp * 7)) * syms.length)];
    } else {
      display += " ";
    }
  }

  const fadeIn = Math.min(1, lf / 10);

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        top: y,
        textAlign: "center",
        opacity: fadeIn,
      }}
    >
      <span
        style={{
          fontFamily: "monospace",
          fontSize,
          fontWeight: 700,
          color,
          letterSpacing: 2,
          textShadow: `0 0 15px ${color}44`,
        }}
      >
        {display}
      </span>
    </div>
  );
};

/**
 * SweepLine — Colored accent bar sweeps left to right
 */
const SweepLine: React.FC<{
  frame: number;
  startFrame: number;
  duration: number;
  color?: string;
  y?: number;
}> = ({ frame, startFrame, duration, color = "#ffcc00", y = 540 }) => {
  const lf = frame - startFrame;
  if (lf < 0 || lf > duration) return null;
  const p = customEase(Math.min(1, lf / duration));
  const fadeOut = lf > duration * 0.65 ? 1 - (lf - duration * 0.65) / (duration * 0.35) : 1;
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: y,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          height: 2,
          width: `${p * 80}%`,
          backgroundColor: color,
          opacity: 0.45 * Math.max(0, fadeOut),
          boxShadow: `0 0 12px ${color}44`,
        }}
      />
    </div>
  );
};

/**
 * ScatterBg — Small keywords at fixed positions with pulsing opacity
 */
const SCATTER_KEYWORDS = [
  "AI",
  "未来",
  "创造",
  "无限",
  "科技",
  "想象",
  "进化",
  "智慧",
  "灵感",
  "梦想",
  "视频",
  "动画",
];

const SCATTER_POS = SCATTER_KEYWORDS.map((text, i) => ({
  text,
  x: seededRandom(i * 7 + 1) * 88 + 4,
  y: seededRandom(i * 7 + 2) * 88 + 4,
}));

const ScatterBg: React.FC<{ frame: number; color?: string }> = ({ frame, color = "#ffcc00" }) => (
  <>
    {SCATTER_POS.map((item, i) => {
      const pulse = 0.15 + Math.sin((frame / FPS) * 0.4 + i * 0.8) * 0.08;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${item.x}%`,
            top: `${item.y}%`,
            fontSize: 11,
            fontWeight: 700,
            fontFamily: "monospace",
            color,
            opacity: pulse,
            letterSpacing: 2,
          }}
        >
          {item.text}
        </div>
      );
    })}
  </>
);

/**
 * Vignette overlay for cinematic depth
 */
const Vignette: React.FC<{ intensity?: number }> = ({ intensity = 0.6 }) => (
  <div
    style={{
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: `radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,${intensity}) 100%)`,
      pointerEvents: "none",
    }}
  />
);

// ─────────────────────────────────────────────────────────────────────────────
// Camera Movement
// ─────────────────────────────────────────────────────────────────────────────

function getCameraTransform(
  frame: number,
  durationInFrames: number,
  cameraMove: CameraMove,
): { transform: string } {
  switch (cameraMove) {
    case "pan_left":
      return {
        transform: `translateX(${interpolate(frame, [0, durationInFrames], [0, -80], { extrapolateRight: "clamp" })}px) scale(1.1)`,
      };
    case "pan_right":
      return {
        transform: `translateX(${interpolate(frame, [0, durationInFrames], [-80, 0], { extrapolateRight: "clamp" })}px) scale(1.1)`,
      };
    case "zoom_in":
      return {
        transform: `scale(${interpolate(frame, [0, durationInFrames], [1, 1.2], { extrapolateRight: "clamp" })})`,
      };
    case "zoom_out":
      return {
        transform: `scale(${interpolate(frame, [0, durationInFrames], [1.2, 1], { extrapolateRight: "clamp" })})`,
      };
    case "tilt_up":
      return {
        transform: `translateY(${interpolate(frame, [0, durationInFrames], [60, -60], { extrapolateRight: "clamp" })}px) scale(1.1)`,
      };
    default:
      return { transform: "scale(1)" };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Caption Overlay
// ─────────────────────────────────────────────────────────────────────────────

const CaptionOverlay: React.FC<{
  text: string;
  frame: number;
  durationFrames: number;
}> = ({ text, frame, durationFrames }) => {
  const fadeIn = Math.min(15, Math.floor(durationFrames * 0.1));
  const fadeOut = Math.min(15, Math.floor(durationFrames * 0.1));
  const opacity = Math.min(
    Math.min(1, Math.max(0, frame / fadeIn)),
    Math.min(1, Math.max(0, (durationFrames - frame) / fadeOut)),
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 60,
        opacity,
      }}
    >
      <div
        style={{
          display: "inline-block",
          backgroundColor: "rgba(0,0,0,0.72)",
          color: "#fff",
          fontSize: 26,
          fontWeight: 600,
          padding: "12px 32px",
          borderRadius: 8,
          fontFamily: "sans-serif",
          textAlign: "center",
          maxWidth: "80%",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Scene Opacity for Cross-Fade
// ─────────────────────────────────────────────────────────────────────────────

function sceneOpacity(
  frame: number,
  start: number,
  end: number,
  fadeIn = 20,
  fadeOut = 25,
): number {
  return Math.min(
    Math.min(1, Math.max(0, (frame - start) / fadeIn)),
    Math.min(1, Math.max(0, (end - frame) / fadeOut)),
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Single Scene Component
// ─────────────────────────────────────────────────────────────────────────────

const Scene: React.FC<SceneData & { globalFrame: number }> = ({
  globalFrame,
  imagePath,
  audioPath,
  durationInFrames,
  transition = "fade",
  animation = "fade",
  cameraMove = "static",
  title,
  caption,
}) => {
  const frame = globalFrame;
  const { fps } = useVideoConfig();

  // Fade transition
  const tf = Math.min(20, Math.floor(durationInFrames * 0.15));
  const enterOpacity = interpolate(frame, [0, tf], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const exitOpacity = interpolate(frame, [durationInFrames - tf, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.in(Easing.cubic),
  });
  const baseOpacity = Math.min(enterOpacity, exitOpacity);

  // Camera movement
  const cam = getCameraTransform(frame, durationInFrames, cameraMove);

  return (
    <AbsoluteFill style={{ opacity: baseOpacity }}>
      {/* Background image with camera movement */}
      {imagePath && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            overflow: "hidden",
            ...cam,
          }}
        >
          <Img
            src={staticFile(imagePath)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
      )}

      {/* Dark overlay for text readability */}
      {imagePath && title && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "linear-gradient(to bottom, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.7) 100%)",
          }}
        />
      )}

      {/* Vignette */}
      <Vignette intensity={imagePath ? 0.4 : 0.6} />

      {/* Scatter background (when no image) */}
      {!imagePath && <ScatterBg frame={frame} />}

      {/* Kinetic grid (behind text) */}
      {animation === "kinetic" && title && (
        <KineticGrid
          frame={frame}
          startFrame={0}
          durationFrames={durationInFrames}
          text={title}
          gridOpacity={0.04}
        />
      )}

      {/* Text animation */}
      {title && animation === "fade" && (
        <TextReveal text={title} frame={frame} fps={fps} y={440} fontSize={56} />
      )}
      {title && animation === "char_explode" && (
        <div
          style={{
            position: "absolute",
            top: "40%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <CharsExplode
            text={title}
            frame={frame}
            startFrame={5}
            size={72}
            seed={title.length * 7}
          />
        </div>
      )}
      {title && animation === "blur_reveal" && (
        <div
          style={{
            position: "absolute",
            top: "40%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <CharsBlur text={title} frame={frame} startFrame={3} size={56} stagger={0.08} />
        </div>
      )}
      {title && animation === "scramble" && (
        <ScrambleText
          text={title}
          frame={frame}
          startFrame={0}
          duration={50}
          fontSize={52}
          y={440}
        />
      )}
      {title && animation === "kinetic" && (
        <div
          style={{
            position: "absolute",
            top: "38%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <CharsExplode
            text={title}
            frame={frame}
            startFrame={10}
            size={64}
            color="#fff"
            seed={title.length * 13}
          />
        </div>
      )}

      {/* Sweep accent line */}
      {title && (animation === "kinetic" || animation === "char_explode") && (
        <SweepLine frame={frame} startFrame={5} duration={durationInFrames - 10} y={530} />
      )}

      {/* Caption */}
      {caption && <CaptionOverlay text={caption} frame={frame} durationFrames={durationInFrames} />}

      {/* Audio */}
      {audioPath && <Audio src={staticFile(audioPath)} />}
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Video Composition
// ─────────────────────────────────────────────────────────────────────────────

export const VideoComposition: React.FC<VideoProps> = ({ scenes, musicPath, title }) => {
  const safeScenes = scenes ?? [];
  const frame = useCurrentFrame();
  const totalDuration = safeScenes.reduce((sum, s) => sum + s.durationInFrames, 0);

  // Calculate frame offsets for each scene
  let frameOffset = 0;
  const sceneOffsets = safeScenes.map((s) => {
    const from = frameOffset;
    frameOffset += s.durationInFrames;
    return from;
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background music */}
      {musicPath && <Audio src={staticFile(musicPath)} loop volume={0.3} />}

      {/* Title scene (optional opener) */}
      {title && safeScenes.length > 0 && (
        <Sequence
          from={0}
          durationInFrames={Math.min(safeScenes[0].durationInFrames, totalDuration)}
        >
          {/* Title is overlaid via first scene */}
        </Sequence>
      )}

      {/* Scenes */}
      {safeScenes.map((scene, i) => (
        <Sequence
          key={i}
          from={sceneOffsets[i]}
          durationInFrames={scene.durationInFrames}
          name={`Scene ${i + 1}`}
        >
          <Scene {...scene} globalFrame={frame - sceneOffsets[i]} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Registration Example (for src/index.tsx)
// ─────────────────────────────────────────────────────────────────────────────
//
// import React from 'react';
// import { registerRoot, Composition } from 'remotion';
// import { VideoComposition, VideoProps, SceneData } from './SceneComposition';
//
// const scenes: SceneData[] = [
//   {
//     imagePath: "scenes/scene_0.jpg",
//     audioPath: "audio/speech_12345.mp3",
//     durationInFrames: 300,
//     animation: "blur_reveal",
//     transition: "crossfade",
//     cameraMove: "zoom_in",
//     title: "在信息的海洋深处",
//     caption: "AI的觉醒",
//     mood: "mysterious",
//   },
//   {
//     imagePath: "scenes/scene_1.jpg",
//     audioPath: "audio/speech_67890.mp3",
//     durationInFrames: 300,
//     animation: "char_explode",
//     transition: "crossfade",
//     cameraMove: "pan_left",
//     title: "数字世界的脉搏",
//     caption: "开始跳动",
//     mood: "dramatic",
//   },
//   // ... more scenes
// ];
//
// registerRoot(function App() {
//   return (
//     <Composition
//       id="MyVideo"
//       component={VideoComposition}
//       props={{ scenes, title: "AI的觉醒" } as VideoProps}
//       durationInFrames={scenes.reduce((sum, s) => sum + s.durationInFrames, 0)}
//       fps={30}
//       width={1920}
//       height={1080}
//     />
//   );
// });
