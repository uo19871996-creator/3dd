import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Audio,
  continueRender,
  delayRender,
  Easing,
  Img,
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
import { Icon } from "./Icon";
import { Logo } from "./Logo";
import { MapCard } from "./MapCard";
import { FONT, FPS, INK, MUTED, type ChartSpec, type Chunk, type Photo, type SceneV2, type ShortV2Props } from "./types";

const TAIL = 10; // sahne çıkış animasyonu (kare)
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

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

/* ---------- Arka plan ---------- */

const Background: React.FC<{ accent: string; icon: string }> = ({ accent, icon }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const blob = (i: number, size: number, color: string, opacity: number) => {
    const x = 540 + Math.sin(t * 0.18 + i * 2.1) * 420;
    const y = 960 + Math.cos(t * 0.14 + i * 1.3) * 780;
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x - size / 2,
          top: y - size / 2,
          width: size,
          height: size,
          background: `radial-gradient(closest-side, ${color} 0%, ${color}99 30%, ${color}33 62%, transparent 100%)`,
          opacity,
        }}
      />
    );
  };
  return (
    <AbsoluteFill style={{ background: "#060a14", overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(120% 75% at 50% 0%, #121b31 0%, #060a14 62%)" }} />
      {blob(0, 1500, accent, 0.26)}
      {blob(1, 1200, "#6366f1", 0.2)}
      {blob(2, 1100, accent, 0.14)}
      <div
        style={{
          position: "absolute",
          right: -220,
          bottom: 120,
          opacity: 0.06,
          transform: `rotate(${-12 + Math.sin(t * 0.3) * 4}deg)`,
        }}
      >
        <Icon name={icon} size={900} color="#ffffff" strokeWidth={1.2} />
      </div>
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "90px 90px",
          backgroundPosition: `0px ${(t * 14) % 90}px`,
          maskImage: "radial-gradient(90% 70% at 50% 45%, black 30%, transparent 100%)",
          WebkitMaskImage: "radial-gradient(90% 70% at 50% 45%, black 30%, transparent 100%)",
        }}
      />
      <AbsoluteFill
        style={{ background: "radial-gradient(120% 90% at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%)" }}
      />
    </AbsoluteFill>
  );
};

/* ---------- Üst bar ---------- */

const TopBar: React.FC<{ p: ShortV2Props; sceneIdx: number; sec: number }> = ({ p, sceneIdx, sec }) => {
  const frame = useCurrentFrame();
  const enter = spring({ frame, fps: FPS, config: { damping: 200 } });
  return (
    <div
      style={{
        position: "absolute",
        top: 90,
        left: 60,
        right: 60,
        opacity: enter,
        transform: `translateY(${(1 - enter) * -30}px)`,
        fontFamily: FONT,
      }}
    >
      <div style={{ display: "flex", gap: 10 }}>
        {p.scenes.map((s, i) => {
          const fill = i < sceneIdx ? 1 : i > sceneIdx ? 0 : (sec - s.start) / Math.max(0.1, s.end - s.start);
          return (
            <div key={i} style={{ flex: 1, height: 8, borderRadius: 8, background: "rgba(255,255,255,0.16)" }}>
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
      <div style={{ marginTop: 30, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <Logo size={62} style={{ borderRadius: 14, boxShadow: "0 6px 18px rgba(0,0,0,0.45)" }} />
          <div
            style={{
              background: p.accent,
              color: "#04121a",
              fontWeight: 900,
              fontSize: 32,
              letterSpacing: 2,
              padding: "11px 22px",
              borderRadius: 14,
            }}
          >
            {p.brand}
          </div>
          <div style={{ color: MUTED, fontWeight: 700, fontSize: 30 }}>{p.date}</div>
        </div>
        <div style={{ color: INK, fontWeight: 800, fontSize: 32 }}>
          {p.index}
          <span style={{ color: MUTED }}>/{p.total}</span>
        </div>
      </div>
    </div>
  );
};

/* ---------- Başlık (açılışta büyük, sonra üstte küçük) ---------- */

const IconBadge: React.FC<{ name: string; accent: string; size: number; local: number }> = ({
  name,
  accent,
  size,
  local,
}) => {
  const s = spring({ frame: local, fps: FPS, config: { damping: 11, mass: 0.7 } });
  const float = Math.sin(local / 18) * 8;
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: `radial-gradient(circle at 35% 30%, ${accent}55, ${accent}18 60%, transparent 72%)`,
        border: `4px solid ${accent}`,
        boxShadow: `0 0 80px ${accent}66, inset 0 0 40px ${accent}33`,
        transform: `translateY(${float}px) scale(${0.6 + 0.4 * s})`,
        opacity: Math.min(1, s * 1.5),
      }}
    >
      <Icon name={name} size={size * 0.5} color={INK} strokeWidth={1.6} />
    </div>
  );
};

const TitleBlock: React.FC<{ p: ShortV2Props }> = ({ p }) => {
  const frame = useCurrentFrame();
  const firstEnd = Math.round((p.scenes[0]?.end ?? 3) * FPS);
  const shrink = spring({ frame: frame - firstEnd + 6, fps: FPS, config: { damping: 200 } });
  const sub = p.scenes.find((s) => s.subscribe);
  const hideForOutro = sub ? interpolate(frame, [sub.start * FPS, sub.start * FPS + 10], [1, 0], clamp) : 1;
  const big = p.title.length > 60 ? 68 : p.title.length > 42 ? 78 : 96;
  const size = interpolate(shrink, [0, 1], [big, 42]);
  const top = interpolate(shrink, [0, 1], [740, 236]);
  const words = p.title.split(" ");
  const hookIcon = p.scenes[0]?.icon ?? p.categoryIcon;
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 380,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          opacity: p.scenes[0]?.photo ? 0 : 1 - shrink,
          transform: `scale(${1 - shrink * 0.3})`,
        }}
      >
        <IconBadge name={hookIcon} accent={p.accent} size={300} local={frame - 2} />
      </div>
      <div style={{ position: "absolute", top, left: 60, right: 60, fontFamily: FONT, opacity: hideForOutro }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            color: p.accent,
            border: `3px solid ${p.accent}`,
            borderRadius: 100,
            padding: "8px 22px",
            fontWeight: 800,
            fontSize: 26,
            letterSpacing: 4,
            marginBottom: interpolate(shrink, [0, 1], [30, 0]),
            maxHeight: interpolate(shrink, [0, 1], [80, 0]),
            overflow: "hidden",
            opacity: spring({ frame: frame - 4, fps: FPS, config: { damping: 200 } }) * (1 - shrink),
          }}
        >
          <Icon name={p.categoryIcon} size={28} color={p.accent} strokeWidth={2.4} />
          {p.category}
        </div>
        <div
          style={{
            color: INK,
            fontWeight: 900,
            fontSize: size,
            lineHeight: 1.08,
            letterSpacing: -1.5,
            // küçük halde en fazla 2 satır
            maxHeight: shrink > 0.5 ? size * 1.08 * 2 + 4 : undefined,
            overflow: shrink > 0.5 ? "hidden" : undefined,
          }}
        >
          {words.map((w, i) => {
            const s = spring({ frame: frame - 6 - i * 3, fps: FPS, config: { damping: 15, mass: 0.6 } });
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  marginRight: "0.26em",
                  opacity: Math.min(1, s * 1.4),
                  transform: `translateY(${(1 - s) * 60}px) scale(${0.9 + 0.1 * s})`,
                }}
              >
                {w}
              </span>
            );
          })}
        </div>
        <div
          style={{
            marginTop: interpolate(shrink, [0, 1], [30, 0]),
            height: 8 * (1 - shrink),
            width: interpolate(spring({ frame: frame - 14, fps: FPS, config: { damping: 200 } }), [0, 1], [0, 220]),
            background: p.accent,
            borderRadius: 8,
          }}
        />
      </div>
    </>
  );
};

/* ---------- Fotoğraflar (Wikimedia Commons, atıflı) ---------- */

const Credit: React.FC<{ text: string; style?: React.CSSProperties }> = ({ text, style }) => (
  <div
    style={{
      fontFamily: FONT,
      fontWeight: 600,
      fontSize: 20,
      color: "rgba(255,255,255,0.78)",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis",
      textShadow: "0 2px 8px rgba(0,0,0,0.8)",
      ...style,
    }}
  >
    {text}
  </div>
);

const PhotoVisual: React.FC<{
  photo: Photo;
  accent: string;
  local: number;
  dur: number;
  stat?: { value: string; label: string };
}> = ({ photo, accent, local, dur, stat }) => {
  const k = interpolate(local, [0, Math.max(1, dur)], [0, 1], clamp);
  const pop = spring({ frame: local - 10, fps: FPS, config: { damping: 13, mass: 0.6 } });
  return (
    <div
      style={{
        position: "relative",
        width: 960,
        height: 760,
        borderRadius: 40,
        overflow: "hidden",
        border: "2px solid rgba(255,255,255,0.14)",
        boxShadow: `0 30px 80px rgba(0,0,0,0.45), 0 0 100px ${accent}22`,
      }}
    >
      <Img
        src={staticFile(photo.src)}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${1.04 + 0.1 * k}) translate(${-1.2 * k}%, ${-0.8 * k}%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "linear-gradient(180deg, rgba(4,7,15,0) 45%, rgba(4,7,15,0.88) 100%)",
        }}
      />
      {stat ? (
        <div
          style={{
            position: "absolute",
            left: 36,
            bottom: 58,
            fontFamily: FONT,
            opacity: pop,
            transform: `translateY(${(1 - pop) * 30}px)`,
          }}
        >
          <div style={{ color: accent, fontWeight: 900, fontSize: 110, lineHeight: 1, letterSpacing: -2 }}>
            {stat.value}
          </div>
          <div style={{ color: INK, fontWeight: 700, fontSize: 36, marginTop: 8 }}>{stat.label}</div>
        </div>
      ) : null}
      <Credit text={photo.credit} style={{ position: "absolute", left: 24, right: 24, bottom: 16 }} />
    </div>
  );
};

const HookPhoto: React.FC<{ p: ShortV2Props }> = ({ p }) => {
  const frame = useCurrentFrame();
  const photo = p.scenes[0]?.photo;
  if (!photo) return null;
  const firstEnd = Math.round((p.scenes[0]?.end ?? 3) * FPS);
  const fade = interpolate(frame, [firstEnd - 4, firstEnd + 8], [1, 0], clamp);
  if (fade <= 0) return null;
  const k = interpolate(frame, [0, firstEnd], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Img
        src={staticFile(photo.src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${1.08 + 0.1 * k})`,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(4,7,15,0.55) 0%, rgba(4,7,15,0.35) 30%, rgba(4,7,15,0.75) 60%, rgba(4,7,15,0.92) 100%)",
        }}
      />
      <Credit text={photo.credit} style={{ position: "absolute", left: 60, right: 60, top: 246 }} />
    </AbsoluteFill>
  );
};

/* ---------- Sahne görselleri ---------- */

const parseStat = (v: string) => {
  const m = v.match(/^([%$€₺]?)(\d+(?:,\d+)?)(\+| milyon| milyar| bin)?$/);
  if (!m) return null;
  const decimals = m[2].includes(",") ? m[2].split(",")[1].length : 0;
  return { prefix: m[1], num: parseFloat(m[2].replace(",", ".")), decimals, suffix: m[3] ?? "" };
};

const fmt = (n: number, decimals: number) => n.toFixed(decimals).replace(".", ",");

const Heading: React.FC<{ n: number; text: string; accent: string; icon?: string }> = ({ n, text, accent, icon }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 22, fontFamily: FONT }}>
    <div
      style={{
        minWidth: 76,
        height: 76,
        borderRadius: 22,
        background: "rgba(255,255,255,0.08)",
        border: "2px solid rgba(255,255,255,0.16)",
        color: accent,
        fontWeight: 900,
        fontSize: 34,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {icon ? <Icon name={icon} size={40} color={accent} strokeWidth={2.2} /> : String(n).padStart(2, "0")}
    </div>
    <div style={{ color: INK, fontWeight: 800, fontSize: 56, lineHeight: 1.1, letterSpacing: -0.5 }}>{text}</div>
  </div>
);

const StatVisual: React.FC<{ stat: { value: string; label: string }; accent: string; icon?: string; local: number }> = ({
  stat,
  accent,
  icon,
  local,
}) => {
  const pop = spring({ frame: local - 6, fps: FPS, config: { damping: 12, mass: 0.6 } });
  const parsed = parseStat(stat.value);
  const k = interpolate(local, [6, 40], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const shown = parsed ? `${parsed.prefix}${fmt(parsed.num * k, parsed.decimals)}${parsed.suffix}` : stat.value;
  const len = stat.value.length;
  return (
    <div
      style={{
        padding: "56px 56px",
        borderRadius: 40,
        background: "linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04))",
        border: "2px solid rgba(255,255,255,0.14)",
        boxShadow: `0 30px 80px rgba(0,0,0,0.35), 0 0 120px ${accent}22`,
        transform: `scale(${0.85 + 0.15 * pop})`,
        transformOrigin: "left top",
        opacity: Math.min(1, pop * 1.6),
        fontFamily: FONT,
        display: "flex",
        alignItems: "center",
        gap: 40,
      }}
    >
      <div style={{ flex: 1 }}>
        <div
          style={{
            color: accent,
            fontWeight: 900,
            fontSize: len > 9 ? 110 : len > 6 ? 140 : 180,
            lineHeight: 1,
            letterSpacing: -3,
          }}
        >
          {shown}
        </div>
        <div style={{ marginTop: 18, color: MUTED, fontWeight: 700, fontSize: 42, lineHeight: 1.2 }}>{stat.label}</div>
      </div>
      {icon ? (
        <div style={{ opacity: 0.9 }}>
          <Icon name={icon} size={150} color={accent} strokeWidth={1.4} />
        </div>
      ) : null}
    </div>
  );
};

const ChartVisual: React.FC<{ chart: ChartSpec; accent: string; local: number }> = ({ chart, accent, local }) => {
  const items = chart.items.slice(0, 5);
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 1);
  return (
    <div
      style={{
        padding: "44px 48px",
        borderRadius: 40,
        background: "rgba(255,255,255,0.06)",
        border: "2px solid rgba(255,255,255,0.12)",
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        gap: 34,
      }}
    >
      {items.map((it, i) => {
        const g = interpolate(local, [8 + i * 6, 38 + i * 6], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
        const decimals = String(it.value).includes(".") ? String(it.value).split(".")[1].length : 0;
        const isLast = i === items.length - 1;
        return (
          <div key={i}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ color: INK, fontWeight: 800, fontSize: 38 }}>{it.label}</span>
              <span style={{ color: isLast ? accent : INK, fontWeight: 900, fontSize: 40 }}>
                {chart.unit === "%" ? "%" : ""}
                {fmt(it.value * g, decimals)}
                {chart.unit && chart.unit !== "%" ? chart.unit : ""}
              </span>
            </div>
            <div style={{ height: 34, borderRadius: 17, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
              <div
                style={{
                  width: `${(Math.abs(it.value) / max) * 100 * g}%`,
                  height: "100%",
                  borderRadius: 17,
                  background: isLast ? accent : `${accent}88`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const ListVisual: React.FC<{ points: string[]; accent: string; local: number; dur: number }> = ({
  points,
  accent,
  local,
  dur,
}) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 26, fontFamily: FONT }}>
    {points.slice(0, 4).map((pt, i) => {
      const at = 6 + (i * dur * 0.7) / Math.max(1, points.length);
      const s = spring({ frame: local - at, fps: FPS, config: { damping: 15 } });
      return (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 26,
            padding: "28px 34px",
            borderRadius: 28,
            background: "rgba(255,255,255,0.07)",
            border: "2px solid rgba(255,255,255,0.12)",
            opacity: s,
            transform: `translateX(${(1 - s) * 80}px)`,
          }}
        >
          <div
            style={{
              width: 22,
              height: 22,
              borderRadius: 11,
              background: accent,
              boxShadow: `0 0 24px ${accent}`,
              flexShrink: 0,
            }}
          />
          <div style={{ color: INK, fontWeight: 700, fontSize: 44, lineHeight: 1.2 }}>{pt}</div>
        </div>
      );
    })}
  </div>
);

const IconVisual: React.FC<{ name: string; accent: string; local: number }> = ({ name, accent, local }) => (
  <div style={{ display: "flex", justifyContent: "center", paddingTop: 40 }}>
    <IconBadge name={name} accent={accent} size={460} local={local} />
  </div>
);

const QuestionVisual: React.FC<{ accent: string; local: number }> = ({ accent, local }) => {
  const s = spring({ frame: local - 14, fps: FPS, config: { damping: 14 } });
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 46, paddingTop: 30 }}>
      <IconBadge name="message-circle" accent={accent} size={400} local={local} />
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "22px 40px",
          borderRadius: 100,
          background: "rgba(255,255,255,0.08)",
          border: `3px solid ${accent}`,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 44,
          color: INK,
          opacity: s,
          transform: `translateY(${(1 - s) * 30}px)`,
        }}
      >
        <Icon name="message-square-text" size={50} color={accent} strokeWidth={2.2} />
        Yorumunu bekliyorum
      </div>
    </div>
  );
};

const SubscribeVisual: React.FC<{ p: ShortV2Props; local: number }> = ({ p, local }) => {
  const CLICK = 42; // imlecin düğmeye tıkladığı kare
  const logo = spring({ frame: local, fps: FPS, config: { damping: 10, mass: 0.7 } });
  const name = spring({ frame: local - 8, fps: FPS, config: { damping: 14 } });
  const btn = spring({ frame: local - 14, fps: FPS, config: { damping: 12 } });
  const clicked = local >= CLICK;
  const press = clicked ? 1 - 0.08 * Math.max(0, 1 - (local - CLICK) / 6) : 1;
  const cur = interpolate(local, [16, CLICK - 2], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const curX = interpolate(cur, [0, 1], [800, 545]);
  const curY = interpolate(cur, [0, 1], [930, 530]);
  const curOpacity = interpolate(local, [14, 20, CLICK + 18, CLICK + 28], [0, 1, 1, 0], clamp);
  const ripple = clicked ? Math.min(1, (local - CLICK) / 14) : 0;
  const bellRot = clicked ? Math.sin((local - CLICK) / 2.2) * 22 * Math.max(0, 1 - (local - CLICK) / 40) : 0;
  return (
    <div style={{ position: "relative", height: 820, fontFamily: FONT }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div
          style={{
            transform: `scale(${0.4 + 0.6 * logo}) rotate(${(1 - logo) * -12}deg)`,
            opacity: Math.min(1, logo * 1.5),
            filter: `drop-shadow(0 0 60px ${p.accent}66)`,
          }}
        >
          <Logo size={300} style={{ borderRadius: 64, boxShadow: "0 30px 80px rgba(0,0,0,0.55)" }} />
        </div>
        <div
          style={{
            marginTop: 40,
            color: INK,
            fontWeight: 900,
            fontSize: 70,
            letterSpacing: -1,
            opacity: name,
            transform: `translateY(${(1 - name) * 30}px)`,
          }}
        >
          {p.channelName ?? p.brand}
        </div>
        <div style={{ marginTop: 10, color: MUTED, fontWeight: 700, fontSize: 36, opacity: name, textAlign: "center" }}>
          {p.channelTagline ?? "Her gün gündemin en önemli 5 haberi"}
        </div>
        <div
          style={{
            marginTop: 54,
            position: "relative",
            display: "flex",
            alignItems: "center",
            gap: 20,
            padding: "28px 56px",
            borderRadius: 100,
            background: clicked ? "#2b303c" : "#ff1f3d",
            boxShadow: clicked ? "none" : "0 16px 50px rgba(255,31,61,0.45)",
            color: "#fff",
            fontWeight: 900,
            fontSize: 50,
            letterSpacing: 1,
            opacity: btn,
            transform: `scale(${(0.7 + 0.3 * btn) * press})`,
          }}
        >
          <div style={{ transform: `rotate(${bellRot}deg)`, display: "flex" }}>
            <Icon name={clicked ? "bell-ring" : "bell"} size={58} color="#fff" strokeWidth={2.4} />
          </div>
          {clicked ? "ABONE OLUNDU" : "ABONE OL"}
          {clicked ? <Icon name="check" size={52} color="#fff" strokeWidth={3} /> : null}
          {ripple > 0 && ripple < 1 ? (
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                width: 40 + ripple * 520,
                height: 40 + ripple * 520,
                marginLeft: -(20 + ripple * 260),
                marginTop: -(20 + ripple * 260),
                borderRadius: "50%",
                border: "4px solid rgba(255,255,255,0.7)",
                opacity: 1 - ripple,
              }}
            />
          ) : null}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: curX,
          top: curY,
          opacity: curOpacity,
          transform: `scale(${clicked && local < CLICK + 6 ? 0.85 : 1})`,
          filter: "drop-shadow(0 6px 14px rgba(0,0,0,0.6))",
        }}
      >
        <Icon name="mouse-pointer-2" size={96} color="#ffffff" strokeWidth={1.6} />
      </div>
    </div>
  );
};

/* ---------- Sahne katmanı (giriş/çıkış geçişi) ---------- */

const SceneLayer: React.FC<{ s: SceneV2; n: number; last: boolean; p: ShortV2Props }> = ({ s, n, last, p }) => {
  const frame = useCurrentFrame();
  const startF = Math.round(s.start * FPS);
  const endF = Math.round(s.end * FPS);
  const local = frame - startF;
  const dur = endF - startF;
  const enter = spring({ frame: local, fps: FPS, config: { damping: 16, mass: 0.7 } });
  const exit = interpolate(frame, [endF, endF + TAIL], [0, 1], clamp);
  const kind = s.subscribe
    ? "subscribe"
    : last
      ? "question"
      : s.photo
      ? "photo"
      : s.map
        ? "map"
        : s.chart
          ? "chart"
          : s.stat
            ? "stat"
            : s.points?.length
              ? "list"
              : "icon";
  const visual =
    kind === "photo" && s.photo ? (
      <PhotoVisual photo={s.photo} accent={p.accent} local={local} dur={dur} stat={s.stat} />
    ) : kind === "map" && s.map ? (
      <MapCard spec={s.map} accent={p.accent} local={local} duration={dur} />
    ) : kind === "chart" && s.chart ? (
      <ChartVisual chart={s.chart} accent={p.accent} local={local} />
    ) : kind === "stat" && s.stat ? (
      <StatVisual stat={s.stat} accent={p.accent} icon={s.icon} local={local} />
    ) : kind === "list" && s.points ? (
      <>
        <ListVisual points={s.points} accent={p.accent} local={local} dur={dur} />
        <div style={{ display: "flex", justifyContent: "center", marginTop: 50, opacity: 0.85 }}>
          <IconBadge name={s.icon ?? p.categoryIcon} accent={p.accent} size={240} local={local - 4} />
        </div>
      </>
    ) : kind === "subscribe" ? (
      <SubscribeVisual p={p} local={local} />
    ) : kind === "question" ? (
      <QuestionVisual accent={p.accent} local={local} />
    ) : (
      <IconVisual name={s.icon ?? p.categoryIcon} accent={p.accent} local={local} />
    );
  return (
    <div
      style={{
        position: "absolute",
        top: 365,
        left: 60,
        right: 60,
        opacity: Math.min(1, enter * 1.4) * (1 - exit),
        transform: `translateX(${(1 - enter) * 120 - exit * 120}px) scale(${0.97 + 0.03 * enter})`,
      }}
    >
      {kind === "subscribe" ? null : (
        <Heading n={n} text={s.heading} accent={p.accent} icon={kind === "icon" ? undefined : s.icon} />
      )}
      <div style={{ marginTop: kind === "subscribe" ? 0 : 40 }}>{visual}</div>
    </div>
  );
};

/* ---------- Altyazı ---------- */

const Caption: React.FC<{ chunk?: Chunk; accent: string; top: number }> = ({ chunk, accent, top }) => {
  const frame = useCurrentFrame();
  if (!chunk) return null;
  const local = frame - Math.round(chunk.start * FPS);
  const pop = spring({ frame: local, fps: FPS, config: { damping: 14, mass: 0.45 } });
  const words = chunk.text.split(" ");
  const dur = Math.max(1, (chunk.end - chunk.start) * FPS);
  const active = Math.min(words.length - 1, Math.floor((local / dur) * words.length));
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        width: 880,
        top,
        minHeight: 300,
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
          fontSize: chunk.text.length > 24 ? 74 : 86,
          lineHeight: 1.16,
          letterSpacing: -1,
          padding: "18px 34px 22px",
          borderRadius: 30,
          background: "rgba(4,7,15,0.62)",
          boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
          transform: `scale(${0.88 + pop * 0.12})`,
          opacity: Math.min(1, pop * 2),
        }}
      >
        {words.map((w, i) => (
          <span key={i} style={{ display: "inline-block", marginRight: "0.24em", color: i === active ? accent : INK }}>
            {w}
          </span>
        ))}
      </div>
    </div>
  );
};

/* ---------- Kompozisyon ---------- */

export const ShortV2: React.FC<ShortV2Props> = (p) => {
  useFonts();
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const sec = frame / FPS;
  let sceneIdx = p.scenes.findIndex((s) => sec >= s.start && sec < s.end);
  if (sceneIdx < 0) sceneIdx = sec < (p.scenes[0]?.start ?? 0) ? 0 : p.scenes.length - 1;
  const scene = p.scenes[sceneIdx];
  const chunk = scene?.chunks.find((c) => sec >= c.start && sec < (c.until ?? c.end));
  const flash = interpolate(frame, [0, 7], [0.55, 0], clamp);
  const fadeOut = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <Background accent={p.accent} icon={p.categoryIcon} />
      <HookPhoto p={p} />
      <TopBar p={p} sceneIdx={sceneIdx} sec={sec} />
      <TitleBlock p={p} />
      {p.scenes.map((s, i) => {
        if (i === 0) return null;
        const lastIdx = p.scenes.length - 1 - (p.scenes[p.scenes.length - 1]?.subscribe ? 1 : 0);
        const a = Math.round(s.start * FPS);
        const b = Math.round(s.end * FPS) + TAIL;
        return frame >= a && frame <= b ? (
          <SceneLayer key={i} s={s} n={i} last={i === lastIdx} p={p} />
        ) : null;
      })}
      <Caption chunk={chunk} accent={p.accent} top={sceneIdx === 0 ? 1290 : 1225} />
      <AbsoluteFill style={{ background: "#ffffff", opacity: flash, pointerEvents: "none" }} />
      {p.audio ? <Audio src={staticFile(p.audio)} /> : null}
    </AbsoluteFill>
  );
};
