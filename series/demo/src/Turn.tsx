import React from "react";
import { AbsoluteFill } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Char, headCenter, headRadius, type V3 } from "./rig/char";
import { CAST } from "./rig/cast";
import { Cat, Dog } from "./rig/pets";
import { SANS } from "./kit/ui";

/** Character QA sheet, rendered from the rig itself (no reference image needed).
 *  Top: front / three-quarter / side / back. Bottom: face close-up. Check it against your character card before shooting:
 *  proportions (as designed in the card), colours, the 2 "never change" details, readable silhouette at thumbnail size. */
const LookAt: React.FC<{ p: V3; t: V3 }> = ({ p, t }) => { const { camera } = useThree(); camera.position.set(...p); camera.lookAt(...t); return null; };
const Studio: React.FC = () => (
  <>
    <color attach="background" args={["#4A4C52"]} />
    <ambientLight intensity={0.9} />
    <directionalLight position={[2, 4, 5]} intensity={1.6} />
    <directionalLight position={[-3, 2, -2]} intensity={0.5} color="#B8C4E0" />
  </>
);
export const Turn: React.FC<{ who: string }> = ({ who }) => {
  const L = CAST[who];
  return (
    <AbsoluteFill style={{ background: "#222" }}>
      <div style={{ position: "absolute", top: 0 }}>
        <ThreeCanvas width={1080} height={900} camera={{ fov: 22, position: [0, 0.85, 8.6] }} gl={{ toneMapping: THREE.ACESFilmicToneMapping }}>
          <LookAt p={[0, 0.85, 8.6]} t={[0, 0.8, 0]} />
          <Studio />
          {[0, 0.2, 0.5, 1].map((r, i) => <Char key={i} L={L} p={[-1.62 + i * 1.08, 0, 0]} ry={-r * Math.PI} seed={i} />)}
        </ThreeCanvas>
      </div>
      <div style={{ position: "absolute", top: 900 }}>
        <ThreeCanvas width={1080} height={1020} camera={{ fov: 24, position: [0, 1.42, 1.5] }} gl={{ toneMapping: THREE.ACESFilmicToneMapping }}>
          <LookAt p={[0, headCenter(L) + 0.02, headRadius(L) * 9]} t={[0, headCenter(L) - 0.01, 0]} />
          <Studio />
          <Char L={L} pose={{ blink: 0, mouth: 0 }} />
        </ThreeCanvas>
      </div>
      <div style={{ position: "absolute", left: 40, top: 30, fontFamily: SANS, fontSize: 44, fontWeight: 700, color: "#EEE" }}>{who}</div>
    </AbsoluteFill>
  );
};
/** pets turnaround */
export const TurnPets: React.FC = () => (
  <AbsoluteFill style={{ background: "#222" }}>
    <ThreeCanvas width={1080} height={1920} camera={{ fov: 30, position: [0, 0.4, 5.6] }} gl={{ toneMapping: THREE.ACESFilmicToneMapping }}>
      <LookAt p={[0, 0.3, 5.6]} t={[0, 0.15, 0]} />
      <Studio />
      {[0, 0.2, 0.5, 1].map((r, i) => <Cat key={`c${i}`} p={[-0.66 + i * 0.44, 0.45, 0]} ry={-r * Math.PI} />)}
      {[0, 0.2, 0.5, 1].map((r, i) => <Dog key={`d${i}`} p={[-0.66 + i * 0.44, -0.25, 0]} ry={-r * Math.PI} s={0.9} />)}
    </ThreeCanvas>
  </AbsoluteFill>
);
