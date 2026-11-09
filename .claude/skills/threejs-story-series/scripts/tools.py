#!/usr/bin/env python3
"""Small QA helpers (run from the episode folder).

  python tools.py mids                      middle frame of every cut in src/Film.tsx (feed to: node stills.mjs <frames>)
  python tools.py contact [cols]            tile out/st/*.png into out/contact.png
  python tools.py sheet out/raw.mp4 [every] contact sheet of a render, one frame every N s (default 2)
  python tools.py strip out/raw.mp4 t0 t1   6 fps strip of a moment (check motion: feet sliding, popping, occlusion)
  python tools.py onsets file.wav [0.45]    first hits inside an SFX file (so mix.json at = beat - hit)
  python tools.py gap take.mp3 t0 t1        quietest 0.15 s inside a window (where a line really starts)
"""
import array
import re
import subprocess
import sys
from pathlib import Path

from common import load, need, run


def mids() -> None:
    """middle frame of every { a: ..., b: ..., el: } cut. a/b may be numbers, consts, or T(n) / E(n) / mid(n) / END / DUR / FPS"""
    s = Path("src/Film.tsx").read_text(encoding="utf-8")
    lines = load("src/lines.json")
    L = lines["lines"]
    env = {"T": lambda n: L[n - 1]["t"], "E": lambda n: L[n - 1]["end"], "mid": lambda n: (L[n - 1]["t"] + L[n - 1]["end"]) / 2,
           "FPS": 30, "DUR": round((lines["total"] + 2.6) * 30)}
    env["END"] = L[-1]["end"] + 0.4
    for k, v in re.findall(r"const ([A-Z_]+) = ([\d.]+);", s):
        env[k] = float(v)
    out = []
    for a, b in re.findall(r"\{ a: ([^,;\n]+?), b: ([^,;\n]+?), el:", s):
        try:
            fa, fb = eval(a, {"__builtins__": {}}, env), eval(b, {"__builtins__": {}}, env)
            out.append(str(round((fa + fb) / 2 * 30)))
        except Exception as e:  # unknown expression: skip, say so
            print(f"# skip cut a={a} b={b}: {e}", file=sys.stderr)
    print(" ".join(out))


def contact(cols: int = 6) -> None:
    run([need("ffmpeg"), "-v", "error", "-y", "-pattern_type", "glob", "-i", "out/st/f*.png", "-vf", f"scale=270:-1,tile={cols}x4:padding=4", "-frames:v", "1", "out/contact.png"])
    print("out/contact.png")


def sheet(video: str, every: float = 2) -> None:
    run([need("ffmpeg"), "-v", "error", "-y", "-i", video, "-vf", f"fps=1/{every},scale=160:-1,tile=11x6:padding=3", "-frames:v", "1", "out/contact-render.png"])
    print("out/contact-render.png")


def strip(video: str, t0: float, t1: float) -> None:
    run([need("ffmpeg"), "-v", "error", "-y", "-ss", str(t0), "-t", str(t1 - t0), "-i", video, "-vf", "fps=6,scale=180:-1,tile=10x3", "-frames:v", "1", "out/strip.png"])
    print("out/strip.png")


def onsets(f: str, th: float = 0.45) -> None:
    raw = subprocess.run([need("ffmpeg"), "-v", "error", "-i", f, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    a = array.array("h", raw)
    w = 200
    env = [max(abs(x) for x in a[i:i + w]) for i in range(0, len(a) - w, w)]
    m = max(env) or 1
    on, prev = [], 0
    for i, e in enumerate(env):
        if e > th * m and prev <= th * m:
            on.append(round(i * w / 8000, 2))
        prev = e
    print(f, on[:10])


def gap(f: str, t0: float, t1: float) -> None:
    raw = subprocess.run([need("ffmpeg"), "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    a = array.array("h", raw)
    best = None
    t = t0
    while t < t1:
        seg = a[int(t * 16000):int((t + 0.15) * 16000)]
        if seg:
            rms = (sum(x * x for x in seg) / len(seg)) ** 0.5
            if best is None or rms < best[0]:
                best = (rms, t)
        t += 0.02
    print("quietest", round(best[1], 2), "-", round(best[1] + 0.15, 2)) if best else print("empty window")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    c, a = sys.argv[1], sys.argv[2:]
    if c == "mids": mids()
    elif c == "contact": contact(int(a[0]) if a else 6)
    elif c == "sheet": sheet(a[0], float(a[1]) if len(a) > 1 else 2)
    elif c == "strip": strip(a[0], float(a[1]), float(a[2]))
    elif c == "onsets": onsets(a[0], float(a[1]) if len(a) > 1 else 0.45)
    elif c == "gap": gap(a[0], float(a[1]), float(a[2]))
    else: sys.exit(__doc__)


if __name__ == "__main__":
    main()
