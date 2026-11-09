#!/usr/bin/env python3
"""Final mix -> the episode MP4 (video copied, audio rebuilt). Reads mix.json in the episode folder.

  python mix.py

mix.json:
  {"video": "out/raw.mp4", "voice": "vo/vo_aligned.wav", "out": "out/ep01-v1.mp4",
   "bgm": {"file": "vo/room.wav", "volume": 0.5}, "clicks_volume": 0.9,
   "sfx": [{"file": "vo/sfx/knock3.wav", "at": "L5", "volume": 0.9, "lowpass": 1600, "loop_to": null}]}

  at       = when the SOUND FILE starts: seconds or a line ref ("L5", "L5+0.4", "L5e" = end of line 5, "END").
             To land a hit on a beat: at = beat - first_hit (python tools.py onsets <file>)
  lowpass  = 900-1400 for things heard through a wall
  loop_to  = loop the file until this second (room tones, wind)
Voice ducks the bed (sidechain), then loudness -> -14 LUFS, peak <= -1.5 dBFS. Prints the measured I and Peak.

The card pops (Click) live in the VIDEO's own audio track, so "video" MUST be the fresh Remotion render (out/raw.mp4).
Never feed a finished mix back in as "video": the old voice would play twice. Voice-only fix? Render the clicks alone:
  npx remotion render src/index.ts Film out/clicks.wav --codec=wav    and set "clicks": "out/clicks.wav"
"""
import re
import subprocess
from pathlib import Path

from common import duration, load, need, resolve_time, run


def main() -> None:
    cfg = load("mix.json")
    ff = need("ffmpeg")
    total = duration(cfg["video"])
    inputs = ["-i", cfg["video"], "-i", cfg["voice"]]
    fc = ["[1]aformat=channel_layouts=stereo,aresample=48000,asplit=2[vo][sc]"]
    bed = []
    n = 2
    clicks_src = cfg.get("clicks")
    if clicks_src:
        inputs += ["-i", clicks_src]
        fc.append(f"[{n}:a]aresample=48000,volume={cfg.get('clicks_volume', 0.9)}[clk]")
        n += 1
    else:
        fc.append(f"[0:a]aresample=48000,volume={cfg.get('clicks_volume', 0.9)}[clk]")
    if cfg.get("bgm") and Path(cfg["bgm"]["file"]).exists():
        inputs += ["-i", cfg["bgm"]["file"]]
        fc.append(f"[{n}]aformat=channel_layouts=stereo,aresample=48000,volume={cfg['bgm'].get('volume', 0.3)}[bg]")
        bed.append("[bg]")
        n += 1
    for k, s in enumerate(cfg.get("sfx", [])):
        if not Path(s["file"]).exists():
            print("skip missing", s["file"])
            continue
        inputs += ["-i", s["file"]]
        chain = f"[{n}]aformat=channel_layouts=stereo,aresample=48000"
        at = resolve_time(s["at"])
        if s.get("loop_to"):
            span = resolve_time(s["loop_to"]) - at
            chain += f",aloop=loop=-1:size=2e9,atrim=0:{span},afade=t=out:st={max(0, span - 1)}:d=1"
        if s.get("lowpass"):
            chain += f",lowpass=f={s['lowpass']}"
        ms = int(at * 1000)
        chain += f",adelay={ms}|{ms},volume={s.get('volume', 0.8)}[x{k}]"
        fc.append(chain)
        bed.append(f"[x{k}]")
        n += 1
    if bed:
        fc.append("".join(bed) + f"amix=inputs={len(bed)}:normalize=0[bed]")
        fc.append("[bed][sc]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=300[duck]")
        fc.append("[vo][duck][clk]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.84:level=disabled[a]")
    else:
        fc.append("[vo][clk]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.84:level=disabled[a]")
    out = cfg["out"]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    run([ff, "-v", "error", "-y", *inputs, "-filter_complex", ";\n".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", out])
    err = subprocess.run([ff, "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    print(f"{out}  I={i[-1] if i else '?'} LUFS  Peak={p[-1] if p else '?'} dBFS  (target -14 ±1, peak <= -1)")


if __name__ == "__main__":
    main()
