#!/usr/bin/env python3
"""Add dramatic pauses after chosen lines -> vo/vo_aligned.wav + src/lines.json (the ONLY timing the picture uses)

  python splice.py              pauses from vo/pauses.json: {"line_number": extra_seconds_after_it, ...}

Typical: +0.4-0.6 after a punch line, +0.8-1.0 before the twist line ("everything right, except one thing"),
+0.9 after "it went quiet". Cuts happen 0.08 s before each line start so no syllable is clipped.
"""
from pathlib import Path

from common import duration, dump, load, need, run


def main() -> None:
    d = load("vo/lines.json")
    L = d["lines"]
    pause = {int(k): float(v) for k, v in (load("vo/pauses.json").items() if Path("vo/pauses.json").exists() else [])}
    parts, shift, out = [], 0.0, []
    for i, l in enumerate(L):
        a = 0.0 if i == 0 else L[i]["t"] - 0.08
        b = (L[i + 1]["t"] - 0.08) if i + 1 < len(L) else None
        out.append({**l, "t": round(l["t"] + shift, 2), "end": round(l["end"] + shift, 2)})
        parts.append((a, b, pause.get(i + 1, 0.0)))
        shift += pause.get(i + 1, 0.0)
    fc, ins = [], []
    for k, (a, b, p) in enumerate(parts):
        fc.append(f"[0]atrim={a}" + (f":{b}" if b else "") + f",asetpts=PTS-STARTPTS,apad=pad_dur={p}[s{k}]")
        ins.append(f"[s{k}]")
    fc.append("".join(ins) + f"concat=n={len(parts)}:v=0:a=1,aresample=48000[o]")
    run([need("ffmpeg"), "-v", "error", "-y", "-i", d["take"], "-filter_complex", ";".join(fc), "-map", "[o]", "-ac", "1", "vo/vo_aligned.wav"])
    total = duration("vo/vo_aligned.wav")
    dump("src/lines.json", {"total": round(total, 2), "lines": out})
    print("vo_aligned", round(total, 2), "s")
    for i, l in enumerate(out, 1):
        print(i, l["t"], l["end"], l["th"])


if __name__ == "__main__":
    main()
