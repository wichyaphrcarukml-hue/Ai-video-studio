import React from "react";
import { Bx, Cy, M, Sp, type V3 } from "../kit/three";

/** Pets (the sidekick that notices danger first). Same primitives as the people: capsule body, sphere head.
 *  Facing +z, feet at y=0. walk = phase, amp = stride; puff/ears react to danger. */

/* ─── cat ─── */
export type CatPose = { walk?: number; amp?: number; puff?: number; head?: [number, number]; tail?: number; crouch?: number; blink?: number; look?: [number, number] };
/** fur colours: change per pet (default = orange tabby, white chest + paw tips, red collar + gold bell) */
export type CatColors = { fur: string; stripe: string; chest: string; collar: string };
export const TABBY: CatColors = { fur: "#E6A26C", stripe: "#D08650", chest: "#F6F2EC", collar: "#A8323A" };
const PINK = "#E8A0A0", AMBER = "#D98E2E", MUZ = "#F2CBA8";
export const Cat: React.FC<{ p: V3; ry?: number; s?: number; pose?: CatPose; colors?: CatColors }> = ({ p, ry = 0, s = 1, pose = {}, colors = TABBY }) => {
  const ORANGE = colors.fur, STRIPE = colors.stripe, WHITE = colors.chest;
  const { walk = 0, amp = 0, puff = 0, head = [0, 0], tail = 0, crouch = 0, blink = 0, look = [0, 0] } = pose;
  const k = 1 + puff * 0.18; // fur puffs up
  const leg = (i: number) => Math.sin(walk + (i % 2 ? Math.PI : 0) + (i > 1 ? Math.PI / 2 : 0)) * 0.5 * amp;
  const by = 0.2 - crouch * 0.07;
  return (
    <group position={p} rotation={[0, ry, 0]} scale={s}>
      {/* body: capsule along z (head at +z) */}
      <group position={[0, by, 0]} scale={[k, k * (1 + puff * 0.1), 1]} rotation={[puff * -0.12, 0, 0]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}><capsuleGeometry args={[0.085, 0.11, 8, 16]} /><M c={ORANGE} /></mesh>
        {[-0.05, 0.02, 0.09].map((z) => <Bx key={z} p={[0, 0.083, z - 0.02]} s={[0.1, 0.012, 0.025]} c={STRIPE} />)}
        <Sp p={[0, -0.0, 0.1]} r={0.068} c={WHITE} sc={[0.95, 1.2, 0.6]} />
      </group>
      {/* legs: short capsules, white paw tips */}
      {([[-0.05, 0.08], [0.05, 0.08], [-0.05, -0.08], [0.05, -0.08]] as [number, number][]).map(([x, z], i) => (
        <group key={i} position={[x * k, by - 0.02, z]} rotation={[leg(i), 0, 0]}>
          <Cy p={[0, -0.075 + crouch * 0.02, 0]} r={0.028} h={0.14 - crouch * 0.05} c={ORANGE} />
          <Sp p={[0, -0.15 + crouch * 0.05, 0.008]} r={0.03} c={WHITE} sc={[1, 0.7, 1.2]} />
        </group>
      ))}
      {/* tail: two tapered segments, up when puffed */}
      <group position={[0, by + 0.04, -0.15]} rotation={[1.1 + puff * 0.4 + Math.sin(tail) * 0.15, Math.sin(tail * 0.7) * 0.4, 0]}>
        <Cy p={[0, 0, -0.12]} r={0.02 * k} r2={0.03 * k} h={0.25} c={ORANGE} rx={Math.PI / 2} />
        <Sp p={[0, 0, -0.245]} r={0.02 * k} c={STRIPE} />
      </group>
      {/* collar + bell */}
      <mesh position={[0, by + 0.07, 0.12]} rotation={[Math.PI / 2 - 0.5, 0, 0]}><torusGeometry args={[0.055, 0.012, 6, 20]} /><M c={colors.collar} /></mesh>
      <Sp p={[0, by + 0.035, 0.155]} r={0.017} c="#D9B24A" />
      {/* head: big round sphere */}
      <group position={[0, by + 0.2, 0.15]} rotation={[head[1], head[0], 0]}>
        <Sp r={0.13} c={ORANGE} sc={[1.08, 0.97, 0.95]} />
        <Sp p={[0, -0.045, 0.1]} r={0.04} c={MUZ} sc={[1.3, 0.75, 0.7]} />
        <Sp p={[0, -0.022, 0.13]} r={0.011} c={PINK} sc={[1.3, 0.8, 0.8]} />
        {[-1, 1].map((sd) => (
          <group key={sd}>
            {/* ears: cones, flatten back when puffed */}
            <group position={[sd * 0.08, 0.125, -0.01]} rotation={[-0.15 - puff * 0.7, 0, sd * (-0.35 - puff * 0.5)]}>
              <mesh><coneGeometry args={[0.048, 0.1, 4]} /><M c={ORANGE} /></mesh>
              <mesh position={[0, -0.005, 0.012]} scale={[0.6, 0.7, 0.4]}><coneGeometry args={[0.048, 0.1, 4]} /><M c={PINK} /></mesh>
            </group>
            {/* eyes: amber, vertical pupil (dilates when scared) */}
            <group position={[sd * 0.05, 0.01, 0.105]}>
              <Sp r={0.034} c={AMBER} sc={[1, 1 - blink * 0.9, 0.5]} />
              {blink < 0.7 ? <Sp p={[look[0] * 0.008, look[1] * 0.008, 0.016]} r={0.023} sc={[0.3 + puff * 0.5, 1 - blink, 0.25]} c="#121212" /> : null}
              <Sp p={[0.01, 0.014, 0.021]} r={0.006} c="#FFFFFF" />
            </group>
          </group>
        ))}
        {[-1, 1].map((sd) => [-0.006, 0.006].map((y) => <Bx key={`${sd}${y}`} p={[sd * 0.085, -0.035 + y, 0.095]} s={[0.06, 0.002, 0.002]} c="#F4F0E8" rz={sd * y * 20} ry={sd * 0.4} />))}
      </group>
    </group>
  );
};


/* ─── puppy ─── */
const CREAM = "#F1E6D2", BROWN = "#B98A5E", NOSE = "#1A1416";
export type DogPose = { walk?: number; amp?: number; head?: [number, number]; tail?: number; lick?: number; whine?: number };
export const Dog: React.FC<{ p: V3; ry?: number; s?: number; pose?: DogPose; headOnly?: boolean }> = ({ p, ry = 0, s = 1, pose = {}, headOnly }) => {
  const { walk = 0, amp = 0, head = [0, 0], tail = 0, lick = 0, whine = 0 } = pose;
  const leg = (i: number) => Math.sin(walk + (i % 2 ? Math.PI : 0) + (i > 1 ? Math.PI / 2 : 0)) * 0.5 * amp;
  const by = 0.17;
  const Head = (
    <group position={headOnly ? [0, 0, 0] : [0, by + 0.17, 0.13]} rotation={[head[1], head[0], whine * 0.15 * Math.sin(walk * 3)]}>
      <Sp r={0.12} c={CREAM} sc={[1.08, 0.98, 0.98]} />
      <Sp p={[0, -0.04, 0.095]} r={0.05} c={CREAM} sc={[1.2, 0.8, 0.9]} />
      <Sp p={[0, -0.02, 0.14]} r={0.018} c={NOSE} sc={[1.3, 0.9, 0.9]} />
      {/* patch over the left eye (character's left = +x) */}
      <Sp p={[0.045, 0.025, 0.085]} r={0.05} c={BROWN} sc={[1, 1, 0.45]} />
      {[-1, 1].map((sd) => (
        <group key={sd}>
          <group position={[sd * 0.042, 0.02, 0.108]}>
            <Sp r={0.02} c="#151214" sc={[1, 1.15, 0.6]} />
            <Sp p={[0.006, 0.008, 0.01]} r={0.0055} c="#FFFFFF" />
          </group>
          {/* floppy ear */}
          <group position={[sd * 0.105, 0.06, -0.01]} rotation={[0.1, 0, sd * (0.35 + 0.1 * Math.sin(walk))]}>
            <Sp p={[sd * 0.01, -0.06, 0]} r={0.05} c={BROWN} sc={[0.55, 1.3, 0.35]} />
          </group>
        </group>
      ))}
      <Sp p={[0, -0.075, 0.105]} r={0.012} c="#3B1E22" sc={[1.4, 0.4 + whine * 0.6, 0.5]} />
      {lick > 0 ? <Sp p={[0, -0.09, 0.12 + lick * 0.02]} r={0.016} c="#E58A94" sc={[1, 0.5, 1.3]} /> : null}
    </group>
  );
  if (headOnly) return <group position={p} rotation={[0, ry, 0]} scale={s}>{Head}</group>;
  return (
    <group position={p} rotation={[0, ry, 0]} scale={s}>
      <group position={[0, by, 0]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}><capsuleGeometry args={[0.08, 0.1, 8, 16]} /><meshStandardMaterial color={CREAM} roughness={0.9} /></mesh>
        <Sp p={[-0.03, 0.06, -0.04]} r={0.045} c={BROWN} sc={[1, 0.5, 1.2]} />
      </group>
      {([[-0.05, 0.07], [0.05, 0.07], [-0.05, -0.07], [0.05, -0.07]] as [number, number][]).map(([x, z], i) => (
        <group key={i} position={[x, by - 0.03, z]} rotation={[leg(i), 0, 0]}>
          <Cy p={[0, -0.06, 0]} r={0.028} h={0.11} c={CREAM} />
          <Sp p={[0, -0.12, 0.008]} r={0.03} c={CREAM} sc={[1, 0.7, 1.2]} />
        </group>
      ))}
      <group position={[0, by + 0.05, -0.13]} rotation={[0.9, Math.sin(tail) * 0.6, 0]}>
        <Cy p={[0, 0, -0.06]} r={0.015} r2={0.025} h={0.12} c={CREAM} rx={Math.PI / 2} />
      </group>
      <mesh position={[0, by + 0.09, 0.1]} rotation={[Math.PI / 2 - 0.4, 0, 0]}><torusGeometry args={[0.055, 0.007, 6, 20]} /><meshStandardMaterial color="#B3262E" /></mesh>
      {Head}
    </group>
  );
};
