// 3D harita sahnesi: Türkiye içi yerlerde kalın Türkiye bloğu (il sınırları, büyük şehirler, yükselen
// il, düşen iğne); yurt dışında ülkeleri boyanmış dünya küresi (Türkiye'den hedefe dönüş ve uçuş izi).
// Kamera her karede tek bir fonksiyondan (pose) hesaplanır; aynı hesapla şehir adları 3D dünyadaki
// noktalara 2D yazı olarak yerleşir. Veri: Natural Earth (kamu malı), world-atlas paketi.
import React, { useLayoutEffect, useMemo } from "react";
import { Easing, interpolate, spring } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { geoContains, geoEquirectangular, geoMercator, geoPath } from "d3-geo";
import type { Feature, FeatureCollection, Geometry, MultiPolygon, Polygon } from "geojson";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import world50 from "world-atlas/countries-50m.json";
import world110 from "world-atlas/countries-110m.json";
import iller from "./data/tr-iller.json";
import { FONT, FPS, type MapSpec } from "../v2/types";

type Countries = FeatureCollection<Geometry, { name: string }>;
const toFeatures = (t: unknown): Countries => {
  const topo = t as Topology<{ countries: GeometryCollection<{ name: string }> }>;
  return feature(topo, topo.objects.countries) as unknown as Countries;
};
const C50 = toFeatures(world50);
const C110 = toFeatures(world110);
const TURKEY = C50.features.find((f) => String(f.id) === "792") as Feature<Geometry>;
type Il = { ad: string; kod: string; polys: number[][][][] };
const ILLER = (iller as unknown as { iller: Il[] }).iller;

export const inTurkey = (lat: number, lon: number) => lat > 35.5 && lat < 42.4 && lon > 25.5 && lon < 45.0;

// Sahne zamanlaması (kare): kamera uçuşu, iğnenin düşüşü ve yere değişi. audio_fx.py aynı formülü kullanır.
export const map3dTiming = (durFrames: number) => {
  const flight = Math.round(Math.min(90, Math.max(45, durFrames * 0.45)));
  const pinAt = flight - 14;
  return { flight, pinAt, land: pinAt + 6 };
};

const BG = "#070b16";
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
const ease = Easing.inOut(Easing.cubic);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

type Pose = { pos: THREE.Vector3; look: THREE.Vector3; fov: number };

const CameraRig: React.FC<{ pose: Pose }> = ({ pose }) => {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  useLayoutEffect(() => {
    camera.fov = pose.fov;
    camera.position.copy(pose.pos);
    camera.lookAt(pose.look);
    camera.updateProjectionMatrix();
  });
  return null;
};

// 3D noktanın ekrandaki yeri (px); kamera arkasındaysa null
const project = (p: THREE.Vector3, pose: Pose, w: number, h: number) => {
  const cam = new THREE.PerspectiveCamera(pose.fov, w / h, 0.1, 400);
  cam.position.copy(pose.pos);
  cam.lookAt(pose.look);
  cam.updateMatrixWorld();
  cam.updateProjectionMatrix();
  const v = p.clone().project(cam);
  if (v.z > 1) return null;
  return { x: ((v.x + 1) / 2) * w, y: ((1 - v.y) / 2) * h };
};

const Label: React.FC<{ x: number; y: number; title: string; sub?: string; accent: string; op: number; big?: boolean }> = ({
  x,
  y,
  title,
  sub,
  accent,
  op,
  big,
}) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      transform: "translate(-50%, 0)",
      textAlign: "center",
      fontFamily: FONT,
      opacity: op,
      whiteSpace: "nowrap",
      pointerEvents: "none",
    }}
  >
    <div
      style={{
        color: "#fff",
        fontWeight: 900,
        fontSize: big ? 84 : 34,
        letterSpacing: big ? 2 : 1,
        textShadow: "0 4px 24px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)",
      }}
    >
      {title}
    </div>
    {sub ? (
      <div style={{ color: accent, fontWeight: 800, fontSize: big ? 38 : 24, marginTop: 4, textShadow: "0 3px 16px rgba(0,0,0,0.85)" }}>
        {sub}
      </div>
    ) : null}
  </div>
);

/* ------------------------------------------------------------------ Türkiye */

const proj = geoMercator().center([35.2, 39]).scale(60).translate([0, 0]);
const P = (lon: number, lat: number) => proj([lon, lat]) as [number, number];
const TOP = 0.51; // blok üst yüzeyi (derinlik 0.45 + pah 0.06)

const shapesOf = (polys: number[][][][]): THREE.Shape[] =>
  polys.map((rings) => {
    const pts = (ring: number[][]) => ring.map(([lon, lat]) => {
      const [x, y] = P(lon, lat);
      return new THREE.Vector2(x, -y);
    });
    const s = new THREE.Shape(pts(rings[0]));
    s.holes = rings.slice(1).map((r) => new THREE.Path(pts(r)));
    return s;
  });

const polysOf = (g: Geometry): number[][][][] =>
  g.type === "Polygon" ? [(g as Polygon).coordinates] : g.type === "MultiPolygon" ? (g as MultiPolygon).coordinates : [];

const CITIES: [string, number, number][] = [
  ["İstanbul", 41.01, 28.98], ["Ankara", 39.93, 32.86], ["İzmir", 38.42, 27.14], ["Bursa", 40.19, 29.06],
  ["Antalya", 36.9, 30.7], ["Konya", 37.87, 32.48], ["Adana", 37.0, 35.32], ["Gaziantep", 37.07, 37.38],
  ["Diyarbakır", 37.91, 40.24], ["Kayseri", 38.73, 35.48], ["Samsun", 41.29, 36.33], ["Trabzon", 41.0, 39.72],
  ["Erzurum", 39.9, 41.27], ["Van", 38.5, 43.38],
];

const extrude = (shapes: THREE.Shape[], depth: number, bevel: boolean) =>
  new THREE.ExtrudeGeometry(shapes, { depth, bevelEnabled: bevel, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 2, curveSegments: 1 });

const TurkeyScene: React.FC<{ spec: MapSpec; accent: string; local: number; dur: number; w: number; h: number }> = ({
  spec,
  accent,
  local,
  dur,
  w,
  h,
}) => {
  const { flight, pinAt } = map3dTiming(dur);
  const geo = useMemo(() => {
    const near = C110.features.filter((f) => {
      if (String(f.id) === "792" || !f.geometry) return false;
      const s = JSON.stringify(f.geometry).match(/-?\d+\.?\d*,-?\d+\.?\d*/g) ?? [];
      return s.some((c) => {
        const [lon, lat] = c.split(",").map(Number);
        return lon > 17 && lon < 55 && lat > 28 && lat < 50;
      });
    });
    const target = ILLER.find((il) => geoContains({ type: "Feature", properties: {}, geometry: { type: "MultiPolygon", coordinates: il.polys } } as Feature, [spec.lon, spec.lat]));
    const lines: number[] = [];
    for (const il of ILLER)
      for (const poly of il.polys)
        for (const ring of poly)
          for (let i = 0; i + 1 < ring.length; i++) {
            const [x0, z0] = P(ring[i][0], ring[i][1]);
            const [x1, z1] = P(ring[i + 1][0], ring[i + 1][1]);
            lines.push(x0, TOP + 0.012, z0, x1, TOP + 0.012, z1);
          }
    const border = new THREE.BufferGeometry();
    border.setAttribute("position", new THREE.Float32BufferAttribute(lines, 3));
    return {
      turkey: extrude(shapesOf(polysOf(TURKEY.geometry)), 0.45, true),
      others: extrude(near.flatMap((f) => shapesOf(polysOf(f.geometry))), 0.12, false),
      province: target ? extrude(shapesOf(target.polys), 0.5, true) : null,
      provinceName: target?.ad,
      border,
    };
  }, [spec.lat, spec.lon]);
  const [tx, tz] = P(spec.lon, spec.lat);
  const target = new THREE.Vector3(tx, TOP, tz);
  const k = ease(clamp01(local / flight));
  const orbit = -0.25 + 0.37 * k + Math.max(0, local - flight) * 0.0015;
  const look = new THREE.Vector3().lerpVectors(new THREE.Vector3(0, 0, 1), target, k);
  const dist = lerp(44, 16, k);
  const tilt = lerp(1.05, 0.62, k);
  const pose: Pose = {
    pos: new THREE.Vector3(look.x + Math.sin(orbit) * Math.cos(tilt) * dist, look.y + Math.sin(tilt) * dist, look.z + Math.cos(orbit) * Math.cos(tilt) * dist),
    look,
    fov: 40,
  };
  const drop = spring({ frame: local - pinAt, fps: FPS, config: { damping: 12, mass: 0.8 } });
  const rise = spring({ frame: local - pinAt - 4, fps: FPS, config: { damping: 14 } });
  const ringK = (((local - pinAt - 8) % 36) + 36) % 36 / 36;
  const color = new THREE.Color(accent);
  // Blok altın; kategori rengi sıcaksa (sarı/turuncu) hedef il seçilsin diye blok soğuk çelik mavisi
  const hsl = { h: 0, s: 0, l: 0 };
  color.getHSL(hsl);
  const slab = new THREE.Color(hsl.h > 0.05 && hsl.h < 0.19 ? "#8fa3c4" : "#cfa24a");
  const pinLabel = project(new THREE.Vector3(tx, TOP, tz), pose, w, h);
  const labelOp = clamp01((local - pinAt - 6) / 10);
  return (
    <>
      <ThreeCanvas width={w} height={h} camera={{ fov: 40, near: 0.1, far: 300 }} shadows>
        <color attach="background" args={[BG]} />
        <fog attach="fog" args={[BG, 25, 85]} />
        <ambientLight intensity={0.55} />
        <hemisphereLight args={["#9fb8ff", "#1a1206", 0.6]} />
        <directionalLight
          position={[-12, 22, -8]}
          intensity={2.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-bias={-0.0002}
          shadow-normalBias={0.04}
          shadow-camera-left={-30}
          shadow-camera-right={30}
          shadow-camera-top={30}
          shadow-camera-bottom={-30}
          shadow-camera-near={1}
          shadow-camera-far={80}
        />
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
          <planeGeometry args={[400, 400]} />
          <meshStandardMaterial color="#0b1528" roughness={1} />
        </mesh>
        <group rotation={[-Math.PI / 2, 0, 0]}>
          <mesh geometry={geo.others} receiveShadow>
            <meshStandardMaterial color="#1f2a3d" roughness={0.9} metalness={0.05} />
          </mesh>
          <mesh geometry={geo.turkey} castShadow receiveShadow>
            <meshStandardMaterial color={slab} roughness={0.55} metalness={0.12} />
          </mesh>
          {geo.province ? (
            <mesh geometry={geo.province} scale={[1, 1, 1 + 0.9 * rise]} castShadow>
              <meshStandardMaterial color={color} roughness={0.4} metalness={0.15} emissive={color} emissiveIntensity={0.25 * rise} />
            </mesh>
          ) : null}
        </group>
        <lineSegments geometry={geo.border}>
          <lineBasicMaterial color="#000000" transparent opacity={0.28} depthWrite={false} />
        </lineSegments>
        {CITIES.map(([n, lat, lon]) => {
          const [x, z] = P(lon, lat);
          return (
            <mesh key={n} position={[x, TOP + 0.05, z]}>
              <sphereGeometry args={[0.08, 12, 8]} />
              <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={0.3} />
            </mesh>
          );
        })}
        <group position={[tx, 0, tz]}>
          <group position={[0, TOP + 0.45 * rise + (1 - drop) * 7, 0]} visible={local >= pinAt}>
            <mesh position={[0, 0.7, 0]} castShadow>
              <cylinderGeometry args={[0.07, 0.02, 1.4, 12]} />
              <meshStandardMaterial color="#ffffff" roughness={0.4} />
            </mesh>
            <mesh position={[0, 1.55, 0]} castShadow>
              <sphereGeometry args={[0.32, 24, 16]} />
              <meshStandardMaterial color="#ff5e62" roughness={0.35} emissive="#ff5e62" emissiveIntensity={0.35} />
            </mesh>
          </group>
          {local > pinAt + 8 ? (
            <mesh position={[0, TOP + 0.47 * rise + 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={0.4 + ringK * 2.2}>
              <ringGeometry args={[0.8, 1, 48]} />
              <meshBasicMaterial color="#ff5e62" transparent opacity={(1 - ringK) * 0.8} depthWrite={false} />
            </mesh>
          ) : null}
        </group>
        <CameraRig pose={pose} />
      </ThreeCanvas>
      {CITIES.map(([n, lat, lon]) => {
        const [x, z] = P(lon, lat);
        const s = project(new THREE.Vector3(x, TOP + 0.1, z), pose, w, h);
        const near = Math.hypot(lat - spec.lat, lon - spec.lon) < 0.6;
        const op = near ? 0 : 0.9 * (1 - k * 0.75);
        return s && op > 0.02 ? <Label key={n} x={s.x} y={s.y + 12} title={n} accent={accent} op={op} /> : null;
      })}
      {pinLabel ? (
        <Label
          x={pinLabel.x}
          y={pinLabel.y + 70}
          title={spec.place.toLocaleUpperCase("tr")}
          sub={spec.label ?? (geo.provinceName && geo.provinceName !== spec.place ? geo.provinceName : undefined)}
          accent={accent}
          op={labelOp}
          big
        />
      ) : null}
    </>
  );
};

/* ------------------------------------------------------------------ Dünya küresi */

const R = 5;
const TR_LAT = 39;
const TR_LON = 35;
const deg = Math.PI / 180;
const unit = (lat: number, lon: number) =>
  new THREE.Vector3(Math.cos(lat * deg) * Math.cos(lon * deg), Math.sin(lat * deg), -Math.cos(lat * deg) * Math.sin(lon * deg));

const earthTexture = (accent: string, targetId: string | null) => {
  const W = 4096;
  const H = 2048;
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d") as CanvasRenderingContext2D;
  const path = geoPath(geoEquirectangular().scale(W / (2 * Math.PI)).translate([W / 2, H / 2]), ctx);
  ctx.fillStyle = "#0b1a36";
  ctx.fillRect(0, 0, W, H);
  for (const f of C50.features) {
    const id = String(f.id);
    ctx.beginPath();
    path(f);
    ctx.fillStyle = id === targetId ? accent : id === "792" ? "#d1a23a" : "#33435f";
    ctx.fill();
    ctx.strokeStyle = "rgba(175,195,235,0.5)";
    ctx.lineWidth = 1.6;
    ctx.stroke();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return tex;
};

const GlobeScene: React.FC<{ spec: MapSpec; accent: string; local: number; dur: number; w: number; h: number }> = ({
  spec,
  accent,
  local,
  dur,
  w,
  h,
}) => {
  const { flight, pinAt } = map3dTiming(dur);
  const targetId = useMemo(() => {
    const f = C50.features.find((c) => c.geometry && geoContains(c as Feature, [spec.lon, spec.lat]));
    return f ? String(f.id) : null;
  }, [spec.lat, spec.lon]);
  const tex = useMemo(() => earthTexture(accent, targetId), [accent, targetId]);
  const k = ease(clamp01(local / flight));
  // en kısa yoldan dön; bitişte hedef ekranın biraz altında kalsın (küre eğriliği görünsün)
  let dLon = spec.lon - TR_LON;
  if (dLon > 180) dLon -= 360;
  if (dLon < -180) dLon += 360;
  const vLat = lerp(TR_LAT + 8, spec.lat + 10, k);
  const vLon = TR_LON + dLon * k + Math.max(0, local - flight) * 0.02;
  const rot = new THREE.Euler(vLat * deg, -Math.PI / 2 - vLon * deg, 0);
  const dist = lerp(29, 11.5, k);
  const pose: Pose = { pos: new THREE.Vector3(0, 0, dist), look: new THREE.Vector3(0, 0, 0), fov: 40 };
  const tgt = unit(spec.lat, spec.lon);
  const trv = unit(TR_LAT, TR_LON);
  const arcN = 40;
  const arcK = clamp01(local / (flight * 0.95));
  const arc = Array.from({ length: arcN }, (_, i) => {
    const t = i / (arcN - 1);
    const v = new THREE.Vector3().copy(trv).lerp(tgt, t).normalize();
    return v.multiplyScalar(R + 0.04 + 0.9 * Math.sin(Math.PI * t) * Math.min(1, tgt.angleTo(trv) * 1.2));
  });
  const world = (v: THREE.Vector3) => v.clone().applyEuler(rot);
  const tScreen = project(world(tgt.clone().multiplyScalar(R)), pose, w, h);
  const trScreen = project(world(trv.clone().multiplyScalar(R)), pose, w, h);
  const ringK = (((local - pinAt - 4) % 36) + 36) % 36 / 36;
  const dot = spring({ frame: local - pinAt, fps: FPS, config: { damping: 12 } });
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), tgt);
  return (
    <>
      <ThreeCanvas width={w} height={h} camera={{ fov: 40, near: 0.1, far: 300 }}>
        <color attach="background" args={[BG]} />
        <ambientLight intensity={0.38} />
        <directionalLight position={[-10, 7, 7]} intensity={2.4} />
        <directionalLight position={[8, -3, 4]} intensity={0.35} color="#5b8cff" />
        <group rotation={rot}>
          <mesh>
            <sphereGeometry args={[R, 128, 64]} />
            <meshStandardMaterial map={tex} roughness={0.85} metalness={0.05} />
          </mesh>
          {arc.map((p, i) =>
            i / (arcN - 1) <= arcK ? (
              <mesh key={i} position={p}>
                <sphereGeometry args={[0.045, 8, 6]} />
                <meshBasicMaterial color={accent} />
              </mesh>
            ) : null,
          )}
          <group position={tgt.clone().multiplyScalar(R + 0.01)} quaternion={q}>
            <mesh scale={0.6 + 0.4 * dot} visible={local >= pinAt}>
              <sphereGeometry args={[0.13, 16, 12]} />
              <meshBasicMaterial color="#ff5e62" />
            </mesh>
            {local > pinAt + 4 ? (
              <mesh scale={0.3 + ringK * 1.2}>
                <ringGeometry args={[0.5, 0.62, 48]} />
                <meshBasicMaterial color="#ff5e62" transparent opacity={(1 - ringK) * 0.85} side={THREE.DoubleSide} depthWrite={false} />
              </mesh>
            ) : null}
          </group>
        </group>
        <mesh>
          <sphereGeometry args={[R * 1.1, 64, 32]} />
          <meshBasicMaterial color="#4f7cff" transparent opacity={0.13} side={THREE.BackSide} />
        </mesh>
        <CameraRig pose={pose} />
      </ThreeCanvas>
      {trScreen ? <Label x={trScreen.x} y={trScreen.y + 18} title="TÜRKİYE" accent={accent} op={0.9 * (1 - clamp01(k * 3))} /> : null}
      {tScreen ? (
        <Label
          x={tScreen.x}
          y={tScreen.y + 60}
          title={spec.place.toLocaleUpperCase("tr")}
          sub={spec.label}
          accent={accent}
          op={clamp01((local - pinAt - 4) / 10)}
          big
        />
      ) : null}
    </>
  );
};

/* ------------------------------------------------------------------ Dışa açılan bileşen */

export const Map3D: React.FC<{ spec: MapSpec; accent: string; local: number; dur: number; width: number; height: number }> = ({
  spec,
  accent,
  local,
  dur,
  width,
  height,
}) => {
  const scope = spec.scope ?? (inTurkey(spec.lat, spec.lon) ? "turkey" : "world");
  const Scene = scope === "turkey" ? TurkeyScene : GlobeScene;
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <Scene spec={spec} accent={accent} local={local} dur={dur} w={width} h={height} />
      {/* başlık satırı ve altyazı okunabilsin */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 560, background: "linear-gradient(180deg, rgba(4,7,15,0.85) 0%, rgba(4,7,15,0.55) 55%, rgba(4,7,15,0) 100%)" }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 760, background: "linear-gradient(0deg, rgba(4,7,15,0.8) 0%, rgba(4,7,15,0.4) 50%, rgba(4,7,15,0) 100%)" }} />
    </div>
  );
};
