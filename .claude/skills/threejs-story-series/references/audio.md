# Audio — voice, timing, fixes, sound, mix

## Voice
- One take per episode (same energy, same mic). Engines: `tts.py edge` (free, Microsoft neural voices),
  `tts.py elevenlabs --voice-id …` (your key in ELEVENLABS_API_KEY), or record yourself (`tts.py own`).
- Write for the ear: numbers as words, single numbers instead of ranges, names the voice reads correctly,
  loan words spelled for the sound you want (Thai: add ไม้ไต่คู้ ็ where a vowel must be short, e.g. "ล็อก" not "ลอก").
- Whisper writes digits and the standard spelling, so it cannot prove a pronunciation — LISTEN to the doubtful words.

## Timing
- `align.py` → `vo/lines.json` (positions inside the raw take) → `splice.py` adds pauses → `src/lines.json`.
- `overlaps: 0` is required. If a caption shows words that are not spoken yet, the split between two lines is
  in the wrong place (often a natural pause INSIDE a line was taken for the gap between lines). Find the real gap
  with `tools.py gap`, correct `t`/`end` in vo/lines.json, rerun splice.py, re-render (captions are in the picture).
- Pauses: +0.4–0.6 s after a punch line, +0.8–1.0 s before the twist line, up to 1.0 s after "silence" beats.

## Fixing one word later (no re-edit)
1. Generate only the corrected lines with the same voice/settings into fix.mp3.
2. Find each line's span inside fix.mp3 (silences) and run `revoice.py fix.mp3 '{"3":[0,4.2],"15":[4.45,7.3]}'`.
   It keeps every slot length; lines are trimmed at the start only (trimming the end eats final consonants).
3. `splice.py`, then remix. The picture does not move.

## Sound effects
- `sound.py sfx vo/sfx` makes knock1/knock3, thud, creak, riser, impact, heartbeat, wind (procedural, licence-free).
- Other sources: your own recordings, CC0 libraries (check each licence), or a paid SFX generator.
- Land a hit on a beat: `tools.py onsets file.wav` gives the first hits inside the file; set `at` = beat − hit.
  If the picture shows the sound (a "knock" word), set those frames from the measured spacing.
- Through a wall: lowpass 900–1400 Hz. Room tone / wind: `loop_to`.

## The bed under the voice (never leave dead silence between lines)
Default — no music: `sound.py room .` → `vo/room.wav`: continuous room tone (dark air + faint mains hum) that
thickens from the "turn" act (low drone), a soft impact on "hero", thinning under the end card.
Optional music: `sound.py bgm .` → `vo/bgm.wav` (pad per act, music-box fragments, heartbeat toward "hero", riser +
impact, bell on "end"; `--key`, `--mood warm`). Set mix.json "bgm.file" to the one you want.
Acts are line references in timeline.json, so the bed follows the voice.

## Card pops
`sound.py pops public/sfx` → `pop-soft.wav` (paper card landing, `Click kind="soft"`) and `pop-tick.wav`
(rows, numbers, the clock: `kind="tick"`). Replace them with your own short wavs to change the feel.

## Mix
`mix.py` ducks the bed under the voice (sidechain), normalises to −14 LUFS, limits peaks, prints I and Peak.
The card pops (Click) are in the RENDER's audio, so mix.json "video" must be the fresh `out/raw.mp4`.
Never remix from a finished MP4: its audio already contains the old voice and you will hear two voices.
Voice-only fix without re-rendering: `npx remotion render src/index.ts Film out/clicks.wav --codec=wav`, set
`"clicks": "out/clicks.wav"` and `"video"` to the previous file (video stream is copied, its audio ignored).
Check: re-transcribe the final MP4; every line must still be understood over the bed.
