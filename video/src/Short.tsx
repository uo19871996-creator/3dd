import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Audio,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import "@fontsource/montserrat/500.css";
import "@fontsource/montserrat/700.css";
import "@fontsource/montserrat/800.css";
import "@fontsource/montserrat/900.css";

export const FPS = 30;

// until: altyazının ekranda kalacağı an (cümle/sahne arası sessizlikte ekran boş kalmasın)
type Chunk = { text: string; start: number; end: number; until?: number };
type Scene = {
  heading: string;
  stat?: { value: string; label: string };
  start: number;
  end: number;
  chunks: Chunk[];
};
export type ShortProps = {
  brand: string;
  date: string;
  index: number;
  total: number;
  category: string;
  accent: string;
  title: string;
  audio: string;
  duration: number;
  levels: number[];
  scenes: Scene[];
};

const FONT = "Montserrat, sans-serif";
const INK = "#f8fafc";
const MUTED = "rgba(226,232,240,0.62)";

const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all(
      [500, 700, 800, 900].map((w) => document.fonts.load(`${w} 40px Montserrat`, "ğüşıöçĞÜŞİÖÇ")),
    )
      .then(() => document.fonts.ready)
      .then(() => continueRender(handle))
      .catch(() => continueRender(handle));
  }, [handle]);
};

const Background: React.FC<{ accent: string; level: number }> = ({ accent, level }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const blob = (i: number, size: number, color: string, opacity: number) => {
    const x = 540 + Math.sin(t * 0.21 + i * 2.1) * 420;
    const y = 900 + Math.cos(t * 0.17 + i * 1.3) * 760;
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x - size / 2,
          top: y - size / 2,
          width: size,
          height: size,
          // blur() filtresi yerine radial-gradient: yazılımsal render'da çok daha hızlı
          background: `radial-gradient(closest-side, ${color} 0%, ${color}99 30%, ${color}33 62%, transparent 100%)`,
          opacity,
        }}
      />
    );
  };
  return (
    <AbsoluteFill style={{ background: "#070b16" }}>
      <AbsoluteFill
        style={{
          background: "radial-gradient(120% 80% at 50% 0%, #131c33 0%, #070b16 62%)",
        }}
      />
      {blob(0, 1500, accent, 0.3 + level * 0.1)}
      {blob(1, 1200, "#6366f1", 0.24)}
      {blob(2, 1100, accent, 0.18)}
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
          backgroundSize: "90px 90px",
          backgroundPosition: `0px ${(t * 14) % 90}px`,
          maskImage: "radial-gradient(90% 70% at 50% 45%, black 30%, transparent 100%)",
          WebkitMaskImage: "radial-gradient(90% 70% at 50% 45%, black 30%, transparent 100%)",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(7,11,22,0.55) 0%, rgba(7,11,22,0) 22%, rgba(7,11,22,0) 70%, rgba(7,11,22,0.75) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

const Header: React.FC<ShortProps & { sceneIdx: number; sec: number }> = (p) => {
  const frame = useCurrentFrame();
  const enter = spring({ frame, fps: FPS, config: { damping: 200 } });
  return (
    <div
      style={{
        position: "absolute",
        top: 96,
        left: 64,
        right: 64,
        opacity: enter,
        transform: `translateY(${(1 - enter) * -30}px)`,
      }}
    >
      <div style={{ display: "flex", gap: 10 }}>
        {p.scenes.map((s, i) => {
          const fill =
            i < p.sceneIdx ? 1 : i > p.sceneIdx ? 0 : (p.sec - s.start) / Math.max(0.1, s.end - s.start);
          return (
            <div
              key={i}
              style={{
                flex: 1,
                height: 8,
                borderRadius: 8,
                background: "rgba(255,255,255,0.16)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.min(1, Math.max(0, fill)) * 100}%`,
                  height: "100%",
                  background: p.accent,
                  borderRadius: 8,
                }}
              />
            </div>
          );
        })}
      </div>
      <div
        style={{
          marginTop: 34,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontFamily: FONT,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div
            style={{
              background: p.accent,
              color: "#04121a",
              fontWeight: 900,
              fontSize: 34,
              letterSpacing: 2,
              padding: "12px 24px",
              borderRadius: 14,
            }}
          >
            {p.brand}
          </div>
          <div style={{ color: MUTED, fontWeight: 700, fontSize: 30 }}>{p.date}</div>
        </div>
        <div style={{ color: INK, fontWeight: 800, fontSize: 34 }}>
          {p.index}
          <span style={{ color: MUTED }}>/{p.total}</span>
        </div>
      </div>
    </div>
  );
};

const fitTitle = (text: string) => (text.length > 60 ? 74 : text.length > 42 ? 86 : 100);

const TitleBlock: React.FC<{ p: ShortProps; sceneIdx: number }> = ({ p, sceneIdx }) => {
  const frame = useCurrentFrame();
  const firstEnd = Math.round((p.scenes[0]?.end ?? 3) * FPS);
  // 0 = büyük başlık (ilk sahne), 1 = küçülmüş başlık (sonraki sahneler)
  const shrink = spring({ frame: frame - firstEnd + 6, fps: FPS, config: { damping: 200 } });
  const words = p.title.split(" ");
  const big = fitTitle(p.title);
  const size = interpolate(shrink, [0, 1], [big, 50]);
  const top = interpolate(shrink, [0, 1], [430, 268]);
  return (
    <div style={{ position: "absolute", top, left: 64, right: 64, fontFamily: FONT }}>
      <div
        style={{
          display: "inline-block",
          color: p.accent,
          border: `3px solid ${p.accent}`,
          borderRadius: 100,
          padding: "8px 24px",
          fontWeight: 800,
          fontSize: 28,
          letterSpacing: 4,
          marginBottom: interpolate(shrink, [0, 1], [34, 18]),
          opacity: spring({ frame: frame - 4, fps: FPS, config: { damping: 200 } }),
        }}
      >
        {p.category}
      </div>
      <div
        style={{
          color: INK,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1.08,
          letterSpacing: -1.5,
          textWrap: "balance",
        }}
      >
        {words.map((w, i) => {
          const s = spring({ frame: frame - 6 - i * 3, fps: FPS, config: { damping: 16, mass: 0.6 } });
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                marginRight: "0.26em",
                opacity: Math.min(1, s * 1.4),
                transform: `translateY(${(1 - s) * 50}px)`,
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
      <div
        style={{
          marginTop: interpolate(shrink, [0, 1], [36, 20]),
          height: 8,
          width: interpolate(
            spring({ frame: frame - 14, fps: FPS, config: { damping: 200 } }),
            [0, 1],
            [0, sceneIdx === 0 ? 260 : 140],
          ),
          background: p.accent,
          borderRadius: 8,
        }}
      />
    </div>
  );
};

const SceneCard: React.FC<{ scene: Scene; n: number; accent: string }> = ({ scene, n, accent }) => {
  const frame = useCurrentFrame();
  const local = frame - Math.round(scene.start * FPS);
  const left = Math.round(scene.end * FPS) - frame;
  const enter = spring({ frame: local, fps: FPS, config: { damping: 18, mass: 0.7 } });
  const exit = interpolate(left, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const statPop = spring({ frame: local - 8, fps: FPS, config: { damping: 11, mass: 0.6 } });
  return (
    <div
      style={{
        position: "absolute",
        top: 560,
        left: 64,
        right: 64,
        fontFamily: FONT,
        opacity: Math.min(enter * 1.5, 1) * exit,
        transform: `translateX(${(1 - enter) * 90}px)`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
        <div
          style={{
            width: 76,
            height: 76,
            borderRadius: 22,
            background: "rgba(255,255,255,0.08)",
            border: "2px solid rgba(255,255,255,0.16)",
            color: accent,
            fontWeight: 900,
            fontSize: 36,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {String(n).padStart(2, "0")}
        </div>
        <div style={{ color: INK, fontWeight: 800, fontSize: 56, lineHeight: 1.1, letterSpacing: -0.5 }}>
          {scene.heading}
        </div>
      </div>
      {scene.stat ? (
        <div
          style={{
            marginTop: 46,
            padding: "40px 44px",
            borderRadius: 36,
            background: "linear-gradient(135deg, rgba(255,255,255,0.11), rgba(255,255,255,0.04))",
            border: "2px solid rgba(255,255,255,0.14)",
            transform: `scale(${0.82 + statPop * 0.18})`,
            transformOrigin: "left top",
            opacity: Math.min(1, statPop * 1.6),
          }}
        >
          <div
            style={{
              color: accent,
              fontWeight: 900,
              fontSize: scene.stat.value.length > 9 ? 100 : scene.stat.value.length > 6 ? 128 : 160,
              lineHeight: 1,
              letterSpacing: -3,
            }}
          >
            {scene.stat.value}
          </div>
          <div style={{ marginTop: 16, color: MUTED, fontWeight: 700, fontSize: 40, lineHeight: 1.2 }}>
            {scene.stat.label}
          </div>
        </div>
      ) : null}
    </div>
  );
};

const Caption: React.FC<{ chunk?: Chunk; accent: string; top: number }> = ({ chunk, accent, top }) => {
  const frame = useCurrentFrame();
  if (!chunk) return null;
  const local = frame - Math.round(chunk.start * FPS);
  const pop = spring({ frame: local, fps: FPS, config: { damping: 14, mass: 0.45 } });
  const words = chunk.text.split(" ");
  const dur = Math.max(1, (chunk.end - chunk.start) * FPS);
  const active = Math.min(words.length - 1, Math.floor((local / dur) * words.length));
  const size = chunk.text.length > 24 ? 80 : 94;
  return (
    <div
      style={{
        position: "absolute",
        left: 70,
        right: 70,
        top,
        height: 420,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          textAlign: "center",
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1.14,
          letterSpacing: -1,
          transform: `scale(${0.86 + pop * 0.14})`,
          opacity: Math.min(1, pop * 2),
          textShadow: "0 8px 40px rgba(0,0,0,0.55)",
          textWrap: "balance",
        }}
      >
        {words.map((w, i) => (
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: "0.24em",
              color: i === active ? accent : INK,
            }}
          >
            {w}
          </span>
        ))}
      </div>
    </div>
  );
};

const Bars: React.FC<{ levels: number[]; accent: string }> = ({ levels, accent }) => {
  const frame = useCurrentFrame();
  const N = 27;
  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        top: 1500,
        width: 500,
        height: 90,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {Array.from({ length: N }).map((_, i) => {
        const lv = levels[Math.max(0, frame - Math.abs(i - (N - 1) / 2) * 1)] ?? 0;
        const wob = 0.55 + 0.45 * Math.sin(i * 1.7 + frame * 0.35);
        const h = 8 + lv * wob * 82;
        return (
          <div key={i} style={{ width: 10, height: h, borderRadius: 6, background: accent, opacity: 0.85 }} />
        );
      })}
    </div>
  );
};

export const Short: React.FC<ShortProps> = (p) => {
  useFonts();
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const sec = frame / FPS;
  let sceneIdx = p.scenes.findIndex((s) => sec >= s.start && sec < s.end);
  if (sceneIdx < 0) sceneIdx = sec < (p.scenes[0]?.start ?? 0) ? 0 : p.scenes.length - 1;
  const scene = p.scenes[sceneIdx];
  const chunk = scene?.chunks.find((c) => sec >= c.start && sec < (c.until ?? c.end));
  const level = p.levels[frame] ?? 0;
  const fadeOut = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <Background accent={p.accent} level={level} />
      <Header {...p} sceneIdx={sceneIdx} sec={sec} />
      <TitleBlock p={p} sceneIdx={sceneIdx} />
      {sceneIdx > 0 && scene ? <SceneCard scene={scene} n={sceneIdx} accent={p.accent} /> : null}
      <Caption chunk={chunk} accent={p.accent} top={sceneIdx === 0 ? 1010 : scene?.stat ? 1130 : 900} />
      <Bars levels={p.levels} accent={p.accent} />
      {p.audio ? <Audio src={staticFile(p.audio)} /> : null}
    </AbsoluteFill>
  );
};
