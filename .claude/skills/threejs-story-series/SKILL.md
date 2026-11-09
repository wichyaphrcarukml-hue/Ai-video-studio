---
name: threejs-story-series
description: >-
  Produce a vertical (9:16) short-form STORY SERIES with real 3D characters animated in code
  (three.js inside Remotion): second-person survival-rule stories ("If X happens, don't Y"), one narrator
  voice, phrase captions + subtitles, a twist and a cliffhanger end card, episode after episode with the
  same cast and world. No image or video generation: every character, set and prop is built from primitives
  and every frame is rendered from code. Use when the user wants an animated story reel / mini-series /
  "make episode N", wants to fix an episode (captions out of sync, wrong pronunciation, a weak shot),
  wants to run the demo episode, or wants to start their own series in this format. Pairs with story-rule-script (writing)
  and code-rig-characters (designing the cast).
---

# three.js story series

You are the director, animator and editor. Deliver per episode: the finished MP4, a cover PNG, the
editable episode folder, and a short report (what was made, known gaps). Never post anywhere yourself.

## Requirements (check first: `python install.py --doctor` from the pack, or check by hand)
Node 18+, ffmpeg + ffprobe, Python 3.9+ with `numpy`, `faster-whisper`, `edge-tts` (optional: an ElevenLabs key).
Internet for the first `npm install`, the Google font, the whisper model download and edge-tts.
Windows: run scripts with `python` (or `py`); macOS/Linux: `python3`. Quote paths that contain spaces.
Remotion is free for individuals and companies up to 3 people; bigger companies need a Remotion company licence.

`scripts/…` below = this skill's scripts folder (use its full path). Everything else is relative to the EPISODE folder;
run every script from inside the episode folder.

## The format (the base look; the user is expected to make it their own)
- 9:16, 1080×1920, 30 fps, 65–72 s. Warm miniature-diorama 3D: matte flat colours, warm practical lights with
  `Glow` halos, `TiltShift` soft bands top and bottom, light grain + vignette, a slow push-in on every shot.
- Cast built in `src/rig` (default `SLIM` build: small head, long limbs, dot eyes) — never stills or AI video.
- One narrator, one take per episode, second person ("you…"). Hook = a rule. Twist line near the end
  ("You got everything right, except one thing.") + a physical detail planted earlier. End card = NEXT episode
  number + its hook, over the blurred last shot.
- Captions: one phrase (≤ 7 words) at a time, cream text centre-low (y≈1230), keywords as red chip / amber text,
  full-sentence subtitle under it. Keep faces/props above ~1150 px or below ~1500 px.
- Cards: cream paper, coloured left bar, one big red number + source on proof cards, HUD clock top-right.
- Hard cut every 1.5–3 s; the camera is never dead still.
- No music by default: continuous room tone, soft paper pops on cards, one-shots on story beats.
- −14 LUFS (±1), peak ≤ −1 dBFS. No emoji, no puffy/3D-outlined text. Gore off unless the bible allows it.
When the user starts THEIR series, ask what they want to change (figure, palette, font, light, sound) and change it
in code before episode 1 — `references/style-guide.md` lists every knob.

## Demo (when the user says "install / show me an example")
From the pack folder: `python install.py --yes --demo ./story-demo` (Codex: add `--target codex`). It installs what
is missing, copies the skills, creates `story-demo/ep01`, and runs voice → timing → sound → render → mix → cover.
Result: `story-demo/ep01/out/ep01-v1.mp4` + `out/cover.png`. Show both to the user, then offer to start their series.

## Workflow

### 0. Series setup (first episode only)
1. Write or load the series bible (skill **story-rule-script**: world, cast, the season's mystery, rules that never change).
2. Design the cast as character cards → `src/rig/cast.ts` (skill **code-rig-characters**), check each with `Turn-<id>`.
3. Build the world once in `src/sets/` (one set file per location, coordinates in a comment on top).
4. `python scripts/new_episode.py <series>/ep01` then `cd <series>/ep01 && npm install`
   (later episodes: `--from <series>/ep01 --ep 2 --link-modules <series>/ep01` shares node_modules).
5. `python scripts/sound.py pops public/sfx` (already present in the template) and `python scripts/sound.py sfx vo/sfx`.
6. Make it the user's own look now (style-guide knobs), render `Turn-<id>` + a few stills, get a yes, then shoot.

### 1. Script → `script.md`
Table rows `| n | VO phrase phrase phrase | subtitle |`, one sentence per row, phrases separated by spaces,
≤ 7 words per phrase. Numbers as words in the VO, digits on screen; no number ranges. Spell for the ear.
Follow **story-rule-script** (hook formula, fact → action, sidekick, twist, cliffhanger). Fiction says so.

### 2. Voice → timing (the picture uses ONLY `src/lines.json`)
```
python scripts/tts.py edge --voice th-TH-NiwatNeural        # or: elevenlabs --voice-id … | own (record)
python scripts/transcribe.py vo/takeA.mp3 --lang th          # read the text against the script; LISTEN to doubtful words
python scripts/align.py vo/takeA.mp3                         # must say overlaps: 0
# edit vo/pauses.json  {"line": extra_seconds}  (+0.4–0.6 after punch lines, +0.8–1.0 before the twist)
python scripts/splice.py                                     # -> vo/vo_aligned.wav + src/lines.json
```
A caption that appears before its words = a wrong split: fix that line's `t`/`end` in `vo/lines.json`
(find the real gap with `python scripts/tools.py gap vo/takeA.mp3 t0 t1`), rerun splice.py.
Wrong pronunciation later? `scripts/revoice.py` swaps single lines without moving any timing. See `references/audio.md`.

### 3. Episode config → `src/episode.json`
ep number, title, rule, ruleLabel, next {ep: N+1, line: the cliffhanger}, red/amb keywords, coverFrame, font.

### 4. Shots + edit → `src/Film.tsx`
- A shot = a small component: the set + characters (positions fixed for the whole episode) + `<Cam p t fov drift>`.
- `CUTS` = the edit table, cut by line number (`T(n)`, `E(n)`, `mid(n)`), so a new take re-times the picture.
- 1–2 shots per line, alternate wide / close / insert / POV; cards only where a number or rule must be seen.
- DOM (cards, Click, captions) goes NEXT TO `<Shot>`, never inside it.
- Read `references/shot-craft.md` before staging action (runs, crowds, doors, hiding, reveals, gore).

### 5. Visual QA (required before a full render)
```
npx tsc --noEmit -p .
node stills.mjs $(python scripts/tools.py mids)    # Windows PowerShell: node stills.mjs (python scripts/tools.py mids).Split()
python scripts/tools.py contact
```
Open `out/contact.png`; check every frame against `references/qa-checklist.md`. Fix, re-render only those frames.
For any motion (walk, run, door, fall) also check a strip after the render: `python scripts/tools.py strip out/raw.mp4 t0 t1`.

### 6. Render, sound, mix
```
npx remotion render src/index.ts Film out/raw.mp4 --crf=20 --concurrency=2 --gl=angle
python scripts/sound.py room .           # room-tone bed (default). Music instead: sound.py bgm . + mix.json bgm.file
                                         # acts in timeline.json are line refs (L5, L8+1.6, END)
python scripts/mix.py                    # mix.json: sfx at line refs; prints LUFS/peak
python scripts/tools.py sheet out/ep01-v1.mp4 1
```
Render one job at a time. `mix.json` "video" must be the fresh render (its audio = the card pops).

### 7. Cover + delivery
`npx remotion still src/index.ts Cover out/cover.png --frame=<coverFrame>` — title and episode number ON TOP,
a frame with a readable emotional face and no caption. Deliver: MP4, cover, episode folder, a caption draft,
known gaps. Re-transcribe the final MP4 once to be sure every line is still intelligible over the music.

### 8. Next episode
`python scripts/new_episode.py <series>/ep02 --from <series>/ep01 --ep 2 --link-modules <series>/ep01`,
then update episode.json (title, rule, keywords, next, coverFrame), timeline.json, mix.json, script.md.
Continuity rules: `references/series-continuity.md`.

## When the user asks for fixes
Fix the cause in code (never paint over a frame), re-render, remix, deliver as v2/v3 next to v1.
Common requests and where they are handled: captions out of sync → align/splice; pronunciation → revoice.py;
a stiff or cropped action shot → shot-craft "Action"; a face too small / camera in a head → shot-craft camera
table; too many explanation cards → remove them and make the picture tell it (cards are the last resort).

## Files
- `template/` — the episode project (Remotion + three.js), with a ~30 s demo episode that renders as-is.
- `scripts/` — tts, transcribe, align, splice, revoice, sound (pops/sfx/room/bgm synth), mix, tools, new_episode.
- `references/` — style-guide, shot-craft, audio, series-continuity, qa-checklist.
