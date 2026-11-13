import React, { useMemo } from "react";
import { Easing, interpolate, spring, useCurrentFrame } from "remotion";
import { geoContains, geoGraticule10, geoMercator, geoOrthographic, geoPath } from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import world50 from "world-atlas/countries-50m.json";
import world110 from "world-atlas/countries-110m.json";
import { FONT, FPS, INK, MUTED, type MapSpec } from "./types";

type Countries = FeatureCollection<Geometry, { name: string }>;

const toFeatures = (t: unknown): Countries => {
  const topo = t as Topology<{ countries: GeometryCollection<{ name: string }> }>;
  return feature(topo, topo.objects.countries) as unknown as Countries;
};

// Harita verisi: Natural Earth (kamu malı), world-atlas paketi (ISC)
const C50 = toFeatures(world50);
const C110 = toFeatures(world110);
const TURKEY = C50.features.find((f) => String(f.id) === "792") as Feature<Geometry>;

const inTurkey = (lat: number, lon: number) => lat > 35.5 && lat < 42.4 && lon > 25.5 && lon < 45.0;

const W = 960;
const H = 700;

const Pin: React.FC<{ x: number; y: number; accent: string; local: number }> = ({ x, y, accent, local }) => {
  const pop = spring({ frame: local, fps: FPS, config: { damping: 10, mass: 0.6 } });
  const rings = [0, 20, 40].map((d) => ((local + d) % 60) / 60);
  return (
    <g transform={`translate(${x},${y})`}>
      {rings.map((r, i) => (
        <circle key={i} r={10 + r * 70} fill="none" stroke={accent} strokeWidth={4} opacity={(1 - r) * 0.8 * pop} />
      ))}
      <circle r={20 * pop} fill={accent} stroke="#fff" strokeWidth={6} />
    </g>
  );
};

const Label: React.FC<{ x: number; y: number; place: string; label?: string; accent: string; local: number }> = ({
  x,
  y,
  place,
  label,
  accent,
  local,
}) => {
  const s = spring({ frame: local - 6, fps: FPS, config: { damping: 14 } });
  const left = Math.min(Math.max(x - 230, 20), W - 480);
  const top = y > H * 0.55 ? y - 210 : y + 50;
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width: 460,
        padding: "22px 28px",
        borderRadius: 26,
        background: "rgba(6,10,20,0.82)",
        border: `3px solid ${accent}`,
        fontFamily: FONT,
        opacity: s,
        transform: `translateY(${(1 - s) * 24}px)`,
        boxShadow: "0 18px 50px rgba(0,0,0,0.45)",
      }}
    >
      <div style={{ color: INK, fontWeight: 900, fontSize: 50, lineHeight: 1.05 }}>{place}</div>
      {label ? (
        <div style={{ color: MUTED, fontWeight: 700, fontSize: 32, marginTop: 8, lineHeight: 1.2 }}>{label}</div>
      ) : null}
    </div>
  );
};

/** Türkiye haritası (şehir pini) ya da dönen dünya küresi (ülke vurgusu + pin). */
export const MapCard: React.FC<{ spec: MapSpec; accent: string; local: number; duration: number }> = ({
  spec,
  accent,
  local,
  duration,
}) => {
  const scope = spec.scope ?? (inTurkey(spec.lat, spec.lon) ? "turkey" : "world");
  const zoomFrames = Math.min(75, Math.max(30, duration * 0.4));
  const p = interpolate(local, [0, zoomFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  const turkey = useMemo(() => {
    if (scope !== "turkey") return null;
    const proj = geoMercator().fitExtent(
      [
        [60, 120],
        [W - 60, H - 120],
      ],
      TURKEY,
    );
    proj.clipExtent([
      [-400, -400],
      [W + 400, H + 400],
    ]);
    const path = geoPath(proj);
    const others = C50.features
      .filter((f) => String(f.id) !== "792")
      .map((f) => path(f))
      .filter((d): d is string => !!d && d.length > 0);
    const tr = path(TURKEY) ?? "";
    const pt = proj([spec.lon, spec.lat]) ?? [W / 2, H / 2];
    return { others, tr, pt };
  }, [scope, spec.lat, spec.lon]);

  const target = useMemo(() => C110.features.find((f) => geoContains(f, [spec.lon, spec.lat])), [spec.lat, spec.lon]);

  let svg: React.ReactNode;
  let pin: [number, number] = [W / 2, H / 2];
  if (turkey) {
    const k = interpolate(p, [0, 1], [1, 1.45]);
    const fx = interpolate(p, [0, 1], [W / 2, turkey.pt[0]]);
    const fy = interpolate(p, [0, 1], [H / 2, turkey.pt[1]]);
    const tf = `translate(${W / 2},${H / 2}) scale(${k}) translate(${-fx},${-fy})`;
    pin = [W / 2 + (turkey.pt[0] - fx) * k, H / 2 + (turkey.pt[1] - fy) * k];
    svg = (
      <g transform={tf}>
        {turkey.others.map((d, i) => (
          <path key={i} d={d} fill="#1b2335" stroke="#2c3850" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        ))}
        <path d={turkey.tr} fill={`${accent}38`} stroke={accent} strokeWidth={4} vectorEffect="non-scaling-stroke" />
      </g>
    );
  } else {
    const R0 = 300;
    const R = interpolate(p, [0.7, 1], [R0, R0 * 1.35], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const lon = interpolate(p, [0, 1], [spec.lon - 80, spec.lon]);
    const lat = interpolate(p, [0, 1], [spec.lat - 25, spec.lat]);
    const proj = geoOrthographic()
      .scale(R)
      .translate([W / 2, H / 2])
      .rotate([-lon, -lat]);
    const path = geoPath(proj);
    pin = proj([spec.lon, spec.lat]) ?? [W / 2, H / 2];
    svg = (
      <g>
        <circle cx={W / 2} cy={H / 2} r={R + 26} fill={`${accent}14`} />
        <path d={path({ type: "Sphere" }) ?? ""} fill="#0d1a33" stroke={`${accent}88`} strokeWidth={3} />
        <path d={path(geoGraticule10()) ?? ""} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={1.2} />
        {C110.features.map((f, i) => (
          <path
            key={i}
            d={path(f) ?? ""}
            fill={f === target ? `${accent}aa` : "#2a3550"}
            stroke={f === target ? accent : "#3a4766"}
            strokeWidth={f === target ? 3 : 1}
          />
        ))}
      </g>
    );
  }

  const pinLocal = local - Math.round(zoomFrames * 0.6);
  return (
    <div style={{ position: "relative", width: W, height: H, borderRadius: 40, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(90% 90% at 50% 40%, #0f1830 0%, #070b16 100%)",
        }}
      />
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {svg}
        {pinLocal > 0 ? <Pin x={pin[0]} y={pin[1]} accent={accent} local={pinLocal} /> : null}
      </svg>
      {pinLocal > 0 ? (
        <Label x={pin[0]} y={pin[1]} place={spec.place} label={spec.label} accent={accent} local={pinLocal} />
      ) : null}
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: 40,
          border: "2px solid rgba(255,255,255,0.12)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
};
