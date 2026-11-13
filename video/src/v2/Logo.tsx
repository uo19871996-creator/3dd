import React from "react";

/** Kanal logosu (Ümit'ten Videolar): sarı "Ü", ortada oynat işareti, turkuaz ve kırmızı noktalar. */
export const Logo: React.FC<{ size: number; style?: React.CSSProperties }> = ({ size, style }) => (
  <svg viewBox="0 0 160 160" width={size} height={size} style={style}>
    <defs>
      <linearGradient id="logo-bg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#1e1e1e" />
        <stop offset="1" stopColor="#0c0c0c" />
      </linearGradient>
    </defs>
    <rect width="160" height="160" rx="34" fill="url(#logo-bg)" />
    <path
      d="M52 66 V91 A29 29 0 0 0 110 91 V66"
      fill="none"
      stroke="#FFC233"
      strokeWidth="17"
      strokeLinecap="round"
    />
    <path d="M76 80 L94 91 L76 102 Z" fill="#fff" stroke="#fff" strokeWidth="5" strokeLinejoin="round" />
    <circle cx="63" cy="46" r="8" fill="#2ED3A3" />
    <circle cx="99" cy="46" r="8" fill="#FF5E62" />
  </svg>
);
