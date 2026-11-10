import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { AMB, CREAM, Click, EP, GOLD, GREEN, INK, MUTED, PAPER, RED, SANS, useSpr } from "../kit/ui";

/** 2D cards that sit OVER a 3D shot (in the cut's fragment, never inside <Shot>). Each pops in with a Click.
 *  Look: cream paper, rounded corners, a coloured bar on the left, soft shadow, small bold heading, flat icons.
 *  Use few: the story should be readable from picture + VO. A card per beat feels like a lecture (viewers hate it). */
const panel: React.CSSProperties = { position: "absolute", background: PAPER, color: INK, borderRadius: 14, fontFamily: SANS, boxShadow: "0 10px 26px rgba(20,12,4,0.38)", overflow: "hidden" };
const bar = (c: string): React.CSSProperties => ({ position: "absolute", left: 0, top: 0, bottom: 0, width: 10, background: c });
const pop = (s: number, dy = 30): React.CSSProperties => ({ opacity: Math.min(1, s * 2), translate: `0 ${(1 - s) * dy}px`, scale: String(0.94 + 0.06 * s) });

export const Tick = ({ s = 44 }: { s?: number }) => <svg width={s} height={s} viewBox="0 0 56 56"><circle cx="28" cy="28" r="27" fill={GREEN} /><path d="M15 29 L25 39 L42 18" stroke="#fff" strokeWidth="7" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>;
export const Cross = ({ s = 44 }: { s?: number }) => <svg width={s} height={s} viewBox="0 0 56 56"><circle cx="28" cy="28" r="27" fill={RED} /><path d="M18 18 L38 38 M38 18 L18 38" stroke="#fff" strokeWidth="7" strokeLinecap="round" /></svg>;

/** the episode's rule on the hook: a small red label over the rule in big type. done = local frame to stamp a tick */
export function RuleSign({ done = -1, y = 210, text = EP.rule }: { done?: number; y?: number; text?: string }) {
  const f = useCurrentFrame();
  const s = useSpr(0, 13);
  const ok = done >= 0 && f >= done ? Math.min(1, (f - done) / 6) : 0;
  return (
    <div style={{ ...panel, left: 170, top: y, width: 740, padding: "24px 34px 30px 46px", ...pop(s, -60) }}>
      <Click at={0} v={0.45} />
      <div style={bar(RED)} />
      <div style={{ display: "inline-block", background: RED, color: "#FFF6EE", fontSize: 28, fontWeight: 700, padding: "2px 16px 5px", borderRadius: 8 }}>{EP.ruleLabel}</div>
      <div style={{ fontSize: 88, fontWeight: 700, lineHeight: 1.15, marginTop: 8 }}>{text}</div>
      {ok ? <div style={{ position: "absolute", right: 22, top: 22, scale: String(ok) }}><Tick s={70} /></div> : null}
      {done >= 0 ? <Click at={done} v={0.35} kind="tick" /> : null}
    </div>
  );
}

/** persistent rule chip, top-left, held across all the shots of one rule. n = rule number, done = local frame for the tick */
export function RuleTag({ text = EP.rule, n, done = -1 }: { text?: string; n?: number; done?: number }) {
  const f = useCurrentFrame();
  const s = useSpr(0, 14);
  const ok = done >= 0 && f >= done;
  return (
    <div style={{ ...panel, left: 34, top: 96, padding: "10px 22px 14px 32px", display: "flex", alignItems: "center", gap: 16, opacity: Math.min(1, s * 2), translate: `${(1 - s) * -60}px 0` }}>
      <div style={bar(RED)} />
      <div>
        <div style={{ fontSize: 22, color: MUTED, fontWeight: 600 }}>{EP.ruleTagLabel}{n ? ` · ข้อ ${n}` : ""}</div>
        <div style={{ fontSize: 40, fontWeight: 700, lineHeight: 1.1 }}>{text}</div>
      </div>
      {ok ? <Tick s={44} /> : null}
      {done >= 0 ? <Click at={done} v={0.3} kind="tick" /> : null}
    </div>
  );
}

/** HUD: clock chip top-right + place chip top-left. Update t through the episode (02:10 → 02:14 …) so time is felt. */
export function Clock({ t, label }: { t: string; label?: string }) {
  const s = useSpr(0, 13);
  const chip: React.CSSProperties = { position: "absolute", top: 92, background: "rgba(246,242,234,0.92)", color: INK, fontFamily: SANS, fontWeight: 700, borderRadius: 12, padding: "6px 18px 9px", boxShadow: "0 6px 16px rgba(0,0,0,0.3)", ...pop(s, -24) };
  return (
    <>
      <Click at={0} v={0.3} kind="tick" />
      <div style={{ ...chip, right: 34, fontSize: 46, fontVariantNumeric: "tabular-nums" }}>{t}</div>
      {label ? <div style={{ ...chip, left: 34, fontSize: 32, padding: "8px 18px 10px" }}>{label}</div> : null}
    </>
  );
}

/** proof card: a real fact with ONE big red number, revealed on the VO word. Always give the source. */
export function ProofCard({ title, big, unit = "", note, source, y = 360 }: { title: string; big: string; unit?: string; note?: string; source?: string; y?: number }) {
  const a = useSpr(0, 13), b = useSpr(8, 12);
  return (
    <div style={{ ...panel, left: 110, top: y, width: 860, padding: "28px 36px 26px 50px", ...pop(a) }}>
      <Click at={0} v={0.45} />
      <div style={bar(GOLD)} />
      <div style={{ fontSize: 34, fontWeight: 700 }}>{title}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginTop: 6, opacity: b, translate: `0 ${(1 - b) * 16}px` }}>
        <div style={{ fontSize: 150, fontWeight: 700, color: RED, lineHeight: 1 }}>{big}</div>
        <div style={{ fontSize: 48, fontWeight: 700, color: RED }}>{unit}</div>
      </div>
      {note ? <div style={{ fontSize: 32, marginTop: 10, lineHeight: 1.3 }}>{note}</div> : null}
      {source ? <div style={{ fontSize: 22, marginTop: 14, color: MUTED }}>{source}</div> : null}
    </div>
  );
}

/** checklist card: rows with a tick or a cross, one row every `every` frames (each row ticks) */
export function Checklist({ title, rows, every = 10, y = 380 }: { title: string; rows: { text: string; ok: boolean }[]; every?: number; y?: number }) {
  const f = useCurrentFrame();
  const a = useSpr(0, 13);
  return (
    <div style={{ ...panel, left: 130, top: y, width: 820, padding: "26px 34px 22px 48px", ...pop(a) }}>
      <Click at={0} v={0.45} />
      <div style={bar(GOLD)} />
      <div style={{ fontSize: 34, fontWeight: 700, marginBottom: 12 }}>{title}</div>
      {rows.map((r, i) => {
        const at = 8 + i * every, k = Math.min(1, Math.max(0, (f - at) / 6));
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, padding: "10px 0", borderTop: i ? "2px solid rgba(42,38,34,0.1)" : "none", opacity: k, translate: `${(1 - k) * 20}px 0` }}>
            <Click at={at} v={0.25} kind="tick" />
            {r.ok ? <Tick s={46} /> : <Cross s={46} />}
            <div style={{ fontSize: 40, fontWeight: 600 }}>{r.text}</div>
          </div>
        );
      })}
    </div>
  );
}

/** counter: n of `of` dots fill one by one (how many are outside, how many doors left) */
export function Dots({ n, of, label, y = 420, every = 6 }: { n: number; of: number; label: string; y?: number; every?: number }) {
  const f = useCurrentFrame();
  const a = useSpr(0, 13);
  return (
    <div style={{ ...panel, left: 240, top: y, width: 600, padding: "22px 30px 24px 44px", textAlign: "center", ...pop(a) }}>
      <Click at={0} v={0.4} />
      <div style={bar(RED)} />
      <div style={{ fontSize: 32, fontWeight: 700 }}>{label}</div>
      <div style={{ display: "flex", justifyContent: "center", gap: 18, marginTop: 16 }}>
        {Array.from({ length: of }, (_, i) => <div key={i} style={{ width: 52, height: 52, borderRadius: 26, border: `5px solid ${RED}`, background: f >= 10 + i * every && i < n ? RED : "transparent" }} />)}
      </div>
      {Array.from({ length: n }, (_, i) => <Click key={i} at={10 + i * every} v={0.2} kind="tick" />)}
    </div>
  );
}

/** a number with a bracket (a measured gap: "10 ซม.", "2 ม.") drawn over the picture */
export function Measure({ value, label, x = 540, y = 420, w = 520 }: { value: string; label: string; x?: number; y?: number; w?: number }) {
  const s = useSpr(0, 12);
  return (
    <div style={{ position: "absolute", left: x - w / 2, top: y, width: w, fontFamily: SANS, textAlign: "center", opacity: Math.min(1, s * 2) }}>
      <Click at={0} v={0.35} kind="tick" />
      <div style={{ fontSize: 30, color: CREAM, opacity: 0.85, textShadow: "0 2px 10px rgba(0,0,0,0.8)" }}>{label}</div>
      <div style={{ fontSize: 110, fontWeight: 700, color: AMB, lineHeight: 1.1, textShadow: "0 4px 16px rgba(0,0,0,0.85)" }}>{value}</div>
      <div style={{ position: "relative", height: 30, marginTop: 6, scale: `${Math.min(1, s * 1.4)} 1` }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: 13, height: 5, background: AMB, borderRadius: 3 }} />
        <div style={{ position: "absolute", left: 0, top: 0, width: 5, height: 30, background: AMB }} />
        <div style={{ position: "absolute", right: 0, top: 0, width: 5, height: 30, background: AMB }} />
      </div>
    </div>
  );
}

/** sound rings (a speaker, a knock source) at screen x,y; `every` frames between rings */
export function Rings({ x = 540, y = 760, c = "rgba(255,226,170,0.8)", from = 0, every = 18 }: { x?: number; y?: number; c?: string; from?: number; every?: number }) {
  const f = useCurrentFrame() - from;
  if (f < 0) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {[0, 1, 2].map((i) => {
        const k = ((f + i * every) % (every * 3)) / (every * 3);
        return <div key={i} style={{ position: "absolute", left: x - 40 - k * 160, top: y - 40 - k * 160, width: 80 + k * 320, height: 80 + k * 320, borderRadius: "50%", border: `5px solid ${c}`, opacity: 1 - k }} />;
      })}
    </AbsoluteFill>
  );
}

/** sound word in a speech bubble ("ก๊อก") popping at local frames `at` (match them to the measured SFX hits: tools.py onsets) */
export function Knocks({ at, word = "ก๊อก", x = 600, y = 760 }: { at: number[]; word?: string; x?: number; y?: number }) {
  const f = useCurrentFrame();
  return (
    <>
      {at.map((a, i) => {
        const k = f - a;
        if (k < 0 || k > 26) return null;
        return <div key={i} style={{ position: "absolute", left: x + (i - 1) * 190, top: y - i * 70, fontFamily: SANS, fontSize: 64, fontWeight: 700, color: INK, background: PAPER, borderRadius: 40, padding: "6px 28px 12px", boxShadow: "0 6px 18px rgba(0,0,0,0.4)", opacity: 1 - Math.max(0, k - 16) / 10, scale: String(Math.min(1, 0.6 + k / 6)) }}>{word}!</div>;
      })}
      {at.map((a, i) => <Click key={`c${i}`} at={a} v={0.2} kind="tick" />)}
    </>
  );
}

/** end card over the blurred last shot: "next" label, next episode number + its hook (the cliffhanger), a quiet CTA.
 *  Always the NEXT episode number. Wrap the shot under it in <BlurIn>. */
export function NextCard({ ep = EP.next.ep, line = EP.next.line }: { ep?: string; line?: string }) {
  const f = useCurrentFrame();
  const a = useSpr(10, 14), b = useSpr(22, 13), e = useSpr(44, 14);
  return (
    <AbsoluteFill style={{ fontFamily: SANS, alignItems: "center", justifyContent: "center", textAlign: "center" }}>
      <Click at={10} v={0.4} />
      <div style={{ fontSize: 88, fontWeight: 700, color: CREAM, opacity: a, translate: `0 ${(1 - a) * 24}px`, textShadow: "0 4px 18px rgba(0,0,0,0.6)" }}>{ep}</div>
      <div style={{ width: 120, height: 6, background: RED, borderRadius: 3, margin: "22px 0", opacity: a }} />
      <div style={{ fontSize: 62, fontWeight: 700, color: RED, opacity: b, translate: `0 ${(1 - b) * 24}px`, maxWidth: 900, lineHeight: 1.25, textShadow: "0 3px 14px rgba(0,0,0,0.5)" }}>{line}</div>
      <div style={{ marginTop: 44, fontSize: 32, color: "#CFC8BB", opacity: e * (0.7 + 0.3 * Math.sin(f / 8)) }}>{EP.next.follow}</div>
    </AbsoluteFill>
  );
}
