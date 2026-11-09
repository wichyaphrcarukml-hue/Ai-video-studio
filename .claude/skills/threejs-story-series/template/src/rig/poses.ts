import type { Pose, V3 } from "./char";

/** walk stride (metres per full cycle) for the default SLIM build; scale it with build.leg for other builds */
export const WALK_STRIDE = 1.2;
/** walk cycle. ph = phase in radians; advance it by distance (ph = dist / WALK_STRIDE * 2π) so feet do not skate */
export function walkPose(ph: number, amp = 1): Pose {
  const s = Math.sin(ph), c = Math.cos(ph);
  return {
    hipL: [s * 0.42 * amp, 0, 0], hipR: [-s * 0.42 * amp, 0, 0],
    knL: Math.max(0, -c) * 0.75 * amp + 0.05, knR: Math.max(0, c) * 0.75 * amp + 0.05,
    shL: [-s * 0.38 * amp, 0, 0.1], shR: [s * 0.38 * amp, 0, -0.1], elL: -0.35, elR: -0.35,
    y: Math.abs(c) * 0.025 * amp, spine: [0.04, s * 0.05 * amp, 0], head: [0, -s * 0.04 * amp, 0],
  };
}

/** one run stride ≈ 2.5 m of ground per full cycle for the default SLIM build (scale with build.leg) */
export const RUN_STRIDE = 2.5;
/** run cycle driven by DISTANCE travelled (metres), not by frame: phase = dist / stride, so the feet never slide.
 *  ph0 = per-character offset so a group never runs in lock-step; amp 0..1 lets a runner slow to a stop. */
export function runPose(dist: number, ph0 = 0, amp = 1): Pose {
  const ph = (dist / RUN_STRIDE) * Math.PI * 2 + ph0, s = Math.sin(ph), c = Math.cos(ph);
  return {
    hipL: [-0.8 * s * amp, 0, 0.05], hipR: [0.8 * s * amp, 0, -0.05],
    knL: 0.15 + 1.5 * Math.max(0, c) * amp, knR: 0.15 + 1.5 * Math.max(0, -c) * amp,
    shL: [0.95 * s * amp, 0, 0.18], shR: [-0.95 * s * amp, 0, -0.18], elL: -1.45, elR: -1.45,
    y: (Math.abs(c) * 0.07 - 0.03) * amp, spine: [0.3 * amp + 0.05, s * 0.12 * amp, 0], head: [-0.2 * amp, -s * 0.06 * amp, 0],
    browUp: 0.9, mouth: 0.3 * amp, blink: 0,
  };
}

/** crouched low (hiding under a window, behind a desk) */
export const CROUCH: Pose = { hipL: [-2.1, 0, 0.12], hipR: [-2.1, 0, -0.12], knL: 2.4, knR: 2.4, y: -0.42, spine: [0.45, 0, 0], shL: [-1.15, 0, 0.35], shR: [-1.15, 0, -0.35], elL: -1.5, elR: -1.5, head: [-0.2, 0, 0] };
/** sitting on a chair / bed edge (seat height ≈ 0.45 for SLIM at height 0.88; y is in leg units) */
export const SIT: Pose = { hipL: [-1.5, 0, 0.08], hipR: [-1.5, 0, -0.08], knL: 1.5, knR: 1.5, y: -0.3, spine: [0.05, 0, 0], shL: [-0.35, 0, 0.15], shR: [-0.35, 0, -0.15], elL: -0.9, elR: -0.9 };
/** knocking with the right fist; k = 0..1 (drive it with a sine for repeated knocks) */
export const knockPose = (k: number): Pose => ({ shR: [-1.55 + k * 0.25, 0, -0.15], elR: -1.7 + k * 0.3, head: [-0.05, 0, 0] });
/** reaching forward with the right hand (door handle, a light switch) */
export const reachPose = (k: number): Pose => ({ shR: [-1.5 * k, 0, -0.1], elR: -0.25, spine: [0.1 * k, 0, 0] });
/** listening: hand cupped behind the ear, head tilted. Arm poses that touch the face are solved for the SLIM build:
 *  re-check them on Turn / a still if you change build.arm or headS. */
export const LISTEN: Pose = { shR: [-2.3, 0, -0.1], elR: -1.9, head: [-0.1, 0.25, 0.12], browUp: 0.6, look: [0.4, 0] };
/** hands over the mouth (stifling a scream) */
export const HUSH: Pose = { shL: [-1.6, -0.2, -0.4], shR: [-1.6, 0.2, 0.4], elL: -1.9, elR: -1.9, browUp: 1, blink: 0 };
/** zombie shamble: arms forward, head down. ph = phase */
export const shamblePose = (ph: number): Pose => ({ ...walkPose(ph, 0.35), shL: [-1.4, 0, 0.1], shR: [-1.5, 0, -0.1], elL: -0.2, elR: -0.3, spine: [0.25, 0, 0], head: [0.3, Math.sin(ph * 0.5) * 0.15, 0.1], mouth: 0.4 });

/** blend two poses (numbers lerp, missing fields fall back to the other pose) */
export function blendPose(a: Pose, b: Pose, k: number): Pose {
  const out: Record<string, unknown> = { ...a };
  for (const key of Object.keys(b) as (keyof Pose)[]) {
    const va = a[key], vb = b[key];
    if (typeof vb === "number") out[key] = (typeof va === "number" ? va : 0) + (vb - (typeof va === "number" ? va : 0)) * k;
    else if (Array.isArray(vb) && vb.length === 3) {
      const A = (Array.isArray(va) ? va : [0, 0, 0]) as V3;
      out[key] = [0, 1, 2].map((i) => A[i] + ((vb as V3)[i] - A[i]) * k);
    } else out[key] = k < 0.5 && va !== undefined ? va : vb;
  }
  return out as Pose;
}
