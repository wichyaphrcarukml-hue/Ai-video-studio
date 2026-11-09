#!/usr/bin/env python3
"""Replace one or more lines in the take with re-voiced versions WITHOUT moving any timing (picture stays in sync).

  python revoice.py fix.mp3 '{"3": [0.0, 4.2], "15": [4.45, 7.3]}'

fix.mp3 = a new take containing only the corrected lines (same voice + settings), JSON maps
line_number (1-based, as in script.md) -> [start, end] seconds of that line inside fix.mp3.
Each new line is trimmed of leading silence, sped up at most to fit the old slot (never slowed), padded to the slot.
The old take is kept as vo/takeA_old.mp3. Then: python splice.py, python mix.py (with a fresh render or clicks.wav).
Keep the tail of each line: trimming the end silence cuts final consonants.
"""
import json
import shutil
import sys

from common import duration, load, need, run


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fix, reps = sys.argv[1], {int(k): v for k, v in json.loads(sys.argv[2]).items()}
    ff = need("ffmpeg")
    d = load("vo/lines.json")
    L, take = d["lines"], d["take"]
    shutil.copy(take, "vo/takeA_old.mp3")
    run([ff, "-v", "error", "-y", "-i", "vo/takeA_old.mp3", "-ar", "44100", "-ac", "1", "vo/_orig.wav"])
    inputs = ["-i", "vo/_orig.wav"]
    fc, ins, cur, n = [], [], 0.0, 0
    for num in sorted(reps):
        i = num - 1
        a, b = reps[num]
        t0 = L[i]["t"] - 0.05
        slot = (L[i + 1]["t"] - 0.1 - t0) if i + 1 < len(L) else (duration("vo/_orig.wav") - t0)
        src = f"vo/_new{num}.wav"
        run([ff, "-v", "error", "-y", "-i", fix, "-af", f"atrim={a}:{b},silenceremove=start_periods=1:start_threshold=-40dB", "-ar", "44100", "-ac", "1", src])
        tempo = max(1.0, duration(src) / (slot - 0.05))
        if tempo > 1.12:
            print(f"warning: line {num} needs {tempo:.2f}x speed to fit; consider a shorter wording")
        fc.append(f"[0]atrim={cur}:{t0},asetpts=PTS-STARTPTS[p{n}]"); ins.append(f"[p{n}]"); n += 1
        inputs += ["-i", src]
        j = len(inputs) // 2 - 1
        fc.append(f"[{j}]atempo={tempo},afade=t=in:d=0.02,apad=whole_dur={slot},atrim=0:{slot}[p{n}]"); ins.append(f"[p{n}]"); n += 1
        cur = t0 + slot
        print(f"line {num}: slot {slot:.2f}s tempo {tempo:.3f}")
    fc.append(f"[0]atrim={cur},asetpts=PTS-STARTPTS[p{n}]"); ins.append(f"[p{n}]"); n += 1
    fc.append("".join(ins) + f"concat=n={n}:v=0:a=1[o]")
    run([ff, "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[o]", "-b:a", "192k", take])
    print("new", take, round(duration(take), 3), "s  (old", round(duration("vo/takeA_old.mp3"), 3), "s) -> now run splice.py")


if __name__ == "__main__":
    main()
