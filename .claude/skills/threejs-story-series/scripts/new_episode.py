#!/usr/bin/env python3
"""Start an episode folder.

  python new_episode.py <dest>                         from the skill's template (first episode of a series)
  python new_episode.py <dest> --from <prev episode>   copy the previous episode (cast, sets, kit) for the next one
  options: --ep N  (sets episode.json ep + next card to N+1)   --link-modules <folder with node_modules>  (share one install)

Copies code + config, never renders, voice takes or out/. Then: cd <dest>; npm install (or the link); edit script.md.
After copying from a previous episode, update in src/episode.json: title, rule, red/amb words, next.line, coverFrame.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "template"
SKIP = shutil.ignore_patterns("node_modules", "out", ".DS_Store", "takeA*", "takeB*", "*.wav", "words.json", "_*")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest")
    ap.add_argument("--from", dest="src")
    ap.add_argument("--ep", type=int)
    ap.add_argument("--link-modules")
    a = ap.parse_args()
    src = Path(a.src) if a.src else TEMPLATE
    dest = Path(a.dest)
    if dest.exists():
        sys.exit(f"{dest} already exists")
    shutil.copytree(src, dest, ignore=SKIP)
    for d in ("out", "vo/sfx", "public/sfx"):
        (dest / d).mkdir(parents=True, exist_ok=True)
    if (src / "public" / "sfx").exists():
        for f in (src / "public" / "sfx").glob("*.wav"):
            shutil.copy(f, dest / "public" / "sfx" / f.name)
    if a.ep:
        p = dest / "src" / "episode.json"
        ep = json.loads(p.read_text(encoding="utf-8"))
        ep["ep"] = a.ep
        nxt = ep.get("next", {})
        nxt["ep"] = re.sub(r"\d+", str(a.ep + 1), nxt.get("ep", "ตอนที่ 2")) if "ep" in nxt else f"ตอนที่ {a.ep + 1}"
        ep["next"] = nxt
        p.write_text(json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.link_modules:
        nm = Path(a.link_modules).resolve() / "node_modules"
        try:
            os.symlink(nm, dest / "node_modules", target_is_directory=True)
            print("linked", nm)
        except OSError:
            print("could not symlink (Windows without developer mode?) - run npm install in", dest)
    print("created", dest)


if __name__ == "__main__":
    main()
