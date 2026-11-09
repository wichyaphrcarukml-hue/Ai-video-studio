import React from "react";
import * as THREE from "three";
import { useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { TiltShift } from "./ui";

/** 3D building blocks. Units = metres. Matte materials only (the look is flat, low-key, no outlines). */
export type V3 = [number, number, number];

export const M: React.FC<{ c: string; e?: string; ei?: number; r?: number; o?: number; side?: THREE.Side }> = ({ c, e, ei = 0, r = 0.9, o = 1, side }) => (
  <meshStandardMaterial color={c} roughness={r} metalness={0} emissive={e ?? "#000"} emissiveIntensity={ei} transparent={o < 1} opacity={o} side={side} />
);
/** box. r = roughness, ry/rx/rz = rotation */
export const Bx: React.FC<{ p?: V3; s: V3; c: string; e?: string; ei?: number; r?: number; ry?: number; rx?: number; rz?: number; o?: number }> = ({ p = [0, 0, 0], s, c, e, ei, r, ry = 0, rx = 0, rz = 0, o }) => (
  <mesh position={p} rotation={[rx, ry, rz]}><boxGeometry args={s} /><M c={c} e={e} ei={ei} r={r} o={o} /></mesh>
);
/** cylinder (r2 = bottom radius for a taper) */
export const Cy: React.FC<{ p?: V3; r: number; r2?: number; h: number; c: string; e?: string; ei?: number; rx?: number; rz?: number; seg?: number }> = ({ p = [0, 0, 0], r, r2, h, c, e, ei, rx = 0, rz = 0, seg = 20 }) => (
  <mesh position={p} rotation={[rx, 0, rz]}><cylinderGeometry args={[r, r2 ?? r, h, seg]} /><M c={c} e={e} ei={ei} /></mesh>
);
/** sphere, sc = non-uniform scale (flatten to a splat with sc=[1,0.03,1]) */
export const Sp: React.FC<{ p?: V3; r: number; c: string; e?: string; ei?: number; sc?: V3 }> = ({ p = [0, 0, 0], r, c, e, ei, sc = [1, 1, 1] }) => (
  <mesh position={p} scale={sc}><sphereGeometry args={[r, 24, 16]} /><M c={c} e={e} ei={ei} /></mesh>
);
/** plane facing +z (rotate with ry/rx); map = a canvas texture from textTex/useTex */
export const Pl: React.FC<{ p?: V3; s: [number, number]; c: string; e?: string; ei?: number; ry?: number; rx?: number; map?: THREE.Texture; o?: number }> = ({ p = [0, 0, 0], s, c, e, ei, ry = 0, rx = 0, map, o = 1 }) => (
  <mesh position={p} rotation={[rx, ry, 0]}>
    <planeGeometry args={s} />
    <meshStandardMaterial color={c} map={map} roughness={0.9} emissive={e ?? "#000"} emissiveIntensity={ei ?? 0} emissiveMap={map && e ? map : undefined} transparent={o < 1} opacity={o} />
  </mesh>
);

const texCache = new Map<string, THREE.CanvasTexture>();
/** draw anything with Canvas 2D and use it as a texture (signs, posters, screens). key must be unique per drawing */
export function useTex(w: number, h: number, draw: (g: CanvasRenderingContext2D) => void, key: string): THREE.CanvasTexture {
  return React.useMemo(() => {
    const hit = texCache.get(key);
    if (hit) return hit;
    const cv = document.createElement("canvas");
    cv.width = w; cv.height = h;
    draw(cv.getContext("2d")!);
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    texCache.set(key, t);
    return t;
  }, [key]);
}
/** centred text on a flat colour, e.g. a room number plate */
export function textTex(text: string, w: number, h: number, bg: string, fg: string, size: number, key = text): THREE.CanvasTexture {
  const hit = texCache.get(key);
  if (hit) return hit;
  const cv = document.createElement("canvas");
  cv.width = w; cv.height = h;
  const g = cv.getContext("2d")!;
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  g.fillStyle = fg; g.font = `bold ${size}px sans-serif`; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(text, w / 2, h / 2);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  texCache.set(key, t);
  return t;
}
/** soft halo round a light source (lamp, sconce, EXIT sign): an additive sprite, so lights "bloom" without post-processing.
 *  s = size in metres, o = strength. Put one on every practical light the camera can see. */
export const Glow: React.FC<{ p: V3; s?: number; c?: string; o?: number }> = ({ p, s = 0.8, c = "#FFD9A0", o = 0.55 }) => {
  const tex = useTex(128, 128, (g) => {
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.22, "rgba(255,255,255,0.5)"); gr.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  }, "glow-halo");
  return (
    <sprite position={p} scale={[s, s, 1]}>
      <spriteMaterial map={tex} color={c} transparent opacity={o} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
    </sprite>
  );
};

/** deterministic pseudo-random 0..1 (never Math.random: every frame must render the same twice) */
export const rnd = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

/** camera: position, target, fov, plus a small handheld drift (0 = locked off, 0.3-0.6 for close-ups) */
export const Cam: React.FC<{ p: V3; t: V3; fov?: number; drift?: number }> = ({ p, t, fov = 35, drift = 1 }) => {
  const { camera } = useThree();
  const f = useCurrentFrame();
  const dx = Math.sin(f / 23) * 0.012 * drift, dy = Math.sin(f / 31 + 1) * 0.008 * drift;
  camera.position.set(p[0] + dx, p[1] + dy, p[2]);
  camera.lookAt(t[0] + dx * 0.5, t[1] + dy * 0.5, t[2]);
  const pc = camera as THREE.PerspectiveCamera;
  if (pc.fov !== fov) { pc.fov = fov; pc.updateProjectionMatrix(); }
  return null;
};

/** one 3D shot = one canvas, 1080x1920. NEVER put DOM (div, Click, Audio, cards) inside a Shot — put them next to it.
 *  tilt = tilt-shift soft bands top/bottom (on by default; tilt={false} for a fully sharp frame, or set band/px). */
export const Shot: React.FC<{ children: React.ReactNode; blur?: number; dim?: number; tilt?: boolean | { band?: number; px?: number } }> = ({ children, blur = 0, dim = 1, tilt = true }) => (
  <AbsoluteFill style={{ filter: blur ? `blur(${blur}px) brightness(${dim})` : dim !== 1 ? `brightness(${dim})` : undefined, transform: blur ? "scale(1.06)" : undefined }}>
    <ThreeCanvas width={1080} height={1920} camera={{ fov: 35, position: [0, 1.5, 5], near: 0.02, far: 300 }} gl={{ toneMapping: THREE.ACESFilmicToneMapping, antialias: true }}>
      {children}
    </ThreeCanvas>
    {tilt && !blur ? <TiltShift {...(typeof tilt === "object" ? tilt : {})} /> : null}
  </AbsoluteFill>
);
