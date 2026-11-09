---
name: code-rig-characters
description: >-
  Design and build 3D characters and pets entirely in code (three.js primitives inside Remotion) from a
  written character card — no image generation, no reference sheet needed. Covers the card format, mapping it to
  the rig's Look fields, body proportions (Build: legs, arms, torso, girth, limbs, neck + head size) so each series
  gets its own figure, new outfits/hair/props, poses (walk/run driven by distance, crouch, sit, knock, hush,
  shamble), things mounted on the body (a pet on the back), and the Turn QA sheet (4 views + face).
  Use when the user wants a new character, a costume change, a creature, a pet, or says a character looks wrong.
  Works inside a threejs-story-series episode folder.
---

# Code-rig characters

Characters are DATA (`Look`) + a shared rig (`src/rig/char.tsx`) + POSES (`src/rig/poses.ts`).
Every frame is a pure function of the frame number, so renders are deterministic.

## 1. Write the character card first (`references/character-card.md`)
Name, role, age band, silhouette idea in one line, palette (skin, hair, top, bottom, shoes, accent),
hair type, outfit, 2 "never change" details, one prop, personality → default face (browUp, eye size).

## 2. Map the card to a Look in `src/rig/cast.ts`
Start from the closest preset (YOU, FRIEND, ADULT, CHILD, COAT, SCRUBS) and override fields.
Default figure = `SLIM` build + `headS` 0.95 + `face: "dots"`, `height` 0.86–0.94 for adults, ~0.68 for a child.
Proportions are the series' signature: decide them ONCE for the whole cast with the user (e.g. stockier:
`build: { ...SLIM, girth: 1, limb: 0.9 }`; long-legged: `leg: 1.5`; big-head cartoon: all build values ≈ 1 with
`headS` 1.3+ and `face: "big"`). Cartoon eyes (`face: "big"`): `irisK` 0.86 friendly, `eyeH` 0.5 menacing.
Add the id to `CAST` so `Turn-<id>` exists.

## 3. Check it (required before shooting)
`npx remotion still src/index.ts Turn-<id> out/turn-<id>.png --gl=angle` → 4 views + face.
Pass: the proportions you chose, the card's colours, both never-change details visible from the front, a readable
silhouette when the image is shrunk to 200 px, eyes not tiny, nothing poking through the hair.
Fixes: head too small → `headS`; bob too long → `hairLen`; hair shiny → `hairR: 0.8`; puffy shoulders →
short sleeves; accessory on the wrong side → the character's left is +x (screen right in a front view).

## 4. Need something the rig does not have?
Read `references/extending-the-rig.md`: add a value to the `Outfit`/hair union and one block in
Torso/Arm/Leg/Head using only capsule, sphere, box, lathe, cone, torus. Never joint balls. Eyes must sit
outside the head sphere (z ≥ 0.141 in head units).

## 5. Animate
`references/poses.md`: the pose fields, the pose library, how to drive walk/run by distance, how to blend,
how to mount things on the back, and the effects that live inside the rig (bruise, bite, optional blood).
Arm poses that touch the face (HUSH, LISTEN, hand on neck) are tuned for SLIM: re-check them after changing
`build.arm` or `headS`.

## Pets
`src/rig/pets.tsx`: `Cat` (colours via `colors`), `Dog` (`headOnly` for a head peeking out of something you mount with `Char back={…}`).
`Turn-pets` shows them. New animal = copy the Cat: capsule body, big sphere head, four short legs, tail segments,
ears as cones; reactions via `puff` (fur + ears back) and head/look.
