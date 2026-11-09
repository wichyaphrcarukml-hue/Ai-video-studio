"""Shared helpers for the episode scripts (Windows / macOS / Linux). Run every script from the episode folder."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Thai text on Windows consoles


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"{tool} not found on PATH. Run the pack installer (install.py) or install it yourself.")
    return path


def run(args: List[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=capture, text=capture)


def duration(path: str) -> float:
    out = subprocess.run([need("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def read_script(path: str = "script.md") -> List[Dict[str, str]]:
    """rows like `| 1 | VO text | subtitle |` -> [{"th": ..., "en": ...}] in order"""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*\d+\s*\|", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append({"th": cells[1], "en": cells[2] if len(cells) > 2 else ""})
    if not rows:
        sys.exit(f"no `| n | text | subtitle |` rows in {path}")
    return rows


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path: str, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def resolve_time(ref, lines_path: str = "src/lines.json") -> float:
    """seconds from a number or a line reference: "L5" start of line 5, "L5e" its end, "L5+0.4", "END" (end card start = last end + 0.4)"""
    if isinstance(ref, (int, float)):
        return float(ref)
    L = load(lines_path)["lines"]
    m = re.match(r"^\s*(L(\d+)(e?)|END)\s*([+-]\s*[\d.]+)?\s*$", str(ref))
    if not m:
        return float(ref)
    if m.group(1) == "END":
        base = L[-1]["end"] + 0.4
    else:
        line = L[int(m.group(2)) - 1]
        base = line["end"] if m.group(3) else line["t"]
    return base + (float(m.group(4).replace(" ", "")) if m.group(4) else 0.0)
