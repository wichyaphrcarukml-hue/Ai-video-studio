#!/usr/bin/env python3
"""Voice the whole episode in ONE take (same voice, same energy for every line) -> vo/takeA.mp3

  python tts.py edge        [--voice th-TH-NiwatNeural] [--rate +0%]       free (Microsoft Edge neural voices, needs internet)
  python tts.py elevenlabs  --voice-id <id> [--model eleven_multilingual_v2] needs ELEVENLABS_API_KEY in the environment
  python tts.py own                                                        you record / bring your own: put it at vo/takeA.mp3

Lines come from script.md in order, one per row; the line breaks become the short pauses align.py uses.
Write numbers as words, avoid ranges ("80 to 85"), and spell loan words the way they should sound
(Thai: add ไม้ไต่คู้ ็ where a vowel must be short, e.g. "ล็อก" not "ลอก"). Listen before you move on.
List edge voices: python -m edge_tts --list-voices   (Thai: th-TH-NiwatNeural male, th-TH-PremwadeeNeural female)
"""
import argparse
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

from common import read_script


def edge(text: str, voice: str, rate: str, out: Path) -> None:
    try:
        import edge_tts
    except ImportError:
        sys.exit("edge-tts missing: python -m pip install edge-tts")

    async def go() -> None:
        await edge_tts.Communicate(text, voice, rate=rate).save(str(out))

    asyncio.run(go())


def eleven(text: str, voice_id: str, model: str, out: Path) -> None:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("set ELEVENLABS_API_KEY (your own key) first")
    body = json.dumps({"text": text, "model_id": model}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128", data=body,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=300) as r:
        out.write_bytes(r.read())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("engine", choices=["edge", "elevenlabs", "own"])
    ap.add_argument("--voice", default="th-TH-NiwatNeural")
    ap.add_argument("--rate", default="+0%")
    ap.add_argument("--voice-id")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--out", default="vo/takeA.mp3")
    a = ap.parse_args()
    lines = [r["th"] for r in read_script()]
    text = "\n".join(lines)
    Path("vo").mkdir(exist_ok=True)
    Path("vo/text.txt").write_text(text + "\n", encoding="utf-8")
    out = Path(a.out)
    if a.engine == "own":
        print("Record or generate the take yourself (one take, lines in order), save it as", out)
        print("The text is in vo/text.txt")
        return
    if a.engine == "edge":
        edge(text, a.voice, a.rate, out)
    else:
        if not a.voice_id:
            sys.exit("--voice-id required for elevenlabs")
        eleven(text, a.voice_id, a.model, out)
    print("wrote", out, "- now: python transcribe.py", out)


if __name__ == "__main__":
    main()
