# Character Lock: Chrome Pole, Black Marble Studio

A prompt for an image-to-video / reference-locked video model (Kling, Veo, Runway, Hailuo, etc.).
Attach the locked character reference image. This repo's three.js pipeline renders stylised code-built
characters only, so it can't make this shot photorealistic.

## Main prompt (paste as one block)

[Character Lock: keep the reference character's face, hair, skin tone, body shape and outfit identical in every frame]
An adult woman in a dark black marble dance studio. A single vertical chrome pole runs from floor to ceiling at
center frame. She stands beside the pole, right hand gripping it at head height. She does a slow, smooth body wave
that rolls from chest to hips, then steps around the pole and does one graceful front hook spin, her outside leg
hooked on the pole, and comes out of the spin balanced and controlled.
Lighting: warm golden rim light from behind, soft atmospheric haze, dark falloff on the marble, subtle film grain.
Camera: slow push-in during the body wave, then a static low-angle shot for the spin.
Vertical 9:16, photorealistic, elegant and confident, natural body physics, realistic weight and momentum,
hand stays in contact with the pole through the spin.

## Shot timing (for a 5-8 s clip)

| Time | Action | Camera |
|------|--------|--------|
| 0.0-3.0 s | Standing beside the pole, right hand at head height, slow body wave chest to hips | Slow push-in, eye level to chest level |
| 3.0-4.0 s | Steps around the pole and sets up the spin | Cut or settle to a static low angle |
| 4.0-7.0 s | One front hook spin, outside leg hooked, lands softly | Static low angle, pole centered |

## Negative prompt

extra limbs, extra fingers, hand passing through pole, pole bending, floating feet, warped face, face change,
outfit change, jittery motion, sliding feet, blurry, low resolution, text, watermark, overexposed rim light

## Settings that usually help

- Reference / character strength: high. Motion strength: medium (high values break the hand grip on the pole).
- If the model handles one move per clip better, generate two clips (body wave, then spin) from the same
  reference image and join them on the step-around.
- Outfit: name it in the reference or the prompt (e.g. "black athletic dance shorts and crop top") so it
  doesn't change mid-spin.
