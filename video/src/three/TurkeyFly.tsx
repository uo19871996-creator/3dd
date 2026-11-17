// DENEME: 3D haber grafiği. Kabartmalı Türkiye, kamera bir şehre uçar, iğne düşer.
// Canlı akışa BAĞLI DEĞİL: Root.tsx'te kayıtlı değil, bu yüzden videolara paketlenmez.
// Denemek için Root.tsx'e geçici olarak ekle:
//   <Composition id="TurkeyFly" component={TurkeyFly} durationInFrames={150} fps={30} width={1080} height={1920} />
// ve: npx remotion render src/index.ts TurkeyFly out.mp4 --gl=swangle
// Harita verisi: Natural Earth (kamu malı), world-atlas paketi. 3D: three.js + @remotion/three.
import React, { useLayoutEffect, useMemo } from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { geoMercator } from "d3-geo";
import type { FeatureCollection, Geometry, MultiPolygon, Polygon } from "geojson";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import world50 from "world-atlas/countries-50m.json";
import world110 from "world-atlas/countries-110m.json";
import "@fontsource/montserrat/800.css";
import "@fontsource/montserrat/900.css";
import { FONT } from "../v2/types";

type Countries = FeatureCollection<Geometry, { name: string }>;
const toFeatures = (t: unknown): Countries => {
  const topo = t as Topology<{ countries: GeometryCollection<{ name: string }> }>;
  return feature(topo, topo.objects.countries) as unknown as Countries;
};

const ACCENT = "#ffc233";
const PIN = "#ff5e62";
const BG = "#070b16";
const proj = geoMercator().center([35.2, 39]).scale(60).translate([0, 0]);

const toShapes = (g: Geometry): THREE.Shape[] => {
  const polys: Polygon["coordinates"][] =
    g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? (g as MultiPolygon).coordinates : [];
  return polys.map((rings) => {
    const pts = (ring: number[][]) =>
      ring.map(([lon, lat]) => {
        const [x, y] = proj([lon, lat]) as [number, number];
        return new THREE.Vector2(x, -y); // kuzey +y; yere yatırınca -z olur
      });
    const shape = new THREE.Shape(pts(rings[0]));
    shape.holes = rings.slice(1).map((r) => new THREE.Path(pts(r)));
    return shape;
  });
};

const Land: React.FC = () => {
  const { turkey, others } = useMemo(() => {
    const c50 = toFeatures(world50);
    const c110 = toFeatures(world110);
    const tr = c50.features.find((f) => String(f.id) === "792")!;
    const near = c110.features.filter((f) => {
      if (String(f.id) === "792" || !f.geometry) return false;
      const [x0, y0, x1, y1] = [17, 28, 55, 50];
      const coords = JSON.stringify(f.geometry).match(/-?\d+\.?\d*,-?\d+\.?\d*/g) ?? [];
      return coords.some((c) => {
        const [lon, lat] = c.split(",").map(Number);
        return lon > x0 && lon < x1 && lat > y0 && lat < y1;
      });
    });
    const ext = (shapes: THREE.Shape[], depth: number, bevel: boolean) =>
      new THREE.ExtrudeGeometry(shapes, {
        depth,
        bevelEnabled: bevel,
        bevelThickness: 0.06,
        bevelSize: 0.05,
        bevelSegments: 2,
        curveSegments: 1,
      });
    return {
      turkey: ext(toShapes(tr.geometry), 0.45, true),
      others: ext(near.flatMap((f) => toShapes(f.geometry)), 0.12, false),
    };
  }, []);
  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <mesh geometry={others} receiveShadow>
        <meshStandardMaterial color="#1f2a3d" roughness={0.9} metalness={0.05} />
      </mesh>
      <mesh geometry={turkey} castShadow receiveShadow>
        <meshStandardMaterial color={ACCENT} roughness={0.5} metalness={0.15} />
      </mesh>
    </group>
  );
};

const Pin: React.FC<{ x: number; z: number; frame: number; fps: number; at: number }> = ({ x, z, frame, fps, at }) => {
  const drop = spring({ frame: frame - at, fps, config: { damping: 12, mass: 0.8 } });
  const y = 0.5 + (1 - drop) * 7;
  const ringK = ((frame - at - 8) % 36) / 36;
  const ringOn = frame > at + 8;
  return (
    <group position={[x, 0, z]}>
      <group position={[0, y, 0]} visible={frame >= at}>
        <mesh position={[0, 0.7, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.02, 1.4, 12]} />
          <meshStandardMaterial color="#ffffff" roughness={0.4} />
        </mesh>
        <mesh position={[0, 1.55, 0]} castShadow>
          <sphereGeometry args={[0.32, 24, 16]} />
          <meshStandardMaterial color={PIN} roughness={0.35} emissive={PIN} emissiveIntensity={0.35} />
        </mesh>
      </group>
      {ringOn ? (
        <mesh position={[0, 0.52, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={0.4 + ringK * 2.2}>
          <ringGeometry args={[0.8, 1, 48]} />
          <meshBasicMaterial color={PIN} transparent opacity={(1 - ringK) * 0.8} />
        </mesh>
      ) : null}
    </group>
  );
};

// Kamera: genel görünümden şehre alçalarak uçar, sonra yavaşça etrafında süzülür
const CameraRig: React.FC<{ frame: number; target: THREE.Vector3 }> = ({ frame, target }) => {
  const camera = useThree((s) => s.camera);
  const k = interpolate(frame, [12, 105], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const orbit = interpolate(frame, [0, 150], [-0.25, 0.12]);
  const look = new THREE.Vector3().lerpVectors(new THREE.Vector3(0, 0, 1), target, k);
  const dist = interpolate(k, [0, 1], [44, 17]);
  const tilt = interpolate(k, [0, 1], [1.05, 0.6]); // yerden açı (radyan)
  useLayoutEffect(() => {
    camera.position.set(
      look.x + Math.sin(orbit) * Math.cos(tilt) * dist,
      look.y + Math.sin(tilt) * dist,
      look.z + Math.cos(orbit) * Math.cos(tilt) * dist,
    );
    camera.lookAt(look);
    camera.updateProjectionMatrix();
  });
  return null;
};

export const TurkeyFly: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const [ax, ay] = proj([32.86, 39.93]) as [number, number]; // Ankara
  const target = useMemo(() => new THREE.Vector3(ax, 0.5, ay), [ax, ay]);
  const label = spring({ frame: frame - 104, fps, config: { damping: 14 } });
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <ThreeCanvas width={width} height={height} camera={{ fov: 40, near: 0.1, far: 300 }} shadows>
        <color attach="background" args={[BG]} />
        <fog attach="fog" args={[BG, 25, 80]} />
        <ambientLight intensity={0.55} />
        <hemisphereLight args={["#9fb8ff", "#1a1206", 0.6]} />
        <directionalLight
          position={[-12, 22, -8]}
          intensity={2.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-bias={-0.0004}
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
        <Land />
        <Pin x={ax} z={ay} frame={frame} fps={fps} at={92} />
        <CameraRig frame={frame} target={target} />
      </ThreeCanvas>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: height * 0.5 + 230,
          textAlign: "center",
          fontFamily: FONT,
          opacity: label,
          transform: `translateY(${(1 - label) * 30}px)`,
        }}
      >
        <div style={{ color: "#fff", fontWeight: 900, fontSize: 92, letterSpacing: 2, textShadow: "0 6px 30px rgba(0,0,0,0.7)" }}>
          ANKARA
        </div>
        <div style={{ color: ACCENT, fontWeight: 800, fontSize: 40, marginTop: 6, textShadow: "0 4px 20px rgba(0,0,0,0.7)" }}>
          9 Kasım · Anıtkabir
        </div>
      </div>
    </AbsoluteFill>
  );
};
