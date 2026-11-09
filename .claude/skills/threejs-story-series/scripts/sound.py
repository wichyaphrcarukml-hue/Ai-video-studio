#!/usr/bin/env python3
"""Procedural sound for the series (numpy only, no samples, no licences to worry about). 48 kHz WAV.

  python sound.py pops  <episode>/public/sfx           pop-soft.wav (paper card landing, main) + pop-tick.wav (small items)
  python sound.py sfx   <episode>/vo/sfx               knock1/knock3, thud, door creak, riser, impact, heartbeat, wind
  python sound.py room  <episode>                      DEFAULT bed: room tone that thickens toward the end -> vo/room.wav
  python sound.py bgm   <episode>                      OPTIONAL music: quiet pad + music-box + heartbeat -> vo/bgm.wav

timeline.json:  {"acts": {"hook": "L1", "setting": "L3", "threat": "L5", "turn": "L7", "hero": "L8+1.6", "end": "END"}}
  values = seconds or line refs (L5, L5e, L5+0.4, END) resolved through src/lines.json; any act names work; "hero" (the twist hit) and "end" are special: a riser lands on hero, a low bell rings on end.
  --key D|E|F|G|A|C (root), --mood dark|warm  change the colour of the bed.
"""
import argparse, json, math, sys, wave
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("numpy missing: python -m pip install numpy")

SR = 48000
rng = np.random.default_rng(7)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, d=0.2, shape=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * shape / max(d, 1e-4))
    return e


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def lp_fast(x, cutoff):
    """vectorised low-pass via FFT brick-wall with soft knee (fine for long beds)"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def save(path, x, stereo=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.clip(x, -1, 1)
    if stereo and x.ndim == 1:
        x = np.stack([x, x], 1)
    data = (x * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2 if stereo else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print("wrote", path)


# ─── one-shots ───
def soft_pop():
    """paper card landing: a short airy flick into a low, round thump (lands at 0.03 s)"""
    t = t_(0.3)
    flick = lp_fast(noise(0.3), 3500) * env(len(t), 0.001, 0.03, 6) * 0.35
    thump = np.sin(2 * math.pi * (120 + 160 * np.exp(-t * 45)) * t) * env(len(t), 0.002, 0.09, 5)
    out = np.zeros(len(t))
    k = int(0.03 * SR)
    out[k:] += thump[: len(t) - k]
    out += flick
    return norm(out, 0.75)


def tick_pop():
    """light dry tick for list rows, numbers, a clock change"""
    t = t_(0.12)
    x = np.sin(2 * math.pi * 2100 * t) * env(len(t), 0.0005, 0.02, 7)
    x += lp_fast(noise(0.12), 5000) * env(len(t), 0.0003, 0.008, 8) * 0.4
    return norm(x, 0.55)


def whoosh_pop():
    """0.3 s air lead-in that lands on a soft round hit at 0.30 s (the Click pre-rolls 9 frames for this)"""
    n = noise(0.55)
    sweep = np.linspace(0, 1, int(0.3 * SR)) ** 2
    air = lp_fast(n[: len(sweep)], 2500) * sweep * 0.5
    hit_t = t_(0.25)
    hit = np.sin(2 * math.pi * (180 + 220 * np.exp(-hit_t * 30)) * hit_t) * env(len(hit_t), 0.002, 0.08, 5)
    out = np.zeros(int(0.55 * SR))
    out[: len(air)] += air
    k = int(0.3 * SR)
    out[k : k + len(hit)] += hit * 0.9
    return norm(out, 0.8)


def box_pop():
    """detuned music-box tick for small items"""
    t = t_(0.6)
    f0 = 1318.5
    x = sum(np.sin(2 * math.pi * f0 * m * t + p) * g for m, p, g in [(1, 0, 1), (2.01, 1, 0.35), (3.03, 2, 0.15)])
    return norm(x * env(len(t), 0.002, 0.25, 4), 0.6)


def knock(n=1, gap=0.55, room=0.35):
    """knuckles on a door: a short thump + woody body; room = tail length"""
    out = np.zeros(int((gap * n + 0.8) * SR))
    for i in range(n):
        t = t_(0.35)
        body = np.sin(2 * math.pi * (95 + 60 * np.exp(-t * 40)) * t) * env(len(t), 0.001, 0.09, 6)
        click = lp_fast(noise(0.35), 1800) * env(len(t), 0.0005, 0.015, 8) * 0.6
        tail = lp_fast(noise(0.35), 700) * env(len(t), 0.002, room, 3) * 0.15
        k = int(i * gap * SR)
        out[k : k + len(t)] += (body + click + tail) * (1 - 0.05 * i)
    return norm(out, 0.85)


def thud():
    t = t_(1.2)
    x = np.sin(2 * math.pi * (55 + 40 * np.exp(-t * 12)) * t) * env(len(t), 0.002, 0.5, 4)
    x += lp_fast(noise(1.2), 400) * env(len(t), 0.001, 0.2, 5) * 0.4
    return norm(x, 0.9)


def creak():
    t = t_(1.6)
    f = 340 + 120 * np.sin(2 * math.pi * 0.7 * t) + 40 * rng.standard_normal(len(t)).cumsum() / SR * 30
    ph = 2 * math.pi * np.cumsum(f) / SR
    saw = (ph / (2 * math.pi)) % 1 * 2 - 1
    x = lp_fast(saw, 1400) * np.minimum(1, t / 0.2) * np.minimum(1, (1.6 - t) / 0.3)
    return norm(x, 0.6)


def riser(dur=2.2):
    t = t_(dur)
    k = t / dur
    x = lp_fast(noise(dur), 3000) * k ** 2 * 0.6
    x += np.sin(2 * math.pi * (110 + 330 * k ** 2) * t) * k ** 3 * 0.4
    return norm(x, 0.7)


def impact():
    t = t_(2.5)
    x = np.sin(2 * math.pi * (48 + 60 * np.exp(-t * 8)) * t) * env(len(t), 0.002, 1.2, 3)
    x += lp_fast(noise(2.5), 900) * env(len(t), 0.001, 0.4, 4) * 0.5
    return norm(x, 0.95)


def heartbeat(bpm=70, dur=6.0):
    out = np.zeros(int(dur * SR))
    beat = 60 / bpm
    t = t_(0.25)
    lub = np.sin(2 * math.pi * 55 * t) * env(len(t), 0.003, 0.08, 6)
    for i in range(int(dur / beat)):
        for off, g in [(0, 1.0), (0.22, 0.7)]:
            k = int((i * beat + off) * SR)
            if k + len(lub) < len(out):
                out[k : k + len(lub)] += lub * g
    return norm(out, 0.8)


def wind(dur=12.0):
    x = lp_fast(noise(dur), 500)
    x *= 0.6 + 0.4 * np.sin(2 * math.pi * 0.11 * t_(dur))
    return norm(x, 0.5)


# ─── room tone (default bed: no music) ───
def room(tl):
    """continuous room tone: a dark air bed + faint mains hum; from the "turn" act it thickens (low drone, slower swell),
    a soft impact lands on "hero", and everything thins out under the end card. Never fully silent between lines."""
    total = float(tl.get("total") or max(tl["acts"].values()) + 3)
    act = dict(tl["acts"])
    n = int(total * SR)
    tt = np.arange(n) / SR
    air = lp_fast(rng.standard_normal(n), 380) * 0.6 + lp_fast(rng.standard_normal(n), 2600) * 0.05
    air *= 0.85 + 0.15 * np.sin(2 * math.pi * 0.07 * tt)
    hum = (np.sin(2 * math.pi * 50 * tt) + 0.4 * np.sin(2 * math.pi * 100 * tt)) * 0.02
    out = air + hum
    turn = act.get("turn", act.get("hero", total) - 6)
    k = np.clip((tt - turn) / 3.0, 0, 1)
    drone = sum(np.sin(2 * math.pi * f * tt + i) for i, f in enumerate((55, 55.4, 82.5))) * 0.06
    out += drone * k * (0.8 + 0.2 * np.sin(2 * math.pi * 0.25 * tt))
    out *= 1 + 0.6 * k
    if "hero" in act:
        im = impact() * 0.6
        s0 = int(act["hero"] * SR)
        out[s0 : s0 + len(im)] += im[: max(0, n - s0)]
    if "end" in act:
        out *= np.clip(1 - (tt - act["end"]) / 1.5, 0.25, 1)
    rms = np.sqrt(np.mean(out ** 2)) or 1
    out *= 0.06 / rms
    return np.clip(out, -0.95, 0.95)


# ─── BGM ───
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9}


def midi_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def bgm(tl, key="D", mood="dark"):
    total = float(tl.get("total") or max(tl["acts"].values()) + 3)
    acts = sorted(tl["acts"].items(), key=lambda kv: kv[1])
    root = 50 + NOTE.get(key, 2)  # D3
    minor = mood == "dark"
    prog = [[0, 3 if minor else 4, 7], [-4, 0, 3 if minor else 4], [-2, 2, 5], [-5, -1, 2], [0, 3 if minor else 4, 7, 10]]
    n = int(total * SR)
    out = np.zeros(n)
    t_all = np.arange(n) / SR
    for i, (name, start) in enumerate(acts):
        end = acts[i + 1][1] if i + 1 < len(acts) else total
        a, b = int(start * SR), int(end * SR)
        if b <= a:
            continue
        tt = t_all[a:b] - start
        chord = prog[i % len(prog)]
        pad = sum(np.sin(2 * math.pi * midi_hz(root + c) * (1 + d) * tt + c) for c in chord for d in (-0.003, 0.003))
        fade = np.minimum(1, tt / 1.2) * np.minimum(1, (end - start - tt) / 1.2 + 0.001)
        out[a:b] += lp_fast(pad, 900) * fade * 0.12
        # music-box fragment at the start of each act
        mb = box_pop()
        k = a + int(0.2 * SR)
        for j, step in enumerate([0, 7, 3 if minor else 4]):
            pitch = 2 ** ((step) / 12)
            idx = np.clip((np.arange(len(mb)) * pitch).astype(int), 0, len(mb) - 1)
            seg = mb[idx] * 0.25
            s0 = k + int(j * 0.32 * SR)
            if s0 + len(seg) < n:
                out[s0 : s0 + len(seg)] += seg
    # thin wind under everything
    w = wind(min(total, 30))
    reps = int(math.ceil(total / 30))
    out += np.tile(w, reps)[:n] * 0.08
    # heartbeat from the first threat-ish act to the hero hit, speeding up
    act = dict(acts)
    if "hero" in act:
        hb_start = act.get("threat", act["hero"] - 8)
        bpm0, bpm1, tcur = 62, 108, hb_start
        while tcur < act["hero"]:
            k = (tcur - hb_start) / max(1e-3, act["hero"] - hb_start)
            bpm = bpm0 + (bpm1 - bpm0) * k
            beat = heartbeat(bpm, 60 / bpm + 0.3)[: int(60 / bpm * SR)]
            s0 = int(tcur * SR)
            out[s0 : s0 + len(beat)] += beat[: max(0, min(len(beat), n - s0))] * 0.35
            tcur += 60 / bpm
        r = riser(2.2)
        s0 = int((act["hero"] - 2.2) * SR)
        if s0 > 0:
            out[s0 : s0 + len(r)] += r[: n - s0] * 0.5
        im = impact()
        s0 = int(act["hero"] * SR)
        out[s0 : s0 + len(im)] += im[: max(0, n - s0)] * 0.7
    if "end" in act:
        tt = t_(4)
        bell = sum(np.sin(2 * math.pi * midi_hz(root - 12) * m * tt) * g for m, g in [(1, 1), (2.76, 0.4), (5.4, 0.2)]) * env(len(tt), 0.002, 2.5, 2.5)
        s0 = int(act["end"] * SR)
        out[s0 : s0 + len(bell)] += bell[: max(0, n - s0)] * 0.3
    # quiet bed: about -18 LUFS-ish (RMS target); the mix ducks it under the voice anyway
    rms = np.sqrt(np.mean(out ** 2)) or 1
    out *= 0.08 / rms
    return np.clip(out, -0.95, 0.95)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["pops", "sfx", "room", "bgm"])
    ap.add_argument("dest")
    ap.add_argument("--key", default="D")
    ap.add_argument("--mood", default="dark", choices=["dark", "warm"])
    a = ap.parse_args()
    d = Path(a.dest)
    if a.what == "pops":
        save(d / "pop-soft.wav", soft_pop())
        save(d / "pop-tick.wav", tick_pop())
    elif a.what == "sfx":
        save(d / "knock1.wav", knock(1))
        save(d / "knock3.wav", knock(3, gap=0.55))
        save(d / "thud.wav", thud())
        save(d / "creak.wav", creak())
        save(d / "riser.wav", riser())
        save(d / "impact.wav", impact())
        save(d / "heartbeat.wav", heartbeat(80, 8))
        save(d / "wind.wav", wind(12))
    else:
        import os
        from common import load, resolve_time
        os.chdir(d)
        tl = load("timeline.json")
        tl["acts"] = {k: resolve_time(v) for k, v in tl["acts"].items()}
        tl["total"] = load("src/lines.json")["total"] + 2.6
        if a.what == "room":
            save(Path("vo") / "room.wav", room(tl))
        else:
            save(Path("vo") / "bgm.wav", bgm(tl, a.key, a.mood))


if __name__ == "__main__":
    main()
