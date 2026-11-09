#!/usr/bin/env python3
"""Word timestamps for a take (faster-whisper, runs on CPU on any OS) -> vo/words.json

  python transcribe.py vo/takeA.mp3 [--lang th] [--model small]

Prints the recognised text: read it against script.md. Whisper often writes digits, drops tone marks or
mishears close sounds; that is fine (align.py is tolerant). Re-voice only if a word is really wrong when you LISTEN.
Models: tiny < base < small (default, good for Thai) < medium < large-v3 (slow on CPU). Downloaded once.
"""
import argparse
import sys

from common import dump


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--lang", default="th")
    ap.add_argument("--model", default="small")
    ap.add_argument("--out", default="vo/words.json")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper missing: python -m pip install faster-whisper")
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(a.audio, language=a.lang, word_timestamps=True, vad_filter=False)
    words, text = [], []
    for s in segs:
        text.append(s.text.strip())
        for w in s.words or []:
            words.append({"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3)})
    dump(a.out, {"audio": a.audio, "words": words})
    print("\n".join(text))
    print(f"\n{len(words)} words -> {a.out}")


if __name__ == "__main__":
    main()
