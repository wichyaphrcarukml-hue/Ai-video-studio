# Poses and motion

## Pose fields (all optional; radians unless noted)
`spine [x,y,z]` lean/twist · `head [x,y,z]` nod/turn/tilt · `shL/shR [x,y,z]` shoulders (x negative = arm forward/up)
`elL/elR` elbow bend (negative bends) · `hipL/hipR [x,y,z]` (x negative = thigh forward) · `knL/knR` knee bend (positive)
`y` body drop in leg units (crouch −0.42, sit −0.3) · `blink` 0..1 · `mouth` 0..1 · `browUp` −1..1 · `look [x,y]` eyes
specials: `handNeckL` 0..1, `handNeckR`, `bite` 0..1, `cloth` 0..1, `blood` 0..1, `bruise` 0..1, `holdOff`

## Library (`src/rig/poses.ts`)
`walkPose(ph, amp)` · `runPose(dist, ph0, amp)` · `CROUCH` · `SIT` · `knockPose(k)` · `reachPose(k)` · `LISTEN` ·
`HUSH` · `shamblePose(ph)` · `blendPose(a, b, k)`. Combine with spread: `{ ...SIT, ...LISTEN, blink }`.

## Locomotion without foot sliding
Move the character by distance d (metres) and derive the phase from the SAME d:
```ts
const d = io(f, 0, 60, 0, 3.0);                 // eased 3 m in 2 s (decelerates at the end)
const amp = Math.max(0, 1 - io(f, 0, 60, 0, 1) ** 2);
<Char p={[x, 0, z0 - d]} ry={Math.PI} pose={runPose(d, 2.2, amp)} />
```
Walk: `walkPose(d / WALK_STRIDE * 2 * Math.PI, amp)`. Never `walkPose(f * k)` while moving at an unrelated speed.
Strides (`WALK_STRIDE` 1.2, `RUN_STRIDE` 2.5) are for SLIM legs: multiply by `build.leg / 1.38` for other legs.

## Groups
Different `ph0` per person (0, 2.2, 4.1), different start offsets, lanes 0.4–0.6 m apart sideways and
~1 m apart in depth; the leader acts first (opens the door), the others react a few frames later.

## Faces
Blinks are automatic (seeded); force `blink: 0` for a stare. Fear: `browUp 1, mouth 0.2–0.35`.
Anger/focus: `browUp -0.4`. Creature chew: `mouth 0.4 + 0.4·|sin(f/3)|`.
