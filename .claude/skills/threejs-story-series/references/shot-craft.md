# Shot craft — staging, cameras, action, effects (lessons paid for in real episodes)

## Coordinates and continuity
- Feet at y=0, characters face +z, the character's left = +x. `ry = atan2(target.x - p.x, target.z - p.z)` faces a target.
- Write the set plan as a comment at the top of the set file. Keep every character's position per scene in ONE
  place (constants at the top of Film.tsx); shots only change the camera. Then continuity is automatic.
- Same character = same Look + same seed in every shot.

## Camera distances that work (default SLIM build, height 0.88: standing head ≈ 1.54 m, sitting ≈ 1.17 m)
The head is small (radius ≈ 0.14 m), so faces are read in head-and-shoulders shots, not giant close-ups.
| Shot | Distance from the face | fov |
|---|---|---|
| Head + shoulders | 1.9–2.2 m | 30–32 |
| Waist / two-shot | 2.6–3.2 m | 34–38 |
| Full figure in a corridor | 4–6 m, camera at chest height | 40–46 |
| Wide room | 5–7 m from a corner | 42–54 |
| Prop macro | 0.5–0.8 m | 28–32 |
| Peephole / spy-hole | against the door, looking down the corridor | 90–100 + a dark round mask |
`headCenter(L)` and `headRadius(L)` (rig/char.tsx) give the numbers for any build. Closer than ~6 head radii =
the camera enters the head/hair. Check the line between camera and subject: nothing (another character, a pillar,
a wall, the subject's own head in an over-the-shoulder) may cross it. Portrait frames are narrow (horizontal
half-angle ≈ fov/2 × 0.56): two subjects more than ~15° apart from the camera will not both fit.

## Lighting
- Every practical light the camera sees gets a `Glow` halo (kit/three) — that soft bloom is half of the look.
- Dark scenes: always a pointLight near every face (≈1–1.5 intensity, 3–4 m distance) or the face becomes a silhouette.
- Light leaking under a door / from a doorway = emissive thin box + a pointLight on the far side.
- Do not light a character so hard that the face clips to white (doorway lights: intensity ≤ 1.5, placed off-axis).

## Action
**Walk / run** — drive the cycle by DISTANCE, not by frame: `runPose(dist, ph0, amp)` (`RUN_STRIDE` 2.5 m per cycle),
`walkPose(dist / WALK_STRIDE * 2π)` (1.2 m). Scale both with `build.leg` if you change the legs. Then feet never skate. Give each person a different `ph0` so a group is not in lock-step.
Running look: forward lean (spine 0.3), elbows bent (−1.45), arms swing opposite the legs, knee lift, bounce.
**A group running** — stage in LANES so every face is visible (left / centre / right, 0.8–1 m apart in depth),
never in a single file that hides the people behind. Best two-shot pattern:
1. tracking shot in front of them, low (0.8 m), camera moving at their speed, all three faces in frame;
2. arrival shot from behind/side: they decelerate (amp → 0 with an ease-out), the leader opens the door
   (reach pose, door leaf swing with ease), light spills in, the leader goes through, the next follows, one looks back.
Never let a shot end with everyone frozen in place for more than ~0.5 s.
**Doors** — leaf hinged on one edge (`group` at the hinge, rotate y), handle, frame that sticks out of the wall,
a number plate in front of the wall (buried plates are invisible).
**Hiding** — CROUCH pose under a window/desk; the threat seen through glass, a gap, or as shadow first.
**Sound you can see** — Rings at the source, the word ("knock") popping on the measured hit frames.

## Gore (off by default — only if the series bible allows it)
- Anything on a body must be PART OF THE RIG (`pose.blood`, children of the body part's group); spheres floating in
  front of a body slide off when it moves.
- On floors: flattened spheres (`Sp sc=[w, 0.03, l]`) that join into one continuous trail, never rectangles. Dark
  colour, slight emissive in dark scenes. Less is scarier.

## Creatures and riders
- A creature = a real rig (e.g. `infected(Look)`) posed and lit, never a pile of primitives.
- Something that rides on a character (a pet, a tank, wings) = `Char back={...}`: it follows the spine.

## Cards over shots
Use a card only for: the rule (hook), a time/place, a measured number, the next-episode card.
A card on every beat explaining the plot reads as a lecture — viewers find it annoying. If a beat is confusing,
fix the PICTURE (show the cause and the effect in two shots) or the line, not with a panel.

## Motion QA
Stills catch framing; only a strip or playback catches motion: `tools.py strip out/raw.mp4 t0 t1` for every
action beat. Look for: feet sliding, limbs popping between frames, characters walking through furniture or each
other, a camera passing through a wall, a frozen tail of a shot.
