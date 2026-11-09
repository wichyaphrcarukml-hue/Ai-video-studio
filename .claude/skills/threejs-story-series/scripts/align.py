#!/usr/bin/env python3
"""Find where each script line starts/ends inside the take -> vo/lines.json

  python align.py vo/takeA.mp3            (needs script.md + vo/words.json from transcribe.py)

1) every recognised character gets a time (spread across its word)
2) difflib matches script characters to recognised characters (digits/typos just stay unmatched)
3) each line's first/last matched character gives start/end, snapped to the nearest silence edge
It must print `overlaps: 0`; check each start against the transcript (±0.3 s).
If a line starts mid-sentence on screen later, the split is wrong: fix t/end of that line in vo/lines.json by hand
(find real gaps with: python tools.py gap vo/takeA.mp3 <t0> <t1>) and re-run splice.py.
"""
import re
import subprocess
import sys
from difflib import SequenceMatcher

from common import dump, load, need, read_script


def keep(s: str) -> str:
    return re.sub(r"[^฀-๿a-zA-Z]", "", s).replace("ๆ", "").lower()


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    take = sys.argv[1]
    lines = read_script()
    wc, wt = [], []
    for w in load("vo/words.json")["words"]:
        c = keep(w["w"])
        for i, ch in enumerate(c):
            wc.append(ch)
            wt.append(w["s"] + (w["e"] - w["s"]) * (i + 0.5) / len(c))
    sc, owner = [], []
    for i, l in enumerate(lines):
        c = keep(l["th"])
        sc += list(c)
        owner += [i] * len(c)
    m = {}
    for blk in SequenceMatcher(None, "".join(sc), "".join(wc), autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            m[blk.a + k] = blk.b + k
    err = subprocess.run([need("ffmpeg"), "-i", take, "-af", "silencedetect=n=-38dB:d=0.1", "-f", "null", "-"], capture_output=True, text=True).stderr
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)] or [0.0]
    se = [0.0] + [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    for i, l in enumerate(lines):
        idx = [k for k, o in enumerate(owner) if o == i and k in m]
        if not idx:
            sys.exit(f"line {i + 1} not found in the transcript - check the take")
        a, b = wt[m[idx[0]]], wt[m[idx[-1]]]
        l["t"] = round(min(se, key=lambda x: abs(x - a) + (0.5 if x > a + 0.15 else 0)), 2)
        l["end"] = round(min(ss, key=lambda x: abs(x - b) + (0.5 if x < b - 0.15 else 0)), 2)
    dump("vo/lines.json", {"take": take, "lines": lines})
    bad = 0
    for i, l in enumerate(lines, 1):
        flag = "  <-- overlaps previous" if i > 1 and l["t"] < lines[i - 2]["end"] else ""
        bad += bool(flag)
        print(f"{i:2d} {l['t']:6.2f} {l['end']:6.2f} {l['th']}{flag}")
    print("overlaps:", bad)


if __name__ == "__main__":
    main()
