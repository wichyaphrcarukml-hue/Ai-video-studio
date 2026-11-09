import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadNotoSansThai } from "@remotion/google-fonts/NotoSansThai";
import { loadFont as loadKanit } from "@remotion/google-fonts/Kanit";
import { loadFont as loadNotoSans } from "@remotion/google-fonts/NotoSans";
import EP from "../episode.json";
import LINES from "../lines.json";

/* ─── timing: everything is driven by src/lines.json (written by scripts/splice.py) ─── */
export const FPS = 30;
export const LINE = LINES.lines;
/** the end card holds 2.6 s after the last word */
export const END_S = Math.round((LINES.total + 2.6) * 10) / 10;
export const DUR = Math.round(END_S * FPS);
export const fr = (s: number) => Math.round(s * FPS);
export { EP };

/* ─── palette: change these to make the series yours ─── */
export const RED = "#D9483B", AMB = "#E9B84A", PAPER = "#ECE5D3", INK = "#2A2622", GREEN = "#2F9A5A";
/** caption text, card accent bar, muted card text */
export const CREAM = "#F2EBDD", GOLD = "#C9A455", MUTED = "#8A8174";

/* ─── font: pick in episode.json ("NotoSansThai" | "Kanit" | "NotoSans"). Add more from @remotion/google-fonts. ─── */
const FONTS: Record<string, () => string> = {
  NotoSansThai: () => loadNotoSansThai("normal", { weights: ["400", "600", "700"], subsets: ["thai", "latin"] }).fontFamily,
  Kanit: () => loadKanit("normal", { weights: ["400", "600", "700"], subsets: ["thai", "latin"] }).fontFamily,
  NotoSans: () => loadNotoSans("normal", { weights: ["400", "600", "700"], subsets: ["latin"] }).fontFamily,
};
export const SANS = (FONTS[EP.font] ?? FONTS.NotoSansThai)();

/* ─── motion helpers ─── */
export const clampE = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);
/** eased 0..1 style interpolation between frames a..b */
export const io = (f: number, a: number, b: number, x: number, y: number) => interpolate(f, [a, b], [x, y], { ...clampE, easing: ease });
export const lin = (f: number, a: number, b: number, x: number, y: number) => interpolate(f, [a, b], [x, y], clampE);
/** springy pop-in 0..1 starting at local frame `delay` */
export function useSpr(delay = 0, damping = 12): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping, stiffness: 200, mass: 0.6 } });
}

/** pop SFX that lands on local frame `at`. "soft" = paper card landing (main), "tick" = light tick (small items: rows, numbers).
 *  Make your own with scripts/sound.py pops (or drop any short wav into public/sfx). Every card that pops in gets one. */
export type ClickKind = "soft" | "tick";
const LEAD: Record<ClickKind, number> = { soft: 1, tick: 0 };
export function Click({ at, v = 0.5, kind = "soft" }: { at: number; v?: number; kind?: ClickKind }) {
  const start = at - LEAD[kind];
  return (
    <Sequence from={Math.max(0, start)} durationInFrames={24} layout="none">
      <Audio src={staticFile(`sfx/pop-${kind}.wav`)} volume={v} startFrom={Math.max(0, -start)} />
    </Sequence>
  );
}

/* ─── atmosphere overlays (DOM, go outside <Shot>) ─── */
export function Grain({ amount = 0.035 }: { amount?: number }) {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity: amount * 4 }}>
      <svg width="1080" height="1920"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={Math.floor(f / 2) % 40} /><feColorMatrix type="saturate" values="0" /></filter><rect width="1080" height="1920" filter="url(#g)" /></svg>
    </AbsoluteFill>
  );
}
export const Vig = ({ a = 0.32 }: { a?: number }) => <AbsoluteFill style={{ background: `radial-gradient(85% 65% at 50% 48%, transparent 50%, rgba(12,8,4,${a}))` }} />;
/** tilt-shift depth of field: the top and bottom bands of the frame go soft, the middle stays sharp (the miniature-diorama look).
 *  band = height of each soft band (px), px = max blur. Built into <Shot> (tilt prop), so cards and captions stay sharp. */
export function TiltShift({ band = 520, px = 9 }: { band?: number; px?: number }) {
  const mask = (dir: "top" | "bottom") => `linear-gradient(to ${dir === "top" ? "bottom" : "top"}, #000 0%, rgba(0,0,0,0.6) 45%, transparent 100%)`;
  const layer = (dir: "top" | "bottom"): React.CSSProperties => ({ position: "absolute", left: 0, right: 0, [dir]: 0, height: band, backdropFilter: `blur(${px}px)`, WebkitBackdropFilter: `blur(${px}px)`, maskImage: mask(dir), WebkitMaskImage: mask(dir) });
  return <AbsoluteFill style={{ pointerEvents: "none" }}><div style={layer("top")} /><div style={layer("bottom")} /></AbsoluteFill>;
}
/** blur a shot in over `len` frames (end card: the last shot goes soft, then the card fades in on top) */
export const BlurIn: React.FC<{ from?: number; len?: number; px?: number; children: React.ReactNode }> = ({ from = 0, len = 15, px = 12, children }) => {
  const f = useCurrentFrame();
  const k = interpolate(f, [from, from + len], [0, 1], clampE);
  return <AbsoluteFill style={{ filter: k > 0 ? `blur(${k * px}px) brightness(${1 - k * 0.35})` : undefined, transform: k > 0 ? `scale(${1 + k * 0.04})` : undefined }}>{children}</AbsoluteFill>;
};
/** coloured edge flash at absolute frame `at` (red = hit, cold blue = reveal) */
export const Flash: React.FC<{ at: number; c: string }> = ({ at, c }) => {
  const f = useCurrentFrame();
  const k = interpolate(f, [at, at + 2, at + 12], [0, 0.55, 0], clampE);
  return k > 0 ? <AbsoluteFill style={{ background: `radial-gradient(70% 55% at 50% 50%, transparent 30%, ${c})`, opacity: k }} /> : null;
};
export const FadeOut: React.FC<{ from: number; len?: number }> = ({ from, len = 26 }) => {
  const f = useCurrentFrame();
  const k = interpolate(f, [from, from + len], [0, 1], clampE);
  return k > 0 ? <AbsoluteFill style={{ background: "#000", opacity: k }} /> : null;
};
