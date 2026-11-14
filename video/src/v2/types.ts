export const FPS = 30;

// words: her kelimenin sesteki başlangıcı (sn); varsa vurgu buna göre ilerler
export type Chunk = { text: string; start: number; end: number; until?: number; words?: number[] };

export type MapSpec = {
  place: string;
  lat: number;
  lon: number;
  scope?: "turkey" | "world";
  label?: string;
};

export type ChartSpec = {
  unit?: string;
  items: { label: string; value: number }[];
};

export type Photo = { src: string; credit: string };

export type SceneV2 = {
  heading: string;
  photo?: Photo;
  start: number;
  end: number;
  chunks: Chunk[];
  stat?: { value: string; label: string };
  icon?: string;
  map?: MapSpec;
  chart?: ChartSpec;
  points?: string[];
  subscribe?: boolean; // videonun sonundaki "abone ol" kapanış ekranı
};

export type ShortV2Props = {
  brand: string;
  date: string;
  index: number;
  total: number;
  category: string;
  categoryIcon: string;
  accent: string;
  title: string;
  audio: string;
  duration: number;
  scenes: SceneV2[];
  channelName?: string;
  channelTagline?: string;
  grain?: number; // film greni şiddeti (0 = kapalı; 0,025 hafif)
};

export const INK = "#f8fafc";
export const MUTED = "rgba(226,232,240,0.66)";
export const FONT = "Montserrat, sans-serif";
