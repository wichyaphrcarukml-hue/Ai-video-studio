import React from "react";
import * as THREE from "three";
import { useCurrentFrame } from "remotion";

/** Character rig built only from primitives (capsule, sphere, box, lathe, cone, torus).
 *  Default build = SLIM: small round head, long neck, slender torso, long thin limbs, a plain dot-eyed face.
 *  Proportions are numbers (Look.build + Look.headS), so every series can find its own figure.
 *  Feet at y=0, facing +z, the character's left = +x. Every motion is a pure function of the frame.
 *  Appearance = Look (see rig/cast.ts), motion = Pose (see rig/poses.ts). No images, no AI stills. */

export type V3 = [number, number, number];
const TAU = Math.PI * 2;

const Mat: React.FC<{ c: string; r?: number; e?: string; ei?: number; side?: THREE.Side }> = ({ c, r = 0.82, e, ei = 0, side }) => (
  <meshStandardMaterial color={c} roughness={r} metalness={0} emissive={e ?? "#000"} emissiveIntensity={ei} side={side} />
);
const Cap: React.FC<{ p?: V3; r: number; l: number; c: string; rot?: V3; s?: V3 }> = ({ p = [0, 0, 0], r, l, c, rot = [0, 0, 0], s = [1, 1, 1] }) => (
  <mesh position={p} rotation={rot} scale={s} castShadow><capsuleGeometry args={[r, l, 8, 18]} /><Mat c={c} /></mesh>
);
const Ball: React.FC<{ p?: V3; r: number; c: string; s?: V3; rot?: V3; e?: string; ei?: number }> = ({ p = [0, 0, 0], r, c, s = [1, 1, 1], rot = [0, 0, 0], e, ei }) => (
  <mesh position={p} scale={s} rotation={rot}><sphereGeometry args={[r, 32, 24]} /><Mat c={c} e={e} ei={ei} /></mesh>
);
const Box: React.FC<{ p?: V3; s: V3; c: string; rot?: V3; e?: string; ei?: number }> = ({ p = [0, 0, 0], s, c, rot = [0, 0, 0], e, ei }) => (
  <mesh position={p} rotation={rot}><boxGeometry args={s} /><Mat c={c} e={e} ei={ei} /></mesh>
);
const Disc: React.FC<{ p: V3; r: number; c: string; s?: V3; e?: string; ei?: number }> = ({ p, r, c, s = [1, 1, 1], e, ei }) => (
  <mesh position={p} scale={s}><circleGeometry args={[r, 28]} /><meshStandardMaterial color={c} roughness={0.4} emissive={e ?? "#000"} emissiveIntensity={ei ?? 0} /></mesh>
);

const Lathe: React.FC<{ pts: [number, number][]; c: string; p?: V3; s?: V3; ph0?: number; ph?: number; r?: number }> = ({ pts, c, p = [0, 0, 0], s = [1, 1, 1], ph0 = 0, ph = TAU, r }) => {
  const g = React.useMemo(() => new THREE.LatheGeometry(pts.map(([x, y]) => new THREE.Vector2(x, y)), 48, ph0, ph), [pts, ph0, ph]);
  return <mesh position={p} scale={s} geometry={g}><Mat c={c} r={r} side={THREE.DoubleSide} /></mesh>;
};
const TORSO_PTS: [number, number][] = [[0.0, -0.05], [0.2, -0.05], [0.212, 0.0], [0.208, 0.12], [0.2, 0.24], [0.185, 0.31], [0.15, 0.36], [0.09, 0.4], [0.05, 0.415], [0.0, 0.42]];
const COAT_PTS: [number, number][] = [[0.0, -0.56], [0.25, -0.56], [0.235, -0.3], [0.215, 0.0], [0.205, 0.15], [0.198, 0.26], [0.18, 0.32], [0.14, 0.37], [0.09, 0.41], [0.0, 0.42]];
const SCRUB_PTS: [number, number][] = [[0.0, -0.06], [0.205, -0.06], [0.206, 0.1], [0.198, 0.24], [0.182, 0.31], [0.15, 0.36], [0.09, 0.4], [0.0, 0.41]];
const SKIRT_PTS: [number, number][] = [[0.0, 0.02], [0.2, 0.02], [0.218, -0.08], [0.26, -0.22], [0.305, -0.38], [0.31, -0.41], [0.0, -0.41]];
const BOB_PTS: [number, number][] = [[0.2, -0.16], [0.198, -0.08], [0.19, 0.0], [0.184, 0.07], [0.176, 0.11], [0.16, 0.15], [0.13, 0.185], [0.085, 0.208], [0.04, 0.218], [0.0, 0.22]];
const FRINGE_PTS: [number, number][] = [[0.168, 0.07], [0.182, 0.076], [0.184, 0.1], [0.176, 0.13], [0.16, 0.155], [0.13, 0.187], [0.085, 0.209], [0.04, 0.219], [0.0, 0.221]];

/* ─── build = body proportions, 1 = the rig's base unit for every part ─── */
export type Build = {
  /** leg length */ leg: number; /** arm length */ arm: number; /** torso height */ torso: number;
  /** torso + hip width */ girth: number; /** limb thickness */ limb: number; /** neck length */ neck: number;
};
/** default: slender figure, small head (pair with headS ≈ 0.9–1.0) */
export const SLIM: Build = { leg: 1.38, arm: 1.32, torso: 1.12, girth: 0.82, limb: 0.72, neck: 1.6 };
/** hip height above the feet for a build (so poses and seats work for any leg length) */
export const hipHeight = (B: Build): number => 0.67 * B.leg + 0.09;

/* ─── look = appearance (presets + your cast live in rig/cast.ts) ─── */
export type Outfit = "hoodie" | "coat" | "scrubs" | "uniform" | "blouse" | "shirt" | "jersey" | "tee";
export type Hair = "short" | "pony" | "messy" | "bob" | "spiky";
export type Look = {
  skin: string; hair: Hair; hairC: string; iris: string; eyeW: number; eyeH: number;
  /** "dots" = two small dark eyes (default), "big" = cartoon eyes with white + iris */ face?: "dots" | "big"; build?: Build;
  outfit: Outfit; top: string; pants: string; shoes: string; patch?: boolean; fangs?: boolean; lips?: string; brow: string; height: number;
  sole?: string; trim?: string; irisK?: number; hairR?: number; hairLen?: number; headS?: number; socks?: string; glasses?: boolean; clip?: string; backpack?: string;
  band?: string; holdR?: "flashlight" | "phone" | "tape" | "keys"; phones?: string;
};
/* ─── pose ─── */
export type Pose = {
  spine?: V3; head?: V3; shL?: V3; shR?: V3; elL?: number; elR?: number; hipL?: V3; hipR?: V3; knL?: number; knR?: number;
  y?: number; blink?: number; mouth?: number; browUp?: number; look?: [number, number]; handNeckR?: boolean; handNeckL?: number; bite?: number; cloth?: number; blood?: number; bruise?: number; holdOff?: boolean;
};
export const REST: Pose = { shL: [0, 0, 0.12], shR: [0, 0, -0.12], elL: -0.15, elR: -0.15 };

const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];

/** deterministic blink: closes ~0.12 s every ~3.4 s, offset by seed */
export function blinkAt(f: number, seed = 0): number {
  const t = (f + seed * 37) % 102;
  return t < 4 ? Math.sin((t / 4) * Math.PI) : 0;
}

/* ─── parts ─── */
const Eye: React.FC<{ x: number; L: Look; blink: number; look: [number, number] }> = ({ x, L, blink, look }) => {
  const h = 0.034 * L.eyeH, w = 0.034 * L.eyeW;
  const open = 1 - blink;
  if ((L.face ?? "dots") === "dots") return (
    <group position={[x, -0.005, 0.141]} rotation={[0, x * 2.2, 0]}>
      <group position={[look[0] * 0.01, look[1] * 0.006, 0]} scale={[1, Math.max(0.12, open), 1]}>
        <Ball r={1} c="#1C1A1D" s={[w * 0.5, h * 0.62, 0.016]} />
        <Disc p={[w * 0.15, h * 0.2, 0.0165]} r={0.0045} c="#FFFFFF" e="#FFFFFF" ei={0.5} />
      </group>
    </group>
  );
  return (
    <group position={[x, -0.005, 0.141]} rotation={[0, x * 2.2, 0]}>
      <Ball r={1} c="#F4F2EC" s={[w, h * Math.max(0.08, open), 0.016]} />
      <group position={[look[0] * 0.012, look[1] * 0.008, 0.0165]} scale={[1, Math.max(0.05, open), 1]}>
        <Disc p={[0, 0, 0]} r={Math.min(w, h) * (L.irisK ?? 0.72)} c={L.iris} s={[L.eyeH < 0.8 ? 0.75 : 1, L.eyeH < 0.8 ? 1.1 : 1, 1]} />
        <Disc p={[0, 0, 0.001]} r={Math.min(w, h) * 0.36} c="#0B0B0E" />
        <Disc p={[0.006, 0.007, 0.002]} r={0.005} c="#FFFFFF" e="#FFFFFF" ei={0.6} />
      </group>
      {/* upper lid: skin cap sliding down (hidden when open) */}
      {blink > 0.02 ? <Ball p={[0, h * (1 - blink) * 0.95 + 0.002, 0.004]} r={1} c={L.skin} s={[w * 1.12, h * blink * 1.05, 0.02]} /> : null}
      {L.eyeH < 0.8 ? <Box p={[x > 0 ? 0.003 : -0.003, h * 0.72, 0.017]} s={[w * 2.1, 0.004, 0.004]} c="#1A1214" rot={[0, 0, x > 0 ? 0.1 : -0.1]} /> : null}
    </group>
  );
};

const HairMessy: React.FC<{ c: string }> = ({ c }) => (
  <group>
    <mesh position={[0, 0.02, -0.012]} rotation={[-0.55, 0, 0]} scale={[1.09, 1.06, 1.09]}>
      <sphereGeometry args={[0.165, 36, 24, 0, TAU, 0, 1.78]} /><Mat c={c} side={THREE.DoubleSide} />
    </mesh>
    {/* fringe locks */}
    {[-0.09, -0.045, 0, 0.045, 0.09].map((x, i) => (
      <mesh key={i} position={[x * 1.08, 0.122 - Math.abs(x) * 0.25, 0.155 - Math.abs(x) * 0.32]} rotation={[0.3, 0, (i - 2) * 0.18 + (i % 2 ? 0.12 : -0.08)]} scale={[0.8, 1, 0.3]}>
        <coneGeometry args={[0.05, 0.1, 10]} /><Mat c={c} />
      </mesh>
    ))}
  </group>
);

/** short: one close cap with a soft hairline (default for adults) */
const HairShort: React.FC<{ c: string }> = ({ c }) => (
  <mesh position={[0, 0.025, -0.012]} rotation={[-0.62, 0, 0]} scale={[1.06, 1.04, 1.07]}>
    <sphereGeometry args={[0.165, 36, 24, 0, TAU, 0, 1.68]} /><Mat c={c} side={THREE.DoubleSide} />
  </mesh>
);
/** pony: close cap + a side-swept fringe + a tie and a tail hanging down the back */
const HairPony: React.FC<{ c: string }> = ({ c }) => (
  <group>
    <HairShort c={c} />
    <Ball p={[0.035, 0.112, 0.118]} r={0.075} c={c} s={[1.25, 0.42, 0.55]} rot={[0.5, 0, -0.32]} />
    <Ball p={[0, 0.06, -0.172]} r={0.034} c={c} />
    <Cap p={[0, -0.06, -0.205]} r={0.04} l={0.17} c={c} rot={[0.28, 0, 0]} s={[1, 1, 0.8]} />
  </group>
);

/** cone lock pointing along dir (from its base), used for spiky hair */
const Lock: React.FC<{ p: V3; dir: V3; r: number; l: number; c: string; flat?: number }> = ({ p, dir, r, l, c, flat = 0.45 }) => {
  const q = React.useMemo(() => new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(...dir).normalize()), [dir]);
  const d = new THREE.Vector3(...dir).normalize().multiplyScalar(l / 2);
  return <mesh position={[p[0] + d.x, p[1] + d.y, p[2] + d.z]} quaternion={q} scale={[1, 1, flat]}><coneGeometry args={[r, l, 8]} /><Mat c={c} /></mesh>;
};
/** spiky: full cap + heavy pointed fringe + crown/side spikes */
const HairSpiky: React.FC<{ c: string }> = ({ c }) => (
  <group>
    <mesh position={[0, 0.03, -0.015]} rotation={[-0.45, 0, 0]} scale={[1.16, 1.12, 1.14]}>
      <sphereGeometry args={[0.165, 36, 24, 0, TAU, 0, 1.75]} /><Mat c={c} side={THREE.DoubleSide} />
    </mesh>
    {/* fringe: long locks hanging over the forehead */}
    {[-0.12, -0.075, -0.03, 0.015, 0.06, 0.105].map((x, i) => (
      <Lock key={i} p={[x, 0.15 - Math.abs(x) * 0.3, 0.12 - Math.abs(x) * 0.25]} dir={[x * 0.8 + (i % 2 ? 0.05 : -0.04), -1, 0.32]} r={0.05} l={0.12 + (i === 2 ? 0.05 : 0)} c={c} />
    ))}
    {/* side locks over the temples */}
    {[-1, 1].map((sd) => <Lock key={`t${sd}`} p={[sd * 0.17, 0.06, 0.02]} dir={[sd * 0.2, -1, 0.1]} r={0.04} l={0.08} c={c} />)}
    {/* crown + back spikes pointing outward */}
    {[[-0.07, 0.19, -0.04, -0.5, 0.6, -0.6], [0.06, 0.19, -0.05, 0.5, 0.6, -0.6], [0.0, 0.19, -0.1, 0.05, 0.7, -0.8], [-0.15, 0.13, -0.06, -1, 0.5, -0.3], [0.15, 0.13, -0.06, 1, 0.5, -0.3], [-0.07, 0.1, -0.17, -0.4, 0.2, -1], [0.07, 0.1, -0.17, 0.4, 0.2, -1], [0, 0.0, -0.18, 0, -0.4, -1]].map(([x, y, z, a, b, d], i) => (
      <Lock key={`s${i}`} p={[x * 0.9, y * 0.9, z * 0.9]} dir={[a, b, d]} r={0.045} l={0.06} c={c} />
    ))}
  </group>
);

const HairBob: React.FC<{ c: string; r?: number; len?: number }> = ({ c, r = 0.45, len = 0.16 }) => (
  <group>
    {/* one shell: crown + straight sides/back, open at the face (len = how far below the head centre it hangs) */}
    <Lathe pts={[[0.2, -len], [0.198, -len / 2], ...BOB_PTS.slice(2)]} c={c} r={r} ph0={0.95} ph={TAU - 1.9} />
    {/* blunt fringe across the forehead */}
    <Lathe pts={FRINGE_PTS} c={c} r={r} ph0={-1.0} ph={2.0} />
  </group>
);

const Head: React.FC<{ L: Look; p: Pose; f: number; seed: number }> = ({ L, p, f, seed }) => {
  const blink = Math.max(p.blink ?? 0, blinkAt(f, seed));
  const look = p.look ?? [0, 0];
  const mo = p.mouth ?? 0;
  return (
    <group>
      <Ball r={0.16} c={L.skin} s={L.fangs ? [0.9, 1.13, 0.97] : [1, 1.06, 0.98]} />
      {[-1, 1].map((sd) => <Ball key={sd} p={[sd * 0.158, -0.005, -0.005]} r={0.032} c={L.skin} s={[0.45, 1, 0.75]} />)}
      <Eye x={-0.058} L={L} blink={blink} look={look} />
      <Eye x={0.058} L={L} blink={blink} look={look} />
      {L.fangs ? null : [-1, 1].map((sd) => <Box key={sd} p={[sd * 0.06, 0.056 + (p.browUp ?? 0) * 0.012, 0.15]} s={[0.05, 0.009, 0.01]} c={L.brow} rot={[0, sd * 0.25, sd * (L.hair === "bob" ? -0.08 : 0.12) * (1 - (p.browUp ?? 0))]} />)}
      <Ball p={[0, -0.03, 0.156]} r={0.012} c={L.skin} s={[0.85, 0.75, 0.8]} />
      {/* mouth */}
      {L.lips ? <Cap p={[0, -0.085, 0.142]} r={0.008} l={0.03} c={L.lips} rot={[0, 0, Math.PI / 2]} /> : null}
      <Ball p={[0, -0.085 - mo * 0.006, 0.143]} r={0.016} c="#3B1E22" s={[1.25 - mo * 0.3, 0.18 + mo * 0.9, 0.4]} />
      {p.blood ? <>
        {/* blood round the lips and a drip off the chin */}
        <Ball p={[0.006, -0.094, 0.142]} r={0.017} c="#7A0C14" s={[1.4, 0.6, 0.3]} />
        <Ball p={[-0.02, -0.088, 0.146]} r={0.007} c="#7A0C14" s={[1, 0.8, 0.3]} />
        <Box p={[0.012, -0.125, 0.147]} s={[0.008, 0.045, 0.004]} c="#7A0C14" />
      </> : null}
      {L.fangs ? [-1, 1].map((sd) => <mesh key={sd} position={[sd * 0.011, -0.093, 0.149]} rotation={[Math.PI, 0, 0]}><coneGeometry args={[0.0035, 0.012, 6]} /><Mat c="#F6F4EE" /></mesh>) : null}
      {L.hair === "short" ? <HairShort c={L.hairC} /> : L.hair === "pony" ? <HairPony c={L.hairC} /> : L.hair === "messy" ? <HairMessy c={L.hairC} /> : L.hair === "spiky" ? <HairSpiky c={L.hairC} /> : <HairBob c={L.hairC} r={L.hairR} len={L.hairLen} />}
      {L.band ? <mesh position={[0, 0.1, 0.0]} rotation={[Math.PI / 2 - 0.12, 0, 0]} scale={[1, 1, 2.2]}><torusGeometry args={[0.186, 0.013, 10, 40]} /><Mat c={L.band} /></mesh> : null}
      {L.clip ? <Box p={[0.15, 0.12, 0.07]} s={[0.014, 0.03, 0.065]} c={L.clip} rot={[0.3, 0.6, -0.6]} /> : null}
      {L.glasses ? <group position={[0, -0.005, 0.158]}>
        {[-1, 1].map((sd) => <mesh key={sd} position={[sd * 0.058, 0, 0]}><torusGeometry args={[0.04, 0.005, 8, 28]} /><Mat c="#2A2A2E" /></mesh>)}
        <Box p={[0, 0.006, 0]} s={[0.036, 0.006, 0.006]} c="#2A2A2E" />
      </group> : null}
    </group>
  );
};

const Arm: React.FC<{ side: 1 | -1; L: Look; B: Build; sh: V3; el: number; hold?: Look["holdR"]; bruise?: number }> = ({ side, L, B, sh, el, hold, bruise = 0 }) => {
  const short = L.outfit === "scrubs" || L.outfit === "uniform" || L.outfit === "blouse" || L.outfit === "jersey" || L.outfit === "tee";
  const sleeve = short ? L.skin : L.top;
  const a = B.arm, w = B.limb, hw = 0.5 + 0.5 * w;
  const hand = -(0.17 * a + 0.046 * w) - 0.05; // hand centre, just past the forearm
  return (
    <group position={[side * 0.215 * B.girth, 0.33 * B.torso, 0]} rotation={sh}>
      {short ? <Cap p={[0, -0.06 * a, 0]} r={0.054 * w} l={0.05 * a} c={L.top} /> : null}
      <Cap p={[0, -0.11 * a, 0]} r={(L.outfit === "hoodie" ? 0.058 : 0.05) * w} l={0.15 * a} c={sleeve} />
      <group position={[0, -0.24 * a, 0]} rotation={[el, 0, 0]}>
        <Cap p={[0, -0.1 * a, 0]} r={(L.outfit === "hoodie" ? 0.054 : 0.046) * w} l={0.14 * a} c={sleeve} />
        {L.outfit === "hoodie" ? <Cap p={[0, -0.2 * a, 0]} r={0.056 * w} l={0.015} c="#B48834" /> : null}
        <Ball p={[0, hand, 0.005]} r={0.058 * hw} c={L.skin} s={[0.8, 1.1, 0.62]} />
        <Cap p={[-side * 0.038 * hw, hand + 0.02, 0.025]} r={0.018 * hw} l={0.035 * hw} c={L.skin} rot={[0.3, 0, side * 0.6]} />
        {bruise > 0 ? <Ball p={[0, -0.1 * a, 0.044 * w]} r={0.03} c="#6A4A7E" s={[1, 1.4 * bruise, 0.2]} /> : null}
        {hold ? <group position={[0, hand + 0.27, 0]}><HoldProp kind={hold} /></group> : null}
      </group>
    </group>
  );
};

/** prop held in the hand (hand centre at y=-0.27 of this group) */
const HoldProp: React.FC<{ kind: NonNullable<Look["holdR"]> }> = ({ kind }) => {
  if (kind === "tape") return <group position={[0, -0.3, 0.05]}><Box s={[0.13, 0.085, 0.022]} c="#1E1E22" /><Box p={[0, 0.005, 0.012]} s={[0.1, 0.04, 0.004]} c="#E9E4D6" />{[-1, 1].map((sd) => <Disc key={sd} p={[sd * 0.025, 0.005, 0.0145]} r={0.011} c="#3A3A40" />)}</group>;
  if (kind === "keys") return <group position={[0, -0.33, 0.03]}><mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.025, 0.005, 6, 18]} /><Mat c="#C9CDD2" r={0.3} /></mesh>{[-0.02, 0.0, 0.02].map((x, i) => <Box key={i} p={[x, -0.045, 0]} s={[0.012, 0.06, 0.004]} c={i === 1 ? "#D9B24A" : "#B8BEC4"} rot={[0, 0, x * 8]} />)}</group>;
  /* phone: dark slab, lit screen facing the character */
  if (kind === "phone") return <group position={[0, -0.29, 0.05]} rotation={[-0.9, 0, 0]}><Box s={[0.075, 0.15, 0.01]} c="#1A1B1F" /><Box p={[0, 0, -0.0055]} s={[0.066, 0.135, 0.002]} c="#BFD6F2" e="#BFD6F2" ei={0.9} /></group>;
  /* flashlight: body along the forearm direction, glowing lens at the tip */
  return (
    <group position={[0, -0.3, 0.04]} rotation={[Math.PI / 2, 0, 0]}>
      <mesh><cylinderGeometry args={[0.02, 0.018, 0.16, 16]} /><Mat c="#2A2C31" r={0.5} /></mesh>
      <mesh position={[0, 0.095, 0]}><cylinderGeometry args={[0.028, 0.021, 0.04, 16]} /><Mat c="#3A3D44" r={0.4} /></mesh>
      <mesh position={[0, 0.116, 0]} rotation={[-Math.PI / 2, 0, 0]}><circleGeometry args={[0.024, 20]} /><meshStandardMaterial color="#FFF4D6" emissive="#FFF4D6" emissiveIntensity={1.6} /></mesh>
    </group>
  );
};

const Leg: React.FC<{ side: 1 | -1; L: Look; B: Build; hip: V3; kn: number }> = ({ side, L, B, hip, kn }) => {
  const boot = L.outfit === "coat";
  const k = B.leg, w = B.limb, fw = 0.5 + 0.5 * w;
  return (
    <group position={[side * 0.09 * B.girth, 0, 0]} rotation={hip}>
      <Cap p={[0, -0.17 * k, 0]} r={0.075 * w} l={0.22 * k} c={L.pants} />
      <group position={[0, -0.34 * k, 0]} rotation={[kn, 0, 0]}>
        <Cap p={[0, -0.16 * k, 0]} r={(boot ? 0.07 : 0.066) * w} l={0.22 * k} c={boot ? L.shoes : L.pants} />
        {L.outfit === "hoodie" ? <Cap p={[0, -0.27 * k, 0]} r={0.07 * w} l={0.02} c="#3E5A80" /> : null}
        {L.socks ? <Cap p={[0, -0.27 * k, 0]} r={0.068 * w} l={0.04} c={L.socks} /> : null}
        <group position={[0, -0.33 * k, 0]} rotation={[-kn * 0.3, 0, 0]}>
          <Cap p={[0, -0.02, 0.04]} r={0.06 * fw} l={0.12} c={L.shoes} rot={[Math.PI / 2, 0, 0]} s={[1.05, 1, 0.8]} />
          <Cap p={[0, -0.065, 0.04]} r={0.058 * fw} l={0.13} c={L.sole ?? (L.outfit === "coat" ? "#0E0E11" : "#D9D6CF")} rot={[Math.PI / 2, 0, 0]} s={[1.05, 1, 0.3]} />
        </group>
      </group>
    </group>
  );
};

const Torso: React.FC<{ L: Look }> = ({ L }) => (
  <group>
    <Lathe pts={L.outfit === "coat" ? COAT_PTS : L.outfit === "scrubs" ? SCRUB_PTS : TORSO_PTS} c={L.top} s={[1, 1, 0.74]} />
    <Ball p={[0, -0.02, 0]} r={0.15} c={L.pants} s={[1.05, 0.5, 0.78]} />
    {L.outfit === "hoodie" ? <>
      <mesh position={[0, 0.39, -0.04]} rotation={[-1.4, 0, 0]} scale={[1.15, 1, 0.8]}><torusGeometry args={[0.105, 0.05, 14, 30, Math.PI]} /><Mat c={L.top} /></mesh>
      <Ball p={[0, 0.42, -0.13]} r={0.1} c={L.top} s={[1.1, 0.8, 0.55]} />
      <Box p={[0, 0.07, 0.152]} s={[0.24, 0.11, 0.012]} c="#B48834" />
      {[-1, 1].map((sd) => <Cap key={sd} p={[sd * 0.04, 0.29, 0.146]} r={0.007} l={0.09} c="#EDE7D6" />)}
      <mesh position={[0, -0.025, 0]} scale={[1, 1, 0.75]}><cylinderGeometry args={[0.213, 0.21, 0.05, 32]} /><Mat c="#B48834" /></mesh>
    </> : null}
    {L.outfit === "coat" ? <>
      <mesh position={[0, 0.52, 0]}><cylinderGeometry args={[0.075, 0.1, 0.13, 20]} /><Mat c={L.top} /></mesh>
      {[0.32, 0.2, 0.08, -0.04].map((y) => <Ball key={y} p={[0.03, y, 0.152]} r={0.009} c="#3A3B42" />)}
    </> : null}
    {L.outfit === "uniform" || L.outfit === "shirt" ? <>
      {/* collar, button line, belt */}
      {[-1, 1].map((sd) => <Box key={sd} p={[sd * 0.045, 0.385, 0.1]} s={[0.07, 0.012, 0.06]} c={L.top} rot={[0.5, sd * 0.5, sd * -0.35]} />)}
      <Box p={[0, 0.2, 0.154]} s={[0.006, 0.36, 0.004]} c="#C9CCCA" />
      {[0.32, 0.22, 0.12, 0.02].map((y) => <Ball key={y} p={[0, y, 0.156]} r={0.006} c="#DADCDA" />)}
      <mesh position={[0, -0.025, 0]} scale={[1, 1, 0.75]}><cylinderGeometry args={[0.214, 0.212, 0.035, 32]} /><Mat c="#141416" /></mesh>
      <Box p={[0, -0.025, 0.16]} s={[0.04, 0.03, 0.01]} c="#B9B39A" />
      {L.trim && L.outfit === "uniform" ? <Box p={[0.085, 0.27, 0.15]} s={[0.05, 0.012, 0.004]} c={L.trim} /> : null}
      {L.outfit === "shirt" ? <Box p={[-0.085, 0.27, 0.149]} s={[0.07, 0.06, 0.006]} c="#9AB6CF" /> : null}
    </> : null}
    {L.backpack ? <>
      <Box p={[0, 0.2, -0.2]} s={[0.3, 0.36, 0.13]} c={L.backpack} />
      <Box p={[0, 0.1, -0.27]} s={[0.22, 0.14, 0.04]} c={L.backpack} />
      {[-1, 1].map((sd) => <Box key={sd} p={[sd * 0.1, 0.22, 0.0]} s={[0.035, 0.42, 0.33]} c={L.outfit === "jersey" ? L.backpack! : "#22305A"} rot={[0, 0, 0]} />)}
    </> : null}
    {L.outfit === "blouse" ? <>
      <Lathe pts={SKIRT_PTS} c={L.trim ?? "#24346A"} s={[1, 1, 0.8]} />
      {/* ribbon bow at the collar */}
      <Ball p={[0, 0.37, 0.12]} r={0.022} c={L.trim ?? "#24346A"} s={[1, 0.8, 0.6]} />
      {[-1, 1].map((sd) => <mesh key={sd} position={[sd * 0.04, 0.37, 0.115]} rotation={[0, 0, sd * -Math.PI / 2]}><coneGeometry args={[0.03, 0.06, 4]} /><Mat c={L.trim ?? "#24346A"} /></mesh>)}
      {[-1, 1].map((sd) => <Box key={sd} p={[sd * 0.02, 0.31, 0.135]} s={[0.022, 0.08, 0.008]} c={L.trim ?? "#24346A"} rot={[0.2, 0, sd * 0.25]} />)}
    </> : null}
    {L.outfit === "tee" ? <mesh position={[0, 0.395, 0.0]} rotation={[Math.PI / 2 - 0.15, 0, 0]} scale={[1, 0.8, 1]}><torusGeometry args={[0.075, 0.012, 8, 28]} /><Mat c={L.trim ?? L.top} /></mesh> : null}
    {L.outfit === "jersey" ? <>
      <mesh position={[0, 0.385, 0.112]} rotation={[0.35, 0, Math.PI]}><circleGeometry args={[0.04, 3]} /><Mat c="#3E7F7C" /></mesh>
      {[-1, 1].map((sd) => <Box key={sd} p={[sd * 0.2, 0.17, 0]} s={[0.012, 0.3, 0.12]} c="#F2F2EE" />)}
    </> : null}
    {L.outfit === "scrubs" ? <>
      <mesh position={[0, 0.4, 0.105]} rotation={[0.25, 0, Math.PI]}><circleGeometry args={[0.055, 3]} /><Mat c="#3C7C78" /></mesh>
      <mesh position={[0, 0.36, 0.06]} rotation={[0.55, 0, 0]}><torusGeometry args={[0.11, 0.004, 6, 30, Math.PI]} /><Mat c="#2A4A7A" /></mesh>
      <Box p={[0.0, 0.2, 0.153]} s={[0.05, 0.07, 0.006]} c="#F2F2EE" rot={[0.05, 0, 0]} />
      <Box p={[0.08, 0.25, 0.146]} s={[0.07, 0.06, 0.01]} c="#447F7B" />
    </> : null}
  </group>
);

/** back = anything mounted on the upper back (a pet in a backpack, a tank, wings). It follows the spine. */
export type CharProps = { L: Look; p?: V3; ry?: number; pose?: Pose; seed?: number; scale?: number; back?: React.ReactNode };

/** the character. Idle breathing + blinking are always on; give every character its own seed so they do not blink together. */
export const Char: React.FC<CharProps> = ({ L, p = [0, 0, 0], ry = 0, pose = REST, seed = 0, scale = 1, back }) => {
  const f = useCurrentFrame();
  const P = { ...REST, ...pose };
  const B = L.build ?? SLIM;
  const br = Math.sin(f / 24 + seed) * 0.008;
  const nk = B.neck, top = 0.4 * B.torso;
  return (
    <group position={p} rotation={[0, ry, 0]} scale={L.height * scale}>
      {/* pose.y is in leg units, so crouch / sit work for any leg length */}
      <group position={[0, hipHeight(B) + (P.y ?? 0) * B.leg, 0]}>
        <Leg side={1} L={L} B={B} hip={P.hipL ?? [0, 0, 0.02]} kn={P.knL ?? 0.04} />
        <Leg side={-1} L={L} B={B} hip={P.hipR ?? [0, 0, -0.02]} kn={P.knR ?? 0.04} />
        <group rotation={P.spine ?? [0, 0, 0]} scale={[1 + br, 1, 1 + br]}>
          <group scale={[B.girth, B.torso, B.girth]}>
            <Torso L={L} />
            {P.blood ? <>
              {/* optional gore (pose.blood): collar ring + drip, inside the torso group so it follows the body */}
              <mesh position={[0, 0.39, 0]} rotation={[Math.PI / 2, 0, 0]} scale={[1.05, 0.82, 1]}><torusGeometry args={[0.1, 0.026, 8, 24]} /><Mat c="#6E0A10" /></mesh>
              <Ball p={[0.02, 0.36, 0.118]} r={0.07} c="#6E0A10" s={[1.25 * P.blood, 0.55, 0.45]} />
              <Box p={[0.04 - (seed % 3) * 0.025, 0.24, 0.151]} s={[0.035, 0.2 * P.blood, 0.006]} c="#6E0A10" />
            </> : null}
          </group>
          {back ? <group position={[0, top, -0.2 * B.girth]}>{back}</group> : null}
          <Arm side={1} L={L} B={B} sh={P.handNeckL ? lerp3(P.shL ?? [0, 0, 0.12], [-2.25, -0.35, 0.55], P.handNeckL) : P.shL ?? [0, 0, 0.12]} el={P.handNeckL ? (P.elL ?? -0.15) + (-2.05 - (P.elL ?? -0.15)) * P.handNeckL : P.elL ?? -0.15} bruise={P.bruise} />
          <Arm side={-1} L={L} B={B} sh={P.handNeckR ? [-2.3, 0.3, -0.75] : P.shR ?? [0, 0, -0.12]} el={P.handNeckR ? -2.0 : P.elR ?? -0.15} hold={P.holdOff ? undefined : L.holdR} />
          <group position={[0, top, 0]}>
            <mesh position={[0, 0.06 * nk - 0.02, 0]}><cylinderGeometry args={[0.05 * (0.5 + 0.5 * B.limb), 0.055 * (0.5 + 0.5 * B.limb), 0.12 * nk, 16]} /><Mat c={L.skin} /></mesh>
            {L.phones ? <group position={[0, 0.02, 0.01]}><mesh rotation={[Math.PI / 2 - 0.2, 0, 0]} scale={[1, 1.15, 1]}><torusGeometry args={[0.1, 0.014, 8, 30, Math.PI]} /><Mat c={L.phones} /></mesh>{[-1, 1].map((sd) => <mesh key={sd} position={[sd * 0.1, 0, 0.02]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.045, 0.045, 0.035, 20]} /><Mat c={L.phones!} /></mesh>)}</group> : null}
            {L.patch ? <Box p={[0.05, 0.05, 0.02]} s={[0.006, 0.05, 0.05]} c="#F6F6F2" rot={[0, 0.5, 0]} /> : null}
            {P.bite ? <group position={[0.041, 0.055, 0.03]} rotation={[0, 0.95, 0]}>
              {[-1, 1].map((k) => <React.Fragment key={k}><Disc p={[0, k * 0.011, 0.001]} r={0.0075} c="#C0303A" /><Disc p={[0, k * 0.011, 0.0015]} r={0.0048} c="#3A060C" /></React.Fragment>)}
              {[-1, 1].map((k) => <Cap key={k} p={[0, k * 0.011 - 0.012 * P.bite!, 0.002]} r={0.0028} l={0.024 * P.bite!} c="#8E1018" s={[1, 1, 0.5]} />)}
            </group> : null}
            {P.cloth ? <group position={[0.045, 0.05, 0.03]} rotation={[0, 0.95, 0.1]}>
              <Box s={[0.075, 0.07, 0.012]} c="#F4F2EC" />
              <Disc p={[0, 0, 0.0065]} r={0.008 + 0.022 * P.cloth} c="#A3121C" />
            </group> : null}
            <group position={[0, 0.08 + 0.12 * (nk - 1), 0]} rotation={P.head ?? [0, 0, 0]}>
              <group position={[0, 0.2 * (L.headS ?? 0.95) / 1.42, 0]} scale={L.headS ?? 0.95}><Head L={L} p={P} f={f} seed={seed} /></group>
            </group>
          </group>
        </group>
      </group>
    </group>
  );
};

/** world height of the head centre (for framing face close-ups) and the head radius in metres */
export const headCenter = (L: Look): number => {
  const B = L.build ?? SLIM;
  return L.height * (hipHeight(B) + 0.4 * B.torso + 0.08 + 0.12 * (B.neck - 1) + (0.2 * (L.headS ?? 0.95)) / 1.42);
};
export const headRadius = (L: Look): number => L.height * 0.16 * 1.06 * (L.headS ?? 0.95);
