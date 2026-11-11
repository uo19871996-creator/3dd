import React from "react";
import { Composition } from "remotion";
import { Short, ShortProps, FPS } from "./Short";

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

export const Root: React.FC = () => (
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
);
