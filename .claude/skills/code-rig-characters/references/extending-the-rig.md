# Extending the rig

## Structure of `Char`
```
group (position p, rotation ry, scale height)
└─ hips at y hipHeight(build) + pose.y × build.leg
   ├─ Leg ×2      hip rotation → thigh capsule → knee group (rotation kn) → shin → foot   (lengths × build.leg, radii × build.limb)
   └─ spine group (rotation pose.spine)
      ├─ torso group scaled [girth, torso, girth]
      │    Torso  lathe body (TORSO_PTS / COAT_PTS / SCRUB_PTS) + outfit details + backpack
      │    blood  optional collar ring + front drip (pose.blood)   ← rig-attached effects live here
      ├─ back     anything passed as <Char back={…}> at (0, 0.4, -0.2)
      ├─ Arm ×2   shoulder rotation → upper arm → elbow group (el) → forearm → mitten hand → HoldProp
      └─ neck (length × build.neck) → head group (rotation pose.head) → Head scaled by headS
                 skin sphere, ears, Eye ×2 (blink/look), brows (browUp), nose, mouth (mouth), hair, extras
```
Units: with SLIM the body is ~1.9 units tall before `height` scaling. The head sphere radius is 0.16 before `headS`.
`headCenter(L)` / `headRadius(L)` return world metres for framing.

## Add an outfit
1. Add the name to `Outfit` in char.tsx.
2. In `Torso`, add `{L.outfit === "apron" ? <> … </> : null}` with boxes/capsules ON the lathe surface
   (front surface z ≈ 0.15 at chest height y 0.1–0.35).
3. Short sleeves? add it to the `short` test in `Arm`. A long coat? give it its own lathe profile like COAT_PTS.
4. Render `Turn-<id>`.

## Add hair
Copy `HairShort` / `HairPony` (cap + a few big shapes), `HairBob` (lathe shell + fringe) or `HairSpiky`
(cap + `Lock` cones pointing along a direction).
Keep it a few large shapes; many small ones flicker at phone size.

## Add a hand prop
Add a kind to `Look.holdR` and a branch in `HoldProp` (hand centre is at y −0.3 of the forearm group).

## Rules
- Primitives only; matte (`roughness` ≥ 0.6). No textures on characters except tiny printed details.
- No joint spheres at shoulders/knees.
- Everything that should move with a body part must be a CHILD of that part's group
  (blood on the shirt in the spine group, blood on the mouth in the head group, a pet in `back`).
- Deterministic only: no Math.random — use `rnd(n)` from kit/three or the seed.
