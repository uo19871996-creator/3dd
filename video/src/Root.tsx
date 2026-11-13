import React from "react";
import { Composition } from "remotion";
import { Short, ShortProps, FPS } from "./Short";
import { ShortV2 } from "./v2/ShortV2";
import type { ShortV2Props } from "./v2/types";

const sample: ShortProps = {
  brand: "GÜNDEM 5",
  date: "11 Kasım 2026",
  index: 1,
  total: 5,
  category: "EKONOMİ",
  accent: "#22d3ee",
  title: "Örnek başlık burada duracak",
  audio: "",
  duration: 12,
  levels: [],
  scenes: [
    {
      heading: "Ne oldu?",
      start: 0,
      end: 6,
      chunks: [
        { text: "Bu bir örnek", start: 0, end: 3 },
        { text: "altyazı satırıdır", start: 3, end: 6 },
      ],
    },
    {
      heading: "Rakamlar",
      stat: { value: "%42", label: "örnek oran" },
      start: 6,
      end: 12,
      chunks: [{ text: "İkinci sahne", start: 6, end: 12 }],
    },
  ],
};

const sampleV2: ShortV2Props = {
  brand: "GÜNDEM 5",
  date: "11 Kasım 2026",
  index: 1,
  total: 5,
  category: "DÜNYA",
  categoryIcon: "globe",
  accent: "#a78bfa",
  title: "Dünya liderleri Antalya'da: COP31 başladı",
  audio: "",
  duration: 16,
  scenes: [
    { heading: "", icon: "globe", start: 0, end: 4, chunks: [{ text: "Örnek giriş", start: 0, end: 4 }] },
    {
      heading: "Nerede?",
      icon: "map-pin",
      map: { place: "Antalya", lat: 36.9, lon: 30.7, label: "9–20 Kasım" },
      start: 4,
      end: 9,
      chunks: [{ text: "Harita sahnesi", start: 4, end: 9 }],
    },
    {
      heading: "Rakamlar",
      icon: "users",
      stat: { value: "102", label: "ülkeden lider" },
      start: 9,
      end: 13,
      chunks: [{ text: "Rakam sahnesi", start: 9, end: 13 }],
    },
    { heading: "Senin yorumun?", start: 13, end: 16, chunks: [{ text: "Yorumlara yaz", start: 13, end: 16 }] },
  ],
};

export const Root: React.FC = () => (
  <>
    <Composition
      id="Short"
      component={Short}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={FPS * 12}
      defaultProps={sample}
      calculateMetadata={({ props }) => ({
        durationInFrames: Math.ceil(props.duration * FPS),
      })}
    />
    <Composition
      id="ShortV2"
      component={ShortV2}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={FPS * 16}
      defaultProps={sampleV2}
      calculateMetadata={({ props }) => ({
        durationInFrames: Math.ceil(props.duration * FPS),
      })}
    />
  </>
);
