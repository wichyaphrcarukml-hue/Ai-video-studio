# Style guide — the base look, and how to make it yours

The template ships ONE neutral base look: a warm, miniature-diorama 3D world with slender, plain-faced figures,
cream paper cards and a quiet room-tone bed. It is a starting point, not a house style. Change the knobs at the
bottom until the series looks like yours (and not like anyone else's channel).

## The base look
| Element | Rule |
|---|---|
| Render | three.js through `@remotion/three`; `meshStandardMaterial`, roughness ~0.7–0.9, metalness 0; ACES tone mapping. Flat colours, no textures except tiny printed signs |
| Sets | Real 3D rooms and corridors with depth: leading lines (a carpet, a corridor) toward a vanishing point, a few large props, skirting boards, door frames that stick out of the wall |
| Characters | Default build `SLIM`: small round head, long neck, slender torso, long thin limbs, simple tee/jeans/sneakers. Face `dots`: two small dark eyes, thin brows, small mouth. Mostly calm poses + micro-motion (breath, blink, a head turn) |
| Light | Warm practical lights (lamp, sconce, EXIT sign) + a `Glow` halo on each one the camera sees; warm ambient/hemisphere fill; one cool source for contrast (a night window). A fill light near every face |
| Lens | `TiltShift` over every shot: the top and bottom bands go soft, the middle stays sharp. Grain 0.035, soft warm vignette |
| Camera | Every shot pushes in slowly (≈3–6 % over the shot) with a little handheld drift. Hard cut every 1.5–3 s; a VO sentence = 2–4 shots. The same shot may hold while only the caption/card changes |
| Frame | 1080×1920, 30 fps. Keep the subject in the upper 60 % — captions own y 1230–1450 |
| Captions | Rounded heavy Thai/Latin sans (Kanit 600 default), cream `#F2EBDD`, soft dark shadow, centred at y≈1230. Key words: red chip `#D9483B` (first time) / amber text `#E9B84A`. Full-sentence subtitle under it in a dark box. Never thick outlines, 3D/offset shadows or sticker letters |
| Cards | Cream `#ECE5D3` paper, rounded, a coloured bar on the left (red = rule, gold = proof), small bold heading, flat icons (✓ green / ✗ red), one big red number on proof cards + the source in small grey type. HUD = clock chip top-right + place chip top-left |
| End | The last shot blurs out (`BlurIn`), then the next-episode card fades in on top: episode number, a red rule, the cliffhanger as a red line, a quiet "follow" line |
| Sound | No music by default: a continuous room tone (`sound.py room`) that thickens toward the twist, soft paper pops on cards, real-feeling one-shots on story beats. −14 LUFS, peak ≤ −1 dBFS |

## Visual registers (rotate them; each has a job)
1. **3D wide** — where are we, who is here (establish geography before any action).
2. **3D medium / insert** — a reaction, a hand, a detail that will matter (plant the twist object here).
3. **POV / over-the-shoulder** — what "you" see; the threat; a peephole or a gap.
4. **Card over a blurred 3D plate** — the rule, a time, a number, a checklist. Only where it must be read.

## Make the series yours (change these, keep the mechanics)
| Knob | Where | Ideas |
|---|---|---|
| Figure | `build` + `headS` per Look in `src/rig/cast.ts` | stockier (girth 1, limb 0.9), longer legs, a big head (headS 1.3+ with build ≈ 1), a different face (`face: "big"`) |
| Palette | `src/kit/ui.tsx` (RED, AMB, PAPER, INK, CREAM, GOLD) + colours at the top of each `src/sets/*.tsx` | cold steel + one neon accent, pastel daylight, sepia |
| Light / lens | sets (lights, `Glow`), `<Shot tilt={...}>` in kit/three.tsx (TiltShift band/px, or `tilt={false}`), `Vig` / `Grain` in `Film.tsx` | no tilt-shift and hard shadows, heavy fog, day exteriors |
| Font | `episode.json` "font" (Kanit / NotoSansThai / NotoSans) or add any `@remotion/google-fonts` family in `kit/ui.tsx` | a condensed grotesk, a serif for folk tales |
| Captions | `src/ui/captions.tsx` (position, size, chip vs text colour, subtitle box via `episode.json` "subtitles") | caption top-left, word-by-word, no subtitle |
| Cards | `src/ui/cards.tsx` | your own shapes, icons, colour bars, map / blueprint cards |
| Language | `script.md` in any language + a matching voice + `transcribe.py --lang xx`. Captions split on spaces — for Thai/Chinese put a space between phrases |
| Cast / world | `src/rig/cast.ts` (code-rig-characters skill), new files in `src/sets/` — build once, shoot from many cameras |
| Sound | `sound.py room` (default) or `sound.py bgm --key A --mood warm` (music), your own SFX, pops in `public/sfx` |
| Pacing | cut length, `vo/pauses.json`, voice rate (`tts.py --rate -5%`) |
| Gore | off by default; `pose.blood` + floor splats exist if your series bible allows it |

Adapt, don't copy: keep a reference's MECHANISM (e.g. "the rule against instinct, the planted detail"), build
your own world, characters and details, and add at least one twist of your own per episode.
