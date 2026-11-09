import React from "react";
import { AbsoluteFill } from "remotion";
import { Film } from "./Film";
import { EP, RED, SANS } from "./kit/ui";

/** Cover = the film without captions + the title ON TOP (episode number + title + the rule in a red pill).
 *  The comp is as long as the film; render ONE frame: npx remotion still src/index.ts Cover out/cover.png --frame=<episode.json coverFrame>
 *  (A 1-frame comp with <Freeze> does not mount later Sequences and shows the wrong shot.)
 *  Pick a frame where a face shows emotion and nothing important sits under the title. */
export const Cover: React.FC = () => (
  <AbsoluteFill>
    <Film noCaps />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(5,6,12,0.88) 0%, rgba(5,6,12,0.55) 26%, transparent 42%)" }} />
    <div style={{ position: "absolute", top: 150, left: 0, right: 0, textAlign: "center", fontFamily: SANS }}>
      <div style={{ color: "#F6F4EE", fontSize: 84, fontWeight: 700, lineHeight: 1.2, textShadow: "0 4px 18px rgba(0,0,0,0.7)" }}>{`ตอนที่ ${EP.ep}`}<br />{EP.title}</div>
      <div style={{ display: "inline-block", marginTop: 18, background: RED, color: "#FFF6EE", fontSize: 76, fontWeight: 700, padding: "4px 30px 10px", borderRadius: 14 }}>{EP.rule}</div>
    </div>
  </AbsoluteFill>
);
