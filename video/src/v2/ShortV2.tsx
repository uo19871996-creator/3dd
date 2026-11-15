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
        {p.total > 1 ? (
          <div style={{ color: INK, fontWeight: 800, fontSize: 32 }}>
            {p.index}
            <span style={{ color: MUTED }}>/{p.total}</span>
          </div>
        ) : null}
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
  // Açılış ikonu (fotoğrafsız açılışta) artık taşınan kartın ilk hali: Stage çizer.
  return (
    <>
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
            opacity: spring({ frame: frame + 8, fps: FPS, config: { damping: 200 } }) * (1 - shrink),
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
            const s = spring({ frame: frame + 8 - i * 1.5, fps: FPS, config: { damping: 15, mass: 0.6 } });
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

// Fotoğraf, bulunduğu kartı doldurur (kart küçülürken fotoğraf da onunla küçülür).
// hook: açılışın tam ekran fotoğrafı; karartma ve atıf, kart küçülmeye başlayınca (veil) söner.
const PhotoFill: React.FC<{
  photo: Photo;
  accent: string;
  local: number;
  dur: number;
  stat?: { value: string; label: string };
  hook?: boolean;
  veil?: number;
}> = ({ photo, accent, local, dur, stat, hook, veil = 1 }) => {
  const k = interpolate(local, [0, Math.max(1, dur)], [0, 1], clamp);
  const pop = spring({ frame: local - 10, fps: FPS, config: { damping: 13, mass: 0.6 } });
  return (
    <AbsoluteFill>
      <Img
        src={staticFile(photo.src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: hook
            ? `scale(${1.08 + 0.1 * k})`
            : `scale(${1.04 + 0.1 * k}) translate(${-1.2 * k}%, ${-0.8 * k}%)`,
        }}
      />
      {hook ? (
        <AbsoluteFill
          style={{
            opacity: veil,
            background:
              "linear-gradient(180deg, rgba(4,7,15,0.55) 0%, rgba(4,7,15,0.35) 30%, rgba(4,7,15,0.75) 60%, rgba(4,7,15,0.92) 100%)",
          }}
        />
      ) : (
        <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(4,7,15,0) 45%, rgba(4,7,15,0.88) 100%)" }} />
      )}
      {stat && !hook ? (
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
      {hook ? (
        <Credit text={photo.credit} style={{ position: "absolute", left: 60, right: 60, top: 246, opacity: veil }} />
      ) : (
        <Credit text={photo.credit} style={{ position: "absolute", left: 24, right: 24, bottom: 16 }} />
      )}
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
        transform: `translateY(${(1 - pop) * 24}px) scale(${0.94 + 0.06 * pop})`,
        transformOrigin: "left center",
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

const QuestionPill: React.FC<{ accent: string; local: number }> = ({ accent, local }) => {
  const s = spring({ frame: local - 14, fps: FPS, config: { damping: 14 } });
  return (
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
  );
};

const SubscribeVisual: React.FC<{ p: ShortV2Props; local: number }> = ({ p, local }) => {
  const CLICK = 30; // imlecin düğmeye tıkladığı kare
  const name = spring({ frame: local - 4, fps: FPS, config: { damping: 14 } });
  const btn = spring({ frame: local - 6, fps: FPS, config: { damping: 12 } });
  const clicked = local >= CLICK;
  const press = clicked ? 1 - 0.08 * Math.max(0, 1 - (local - CLICK) / 6) : 1;
  const cur = interpolate(local, [8, CLICK - 2], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const curX = interpolate(cur, [0, 1], [800, 545]);
  const curY = interpolate(cur, [0, 1], [930, 530]);
  const curOpacity = interpolate(local, [6, 12, CLICK + 14, CLICK + 22], [0, 1, 1, 0], clamp);
  const ripple = clicked ? Math.min(1, (local - CLICK) / 14) : 0;
  const bellRot = clicked ? Math.sin((local - CLICK) / 2.2) * 22 * Math.max(0, 1 - (local - CLICK) / 40) : 0;
  return (
    <div style={{ position: "relative", height: 820, fontFamily: FONT }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ width: 300, height: 300 }} /> {/* logo: taşınan kartın son hali (Stage) */}
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

/* ---------- Taşınan sahne: tek kart, sahneden sahneye dönüşür ----------
   Sahneler birbirinin yerine kayarak geçmez: ekranda tek bir kart vardır ve her sınırda bir
   sonraki sahnenin kartına dönüşür (konum, boyut, köşe, renk). Açılış fotoğrafı küçülüp ilk
   kart olur; fotoğrafsız açılışta ikon dairesi büyüyüp kart olur; soru sahnesinde kart daireye,
   kapanışta kanal logosuna dönüşür. Başlık satırı da yerinde kalır: numara sayaç gibi döner,
   yazı yükselerek değişir. Sahne içi zamanlamalar (ses efektleri bunlara bağlı) değişmedi. */

type Kind = "hookPhoto" | "hookIcon" | "photo" | "map" | "chart" | "stat" | "list" | "icon" | "question" | "subscribe";
type Geo = { x: number; y: number; w: number; h: number; r: number; acc: number; chrome: number };

const STAGE_Y = 481; // başlık satırı (365) + 76 + 40
const PRE = 6; // dönüşüm, sahne sınırından bu kadar kare önce başlar
const MORPH = 18; // dönüşüm süresi (kare)
const morphEase = Easing.bezier(0.3, 1.16, 0.45, 1); // hafifçe taşıp yerine oturur
const riseEase = Easing.bezier(0.2, 0, 0, 1);
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

const kindOf = (s: SceneV2, i: number, lastIdx: number): Kind => {
  if (i === 0) return s.photo ? "hookPhoto" : "hookIcon";
  if (s.subscribe) return "subscribe";
  if (i === lastIdx) return "question";
  if (s.photo) return "photo";
  if (s.map) return "map";
  if (s.chart) return "chart";
  if (s.stat) return "stat";
  if (s.points?.length) return "list";
  return "icon";
};

const lineCount = (t: string, perLine: number) => Math.max(1, Math.ceil(t.length / perLine));
const statFont = (v: string) => (v.length > 9 ? 110 : v.length > 6 ? 140 : 180);

// Her türün yerine oturmuş kart geometrisi (çerçeve koordinatları)
const geoOf = (k: Kind, s: SceneV2, local: number): Geo => {
  const card = (h: number): Geo => ({ x: 60, y: STAGE_Y, w: 960, h, r: 40, acc: 0, chrome: 1 });
  const float = Math.sin(local / 18) * 8;
  switch (k) {
    case "hookPhoto":
      return { x: 0, y: 0, w: 1080, h: 1920, r: 0, acc: 0, chrome: 0 };
    case "hookIcon":
      return { x: 390, y: 380 + float, w: 300, h: 300, r: 150, acc: 1, chrome: 1 };
    case "photo":
      return card(760);
    case "map":
      return card(700);
    case "chart": {
      const n = Math.max(1, Math.min(5, s.chart?.items.length ?? 1));
      return card(98 + n * 94 + (n - 1) * 34);
    }
    case "stat": {
      const st = s.stat ?? { value: "", label: "" };
      return card(122 + statFont(st.value) + 18 + 50 * lineCount(st.label, s.icon ? 24 : 32));
    }
    case "list": {
      const pts = (s.points ?? []).slice(0, 4);
      return card(66 + pts.reduce((a, t) => a + 56 + 53 * lineCount(t, 29), 0) + Math.max(0, pts.length - 1) * 26);
    }
    case "icon":
      return { x: 310, y: 521 + float, w: 460, h: 460, r: 230, acc: 1, chrome: 1 };
    case "question":
      return { x: 340, y: 511 + float, w: 400, h: 400, r: 200, acc: 1, chrome: 1 };
    case "subscribe":
      return { x: 390, y: 365, w: 300, h: 300, r: 64, acc: 0, chrome: 0 };
  }
};

const mixGeo = (a: Geo, b: Geo, t: number): Geo => {
  const m = (u: number, v: number) => u + (v - u) * t;
  const mc = (u: number, v: number) => u + (v - u) * clamp01(t);
  return { x: m(a.x, b.x), y: m(a.y, b.y), w: m(a.w, b.w), h: m(a.h, b.h), r: Math.max(0, m(a.r, b.r)), acc: mc(a.acc, b.acc), chrome: mc(a.chrome, b.chrome) };
};

// Kartın içeriği. Fotoğraf kartı doldurur (kartla birlikte küçülür); diğerleri kendi oturmuş
// boyutunda ortalanır, kart büyürken bir pencere gibi açılır (yazılar ara karelerde kırılmaz).
const CardContent: React.FC<{ k: Kind; s: SceneV2; p: ShortV2Props; local: number; dur: number; veil?: number }> = ({
  k,
  s,
  p,
  local,
  dur,
  veil,
}) => {
  if ((k === "hookPhoto" || k === "photo") && s.photo) {
    return <PhotoFill photo={s.photo} accent={p.accent} local={local} dur={dur} stat={s.stat} hook={k === "hookPhoto"} veil={veil} />;
  }
  const g = geoOf(k, s, 0);
  const center: React.CSSProperties = { position: "absolute", left: "50%", top: "50%", width: g.w, height: g.h, transform: "translate(-50%, -50%)" };
  const middle: React.CSSProperties = { ...center, display: "flex", flexDirection: "column", justifyContent: "center" };
  const glyph = (name: string, size: number) => (
    <div style={{ ...center, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Icon name={name} size={size} color={INK} strokeWidth={1.6} />
    </div>
  );
  switch (k) {
    case "hookIcon":
      return glyph(s.icon ?? p.categoryIcon, 150);
    case "map":
      return s.map ? <div style={center}><MapCard spec={s.map} accent={p.accent} local={local} duration={dur} /></div> : null;
    case "chart":
      return s.chart ? <div style={middle}><ChartVisual chart={s.chart} accent={p.accent} local={local} /></div> : null;
    case "stat":
      return s.stat ? <div style={middle}><StatVisual stat={s.stat} accent={p.accent} icon={s.icon} local={local} /></div> : null;
    case "list":
      return s.points ? (
        <div style={{ ...middle, padding: 28, boxSizing: "border-box" }}>
          <ListVisual points={s.points} accent={p.accent} local={local} dur={dur} />
        </div>
      ) : null;
    case "icon":
      return glyph(s.icon ?? p.categoryIcon, 230);
    case "question":
      return glyph("message-circle", 200);
    case "subscribe":
      return (
        <div style={center}>
          <Logo size={300} style={{ borderRadius: 64 }} />
        </div>
      );
    default:
      return null;
  }
};

// Kartın dışında kalan, sahneye ait parçalar (liste ikonu, soru hapı, kapanış yazıları)
const Satellite: React.FC<{ k: Kind; s: SceneV2; p: ShortV2Props; local: number; opacity: number }> = ({
  k,
  s,
  p,
  local,
  opacity,
}) => {
  if (opacity <= 0) return null;
  const g = geoOf(k, s, 0);
  if (k === "list") {
    const size = Math.max(0, Math.min(240, 1280 - (g.y + g.h + 40)));
    if (size < 120) return null;
    return (
      <div style={{ position: "absolute", top: g.y + g.h + 40, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: 0.85 * opacity }}>
        <IconBadge name={s.icon ?? p.categoryIcon} accent={p.accent} size={size} local={local - 4} />
      </div>
    );
  }
  if (k === "question") {
    return (
      <div style={{ position: "absolute", top: g.y + g.h + 46, left: 0, right: 0, display: "flex", justifyContent: "center", opacity }}>
        <QuestionPill accent={p.accent} local={local} />
      </div>
    );
  }
  if (k === "subscribe") {
    return (
      <div style={{ position: "absolute", top: 365, left: 60, right: 60, opacity }}>
        <SubscribeVisual p={p} local={local} />
      </div>
    );
  }
  return null;
};

const sceneTimes = (p: ShortV2Props) => {
  const S = p.scenes;
  const lastIdx = S.length - 1 - (S[S.length - 1]?.subscribe ? 1 : 0);
  const starts = S.map((s) => Math.round(s.start * FPS));
  const ends = S.map((s) => Math.round(s.end * FPS));
  const kinds = S.map((s, i) => kindOf(s, i, lastIdx));
  return { S, starts, ends, kinds };
};

// Şu anki sahne: dönüşüm sınırdan PRE kare önce başladığı için ona göre seçilir
const activeIndex = (frame: number, starts: number[]) => {
  let i = 0;
  for (let k = 1; k < starts.length; k++) if (frame >= starts[k] - PRE) i = k;
  return i;
};

const Stage: React.FC<{ p: ShortV2Props }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { S, starts, ends, kinds } = sceneTimes(p);
  if (!S.length) return null;
  const i = activeIndex(frame, starts);
  const local = (k: number) => frame - starts[k];
  const dur = (k: number) => Math.max(1, ends[k] - starts[k]);
  const raw = i === 0 ? 1 : clamp01((frame - (starts[i] - PRE)) / MORPH);
  let g = geoOf(kinds[i], S[i], local(i));
  if (i > 0 && raw < 1) g = mixGeo(geoOf(kinds[i - 1], S[i - 1], local(i - 1)), g, morphEase(raw));
  let alpha = 1;
  if (i === 0 && kinds[0] === "hookIcon") {
    // açılış ikonu yaylanarak belirir (eski IconBadge girişi)
    const e = spring({ frame: frame - 2, fps: FPS, config: { damping: 11, mass: 0.7 } });
    const sc = 0.6 + 0.4 * e;
    g = { ...g, x: g.x + (g.w * (1 - sc)) / 2, y: g.y + (g.h * (1 - sc)) / 2, w: g.w * sc, h: g.h * sc, r: g.r * sc };
    alpha = Math.min(1, e * 1.5);
  }
  // İçerik geçişi: açılış fotoğrafı kart olana dek görünür kalır, sonra yeni içeriğe geçer
  const b = starts[i];
  const hookPrev = i === 1 && kinds[0] === "hookPhoto";
  const win: [number, number] = hookPrev ? [b + 2, b + 12] : [b - 2, b + 8];
  const prevOp = i > 0 ? interpolate(frame, win, [1, 0], clamp) : 0;
  const curOp = i > 0 ? interpolate(frame, [win[0] + 2, win[1] + 2], [0, 1], clamp) : 1;
  const veil = hookPrev ? 1 - clamp01(raw * 1.6) : 1;
  return (
    <>
      <div style={{ position: "absolute", left: g.x, top: g.y, width: g.w, height: g.h, opacity: alpha }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: g.r,
            background: "rgba(255,255,255,0.07)",
            border: "2px solid rgba(255,255,255,0.14)",
            boxShadow: `0 30px 80px rgba(0,0,0,0.42), 0 0 100px ${p.accent}22`,
            opacity: g.chrome * (1 - g.acc),
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: g.r,
            background: `radial-gradient(circle at 35% 30%, ${p.accent}55, ${p.accent}18 60%, transparent 72%)`,
            border: `4px solid ${p.accent}`,
            boxShadow: `0 0 80px ${p.accent}66, inset 0 0 40px ${p.accent}33`,
            opacity: g.chrome * g.acc,
          }}
        />
        <div style={{ position: "absolute", inset: 0, borderRadius: g.r, overflow: "hidden" }}>
          {prevOp > 0 ? (
            <div style={{ position: "absolute", inset: 0, opacity: prevOp }}>
              <CardContent k={kinds[i - 1]} s={S[i - 1]} p={p} local={local(i - 1)} dur={dur(i - 1)} veil={veil} />
            </div>
          ) : null}
          <div style={{ position: "absolute", inset: 0, opacity: curOp }}>
            <CardContent k={kinds[i]} s={S[i]} p={p} local={local(i)} dur={dur(i)} />
          </div>
        </div>
      </div>
      {i > 0 ? <Satellite k={kinds[i - 1]} s={S[i - 1]} p={p} local={local(i - 1)} opacity={prevOp} /> : null}
      <Satellite k={kinds[i]} s={S[i]} p={p} local={local(i)} opacity={curOp} />
    </>
  );
};

// Başlık satırı yerinde kalır: numara/ikon kutusu sayaç gibi döner, yazı yükselerek değişir
const HeadingRail: React.FC<{ p: ShortV2Props }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { S, starts, kinds } = sceneTimes(p);
  const i = activeIndex(frame, starts);
  if (i === 0) return null;
  const isSub = kinds[i] === "subscribe";
  const show = isSub ? i - 1 : i;
  if (show < 1) return null;
  const first = i === 1;
  // İlk sahnede açılış başlığı küçülüp yukarı yerleşirken (~sınır+9 kare) üstüne binmesin diye gecikmeli
  const t0 = first ? starts[i] + 4 : starts[i] - PRE;
  const q = riseEase(clamp01((frame - t0) / 12));
  const railOp = isSub ? 1 - q : 1;
  if (railOp <= 0) return null;
  const prev = !first && !isSub ? i - 1 : -1;
  const badge = (k: number) =>
    S[k].icon && kinds[k] !== "icon" ? (
      <Icon name={S[k].icon as string} size={40} color={p.accent} strokeWidth={2.2} />
    ) : (
      String(k).padStart(2, "0")
    );
  const slot = (y: number, op: number, child: React.ReactNode) => (
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", transform: `translateY(${y}px)`, opacity: op }}>
      {child}
    </div>
  );
  const words = (S[show].heading || "").split(" ");
  const fresh = !isSub;
  return (
    <div style={{ position: "absolute", top: 365, left: 60, right: 60, height: 76, fontFamily: FONT, opacity: railOp }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 76,
          height: 76,
          borderRadius: 22,
          background: "rgba(255,255,255,0.08)",
          border: "2px solid rgba(255,255,255,0.16)",
          color: p.accent,
          fontWeight: 900,
          fontSize: 34,
          overflow: "hidden",
          transform: `scale(${first ? 0.6 + 0.4 * q : 1})`,
          opacity: first ? q : 1,
        }}
      >
        {prev > 0 && q < 1 ? slot(-q * 76, 1 - q, badge(prev)) : null}
        {slot(fresh && !first ? (1 - q) * 76 : 0, fresh && !first ? q : 1, badge(show))}
      </div>
      <div style={{ position: "absolute", left: 98, top: 0, right: 0, height: 76 }}>
        {prev > 0 && q < 1 ? (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", transform: `translateY(${-q * 34}px)`, opacity: 1 - q, color: INK, fontWeight: 800, fontSize: 56, letterSpacing: -0.5, whiteSpace: "nowrap" }}>
            {S[prev].heading}
          </div>
        ) : null}
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", color: INK, fontWeight: 800, fontSize: 56, letterSpacing: -0.5, whiteSpace: "nowrap" }}>
          {words.map((w, j) => {
            const e = fresh ? riseEase(clamp01((frame - t0 - 3 - j * 1.5) / 10)) : 1;
            return (
              <span key={j} style={{ display: "inline-block", marginRight: "0.26em", transform: `translateY(${(1 - e) * 40}px)`, opacity: e }}>
                {w}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/* ---------- Film greni ----------
   cinematic-skill'in yöntemi: yarım çözünürlüklü gren (256 px karo ekranda 512 px) ve desen her 2
   karede bir değişir. Tam çözünürlükte her kare değişen gren hem "dijital parazit" gibi görünür hem
   de dosyayı çok büyütür. Karolar build.py'de numpy ile üretilir: beyaz/siyah benekler, saydamlık =
   gürültü şiddeti (0,25 ölçekli); katman opaklığı = amount / 0,25. */
const GRAIN_TILE = 512;
const Grain: React.FC<{ amount?: number }> = ({ amount }) => {
  const frame = useCurrentFrame();
  if (!amount) return null;
  const k = Math.floor(frame / 2);
  const rnd = (n: number) => {
    const x = Math.sin(k * 127.1 + n * 311.7) * 43758.5453;
    return x - Math.floor(x);
  };
  const src = staticFile(`fx/grain-${(k * 3) % 4}.png`);
  const ox = Math.floor(rnd(1) * GRAIN_TILE);
  const oy = Math.floor(rnd(2) * GRAIN_TILE);
  const tiles: [number, number][] = [];
  for (let y = 0; y < 5; y++) for (let x = 0; x < 4; x++) tiles.push([x, y]);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden", opacity: Math.min(1, amount / 0.25) }}>
      <div style={{ position: "absolute", left: -ox, top: -oy, width: 4 * GRAIN_TILE, height: 5 * GRAIN_TILE }}>
        {tiles.map(([x, y]) => (
          <Img
            key={`${x}-${y}`}
            src={src}
            style={{ position: "absolute", left: x * GRAIN_TILE, top: y * GRAIN_TILE, width: GRAIN_TILE, height: GRAIN_TILE }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};

/* ---------- Altyazı ---------- */

const Caption: React.FC<{ chunk?: Chunk; accent: string; top: number }> = ({ chunk, accent, top }) => {
  const frame = useCurrentFrame();
  if (!chunk) return null;
  const local = frame - Math.round(chunk.start * FPS);
  const pop = spring({ frame: local, fps: FPS, config: { damping: 14, mass: 0.45 } });
  const words = chunk.text.split(" ");
  // Etkin kelime: gerçek kelime zamanları varsa onlara göre, yoksa parça süresine orantılı
  const starts =
    chunk.words && chunk.words.length === words.length
      ? chunk.words.map((t) => Math.round(t * FPS))
      : words.map((_, i) => Math.round(chunk.start * FPS + (i * Math.max(1, (chunk.end - chunk.start) * FPS)) / words.length));
  let active = 0;
  starts.forEach((f, i) => {
    if (frame >= f) active = i;
  });
  const wordPop = (i: number) => (i === active ? 1 + 0.07 * Math.max(0, 1 - (frame - starts[i]) / 5) : 1);
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
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: "0.24em",
              color: i === active ? accent : INK,
              transform: `scale(${wordPop(i)})`,
            }}
          >
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
  const flash = interpolate(frame, [0, 5], [0.25, 0], clamp);
  const fadeOut = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <Background accent={p.accent} icon={p.categoryIcon} />
      <Stage p={p} />
      <TopBar p={p} sceneIdx={sceneIdx} sec={sec} />
      <TitleBlock p={p} />
      <HeadingRail p={p} />
      <Caption chunk={chunk} accent={p.accent} top={sceneIdx === 0 ? 1290 : 1225} />
      <AbsoluteFill style={{ background: "#ffffff", opacity: flash, pointerEvents: "none" }} />
      <Grain amount={p.grain} />
      {p.audio ? <Audio src={staticFile(p.audio)} /> : null}
    </AbsoluteFill>
  );
};
