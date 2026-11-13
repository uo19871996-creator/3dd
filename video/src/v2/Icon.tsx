import React from "react";
import { icons, type LucideIcon } from "lucide-react";

const toPascal = (name: string) =>
  name
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join("");

/** Lucide ikonunu isimle çizer ("plane-landing", "Trophy" ...). Bilinmeyen isimde gazete ikonu. */
export const Icon: React.FC<{ name?: string; size: number; color: string; strokeWidth?: number }> = ({
  name,
  size,
  color,
  strokeWidth = 1.8,
}) => {
  const lib = icons as Record<string, LucideIcon>;
  const C = (name && (lib[toPascal(name)] ?? lib[name])) || lib.Newspaper;
  return <C size={size} color={color} strokeWidth={strokeWidth} absoluteStrokeWidth={false} />;
};
