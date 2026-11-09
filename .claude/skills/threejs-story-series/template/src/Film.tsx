import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Cam, Shot, type V3 } from "./kit/three";
import { BlurIn, DUR, FPS, FadeOut, Flash, Grain, LINE, Vig, fr, io } from "./kit/ui";
import { Char, SLIM, headCenter, type Pose } from "./rig/char";
import { YOU, infected, ADULT } from "./rig/cast";
import { HUSH, LISTEN, SIT, blendPose } from "./rig/poses";
import { Cat } from "./rig/pets";
import { Apartment, BED, DOOR, WARDROBE } from "./sets/apartment";
import { Captions } from "./ui/captions";
import { Clock, Knocks, NextCard, Rings, RuleSign, RuleTag } from "./ui/cards";

/** DEMO EPISODE — "If someone knocks at 2 a.m., don't answer" (~30 s).
 *  How an episode is built:
 *    1. Shots = small components that place the cast inside ONE world (sets/…) and set a camera.
 *    2. CUTS = the edit table in seconds, cut on line starts/ends from src/lines.json.
 *    3. Cards / Click / any DOM go NEXT TO a <Shot>, never inside it.
 *  Look: warm practical lights + halos, tilt-shift soft bands top and bottom, slow push-in on every shot. */

/* ─── staging: positions are fixed for the whole episode (continuity) ─── */
const YOU_AT: V3 = [BED[0] + 0.55, 0, BED[2] - 0.1];
const FACE_DOOR = Math.atan2(DOOR[0] - YOU_AT[0], DOOR[2] - YOU_AT[2]); // ry that faces the door
const CAT_AT: V3 = [BED[0] - 0.15, 0.55, BED[2] - 0.6];
const blink = (f: number, s = 0) => ((f + s * 23) % 83 < 4 ? 1 : 0);

/** the room with you on the bed edge and the cat on the blanket. act changes the pose */
type Act = "sit" | "listen" | "hush" | "turn";
const Room: React.FC<{ act?: Act; feet?: number; shake?: number; catUp?: number; children?: React.ReactNode }> = ({ act = "sit", feet = 0, shake = 0, catUp = 0, children }) => {
  const f = useCurrentFrame();
  const pose: Pose =
    act === "listen" ? { ...SIT, ...LISTEN, blink: blink(f) } :
    act === "hush" ? { ...SIT, ...HUSH } :
    act === "turn" ? { ...blendPose({ ...SIT, ...HUSH }, { ...SIT, head: [0.1, -1.25, 0], browUp: 1, mouth: 0.25, blink: 0 }, io(f, 6, 40, 0, 1)) } :
    { ...SIT, head: [0.05, 0, 0], browUp: 0.4, blink: blink(f) };
  return (
    <Apartment feet={feet} shake={shake}>
      {/* fill light near the face: a dark room without it turns the character into a silhouette */}
      <pointLight position={[YOU_AT[0] + 0.9, 1.6, YOU_AT[2] - 0.9]} intensity={1.1} distance={3.5} color="#FFD8B0" />
      <Char L={YOU} p={YOU_AT} ry={FACE_DOOR} pose={pose} seed={1} />
      <Cat p={CAT_AT} ry={FACE_DOOR} pose={{ crouch: 0.6 - catUp * 0.6, puff: catUp * 0.8, head: [0, catUp * 0.25], tail: f / (catUp ? 5 : 14), look: [0.3, 0] }} />
      {children}
    </Apartment>
  );
};

/* ─── cameras. Sitting head ≈ 1.17 m with the default build; the head is small, so a head-and-shoulders shot sits ~2 m away at fov 32.
       Every shot pushes in slowly (the camera is never dead still). ─── */
const FACE_Y = headCenter(YOU) + (SIT.y ?? 0) * (YOU.build ?? SLIM).leg * YOU.height; // sitting: the hips drop by SIT.y (leg units)
const dir = (k: number): V3 => [YOU_AT[0] + Math.sin(FACE_DOOR) * k, FACE_Y + 0.06, YOU_AT[2] + Math.cos(FACE_DOOR) * k];
const SWide = () => { const f = useCurrentFrame(); return <Shot><Room /><Cam p={[-2.0, 1.62, 2.4 - f * 0.003]} t={[0.9, 0.85, -2.6]} fov={46} drift={0.5} /></Shot>; };
const SFace: React.FC<{ act?: Act }> = ({ act = "sit" }) => { const f = useCurrentFrame(); return <Shot><Room act={act} /><Cam p={dir(2.1 - f * 0.003)} t={[YOU_AT[0], FACE_Y - 0.1, YOU_AT[2]]} fov={32} drift={0.4} /></Shot>; };
const SDoorPOV = () => { const f = useCurrentFrame(); return <Shot><Room /><Cam p={[YOU_AT[0] + 0.75, 1.3, YOU_AT[2] - 0.55 - f * 0.004]} t={[DOOR[0], 0.95, DOOR[2]]} fov={40} drift={0.6} /></Shot>; };
const SHigh = () => { const f = useCurrentFrame(); return <Shot><Room /><Cam p={[2.5, 2.55, -2.4 + f * 0.003]} t={[-1.4, 0.5, 1.4]} fov={54} drift={0.4} /></Shot>; };
const SCat = () => { const f = useCurrentFrame(); const up = io(f, 10, 34, 0, 1); return <Shot><Room catUp={up} /><Cam p={[CAT_AT[0] + Math.sin(FACE_DOOR) * 1.45, 0.98, CAT_AT[2] + Math.cos(FACE_DOOR) * 1.45 - f * 0.002]} t={[CAT_AT[0], 0.8, CAT_AT[2]]} fov={38} drift={0.3} /></Shot>; };
const SDoor = () => <Shot><Room act="listen" /><Cam p={[0.3, 1.25, -0.9]} t={[DOOR[0], 1.05, DOOR[2]]} fov={40} drift={0.5} /></Shot>;
const SFloor = () => { const f = useCurrentFrame(); return <Shot><Room act="hush" feet={io(f, 14, 30, 0, 1)} /><Cam p={[DOOR[0] - 0.15, 0.16, DOOR[2] + 1.3]} t={[DOOR[0], 0.0, DOOR[2] + 0.1]} fov={42} drift={0.3} /></Shot>; };
const STurn = () => <Shot><Room act="turn" feet={1} /><Cam p={[-0.1, 1.4, -1.8]} t={[-1.3, 1.0, 1.5]} fov={46} drift={0.4} /></Shot>;
const SWardrobe: React.FC<{ shakeFrom?: number }> = ({ shakeFrom = 0 }) => { const f = useCurrentFrame(); return <Shot><Room act="turn" feet={1} shake={f >= shakeFrom ? 1 : 0} /><Cam p={[WARDROBE[0] + 0.2, 1.15, WARDROBE[2] - 1.9 + f * 0.004]} t={[WARDROBE[0], 1.05, WARDROBE[2]]} fov={42} drift={0.5} /></Shot>; };

/* ─── the edit: cut on line starts/ends, by LINE NUMBER, so a new voice take re-times the picture automatically ─── */
type Cut = { a: number; b: number; el: React.ReactNode };
const T = (n: number) => LINE[n - 1].t;      // start of script line n (seconds)
const E = (n: number) => LINE[n - 1].end;    // end of script line n
const END = E(LINE.length) + 0.4;
const mid = (n: number) => (T(n) + E(n)) / 2;
export const CUTS: Cut[] = [
  { a: 0, b: mid(1), el: <><SDoorPOV /><RuleSign /></> },
  { a: mid(1), b: T(2) - 0.1, el: <><SFace /><RuleTag /></> },
  { a: T(2) - 0.1, b: T(3) - 0.1, el: <SWide /> },
  { a: T(3) - 0.1, b: T(4) - 0.1, el: <><SHigh /><Clock t="02:10" label="ห้อง 604" /></> },
  { a: T(4) - 0.1, b: T(5) - 0.15, el: <SCat /> },
  { a: T(5) - 0.15, b: T(6) - 0.1, el: <><SDoor /><Knocks at={[4, 21, 37]} x={560} y={620} /><Rings x={700} y={760} from={4} every={17} /></> },
  { a: T(6) - 0.1, b: T(7) - 0.1, el: <SFloor /> },
  { a: T(7) - 0.1, b: T(8) - 0.1, el: <SFace act="hush" /> },
  { a: T(8) - 0.1, b: mid(8) + 0.3, el: <STurn /> },
  { a: mid(8) + 0.3, b: END, el: <><SWardrobe shakeFrom={3} /><Knocks at={[3]} x={430} y={560} /></> },
  { a: END, b: DUR / FPS, el: <><BlurIn><SWardrobe /></BlurIn><NextCard /></> },
];

export const HERO_S = mid(8) + 0.3 + 3 / FPS; // the fourth knock
export const Film: React.FC<{ noCaps?: boolean }> = ({ noCaps }) => (
  <AbsoluteFill style={{ background: "#07090F" }}>
    {CUTS.map((c, i) => (
      <Sequence key={i} from={fr(c.a)} durationInFrames={fr(c.b) - fr(c.a)}>
        <AbsoluteFill>{c.el}</AbsoluteFill>
      </Sequence>
    ))}
    <Flash at={fr(HERO_S)} c="rgba(255,236,214,0.85)" />
    <Vig />
    <FadeOut from={DUR - 24} />
    <Grain amount={0.05} />
    {noCaps ? null : <Captions hideFrom={END} />}
  </AbsoluteFill>
);

/** an extra character you can drop into any shot, e.g. the neighbour behind the door (episode 2) */
export const NEIGHBOUR = infected(ADULT);
