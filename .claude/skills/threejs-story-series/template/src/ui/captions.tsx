import React from "react";
import { useCurrentFrame } from "remotion";
import { AMB, CREAM, EP, FPS, LINE, RED, SANS } from "../kit/ui";

/** Captions straight from src/lines.json.
 *  Each VO line is split on spaces into phrases (write ≤7 words per phrase in script.md); each phrase gets screen time
 *  proportional to its length inside the line's [t, end]. Under it: the full subtitle line in a dark box.
 *  Highlight: phrases containing a word from episode.json "red" get a red pill, "amb" get amber text. Update both every episode. */
type Chunk = { a: number; b: number; text: string; sub: string; style: "p" | "r" | "a" };
const RED_WORDS: string[] = EP.red ?? [];
const AMB_WORDS: string[] = EP.amb ?? [];
export const CHUNKS: Chunk[] = LINE.flatMap((l) => {
  const parts = l.th.split(" ").filter(Boolean);
  const total = parts.reduce((s, p) => s + p.length, 0);
  let t = l.t;
  return parts.map((p, i) => {
    const d = ((l.end - l.t) * p.length) / total;
    const c: Chunk = { a: t, b: i === parts.length - 1 ? l.end + 0.25 : t + d, text: p, sub: l.en, style: RED_WORDS.some((w) => p.includes(w)) ? "r" : AMB_WORDS.some((w) => p.includes(w)) ? "a" : "p" };
    t += d;
    return c;
  });
});

/** y = top of the caption block. Keep faces/props above ~1150 px or below ~1500 px in every shot. */
export function Captions({ hideFrom = 1e9, y = 1230 }: { hideFrom?: number; y?: number }) {
  const f = useCurrentFrame();
  const t = f / FPS;
  const c = CHUNKS.find((k) => t >= k.a && t < k.b);
  if (!c || t >= hideFrom) return null;
  const k = Math.min(1, (t - c.a) / 0.08);
  const base: React.CSSProperties = { fontFamily: SANS, fontWeight: 600, fontSize: Math.min(66, Math.floor(1800 / Math.max(1, c.text.length))), lineHeight: 1.25, whiteSpace: "pre" };
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: y, display: "flex", flexDirection: "column", alignItems: "center", opacity: k }}>
      {c.style === "r"
        ? <span style={{ ...base, background: RED, color: "#FFF6EE", padding: "2px 22px 6px", borderRadius: 10, boxShadow: "0 4px 14px rgba(0,0,0,0.35)" }}>{c.text}</span>
        : <span style={{ ...base, color: c.style === "a" ? AMB : CREAM, textShadow: "0 3px 16px rgba(0,0,0,0.65)" }}>{c.text}</span>}
      {EP.subtitles && c.sub ? <div style={{ marginTop: 22, maxWidth: 880, background: "rgba(20,22,28,0.74)", color: "#F2F2F2", fontFamily: SANS, fontWeight: 600, fontSize: 36, lineHeight: 1.3, padding: "8px 26px 10px", borderRadius: 10, textAlign: "center" }}>{c.sub}</div> : null}
    </div>
  );
}
