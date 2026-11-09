#!/usr/bin/env python3
"""Story Series skill pack installer — Windows / macOS / Linux.

  python install.py                      check tools, install missing ones (asks first), install the skills
  python install.py --target codex       skills for Codex (or: claude, both). Default: auto (Codex when run inside Codex)
  python install.py --doctor             only report what is installed / missing
  python install.py --starter DIR        also create DIR/ep01 from the template, npm install it and render a test still
  python install.py --demo DIR           starter + the whole demo episode: voice, timing, sound, render, mix, cover
  python install.py --remotion-skills    also add Remotion's official agent skills (npx skills add remotion-dev/skills)
  python install.py --yes                do not ask before installing system tools (REQUIRED when an AI agent runs this:
                                         there is no keyboard to answer y/N)

AI agents (Claude Code, Codex): run   python install.py --yes --demo ./story-demo   from this folder.
Read AGENTS.md first.

What it installs
  skills   threejs-story-series, story-rule-script, code-rig-characters  ->  ~/.claude/skills/ (or $CODEX_HOME/skills)
  tools    Node.js LTS (18+), ffmpeg/ffprobe        via winget (Windows) / Homebrew (macOS) / apt (Linux, needs sudo)
  python   numpy, faster-whisper, edge-tts>=7       via pip --user
  per project (starter / each episode): npm install (Remotion 4, three.js, React) + Remotion's headless Chrome (auto)
"""
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = ["threejs-story-series", "story-rule-script", "code-rig-characters"]
PY_PKGS = ["numpy", "faster-whisper", "edge-tts>=7"]
OS = platform.system()  # Windows / Darwin / Linux

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def sh(args, check=True, **kw):
    print("  $", " ".join(str(a) for a in args))
    return subprocess.run(args, check=check, **kw)


def version_of(cmd, args=("--version",)):
    exe = shutil.which(cmd)
    if not exe:
        return None
    try:
        out = subprocess.run([exe, *args], capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return "?"


def node_ok():
    v = version_of("node", ("-v",))
    if not v:
        return False, "missing"
    m = re.match(r"v(\d+)", v)
    return (bool(m) and int(m.group(1)) >= 18), v


def py_pkg(name):
    mod = {"faster-whisper": "faster_whisper", "edge-tts>=7": "edge_tts"}.get(name, name)
    r = subprocess.run([sys.executable, "-c", f"import {mod}"], capture_output=True)
    return r.returncode == 0


def doctor():
    ok_node, nv = node_ok()
    rows = [
        ("python", sys.version.split()[0], sys.version_info >= (3, 9)),
        ("node 18+", nv, ok_node),
        ("npm", version_of("npm", ("-v",)) or "missing", bool(shutil.which("npm"))),
        ("ffmpeg", version_of("ffmpeg", ("-version",)) or "missing", bool(shutil.which("ffmpeg"))),
        ("ffprobe", "found" if shutil.which("ffprobe") else "missing", bool(shutil.which("ffprobe"))),
    ]
    for p in PY_PKGS:
        rows.append((f"pip: {p}", "ok" if py_pkg(p) else "missing", py_pkg(p)))
    print("\nTool check")
    for name, v, ok in rows:
        print(f"  {'OK ' if ok else 'NO '} {name:22s} {v}")
    print("  (optional) ELEVENLABS_API_KEY", "set" if os.environ.get("ELEVENLABS_API_KEY") else "not set - edge voices are used by default")
    return all(ok for _, _, ok in rows)


SKIPPED = []


def ask(q, yes):
    if yes:
        return True
    if not sys.stdin or not sys.stdin.isatty():
        print(f"  {q} -> NOT installed: no interactive terminal to answer y/N. Rerun with --yes (or install it yourself).")
        SKIPPED.append(q)
        return False
    try:
        return input(f"{q} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        SKIPPED.append(q)
        return False


def auto_target():
    """Codex sets CODEX_SANDBOX* in the shells it runs; Claude Code sets CLAUDECODE."""
    if any(k.startswith("CODEX_SANDBOX") for k in os.environ) or os.environ.get("CODEX_CI"):
        return "codex"
    return "claude"


def online(url="https://registry.npmjs.org/", timeout=8):
    import urllib.request
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


def install_system(yes):
    ok_node, _ = node_ok()
    need_ff = not (shutil.which("ffmpeg") and shutil.which("ffprobe"))
    if ok_node and not need_ff:
        return
    print("\nMissing system tools:", ", ".join(x for x, n in (("Node.js", not ok_node), ("ffmpeg", need_ff)) if n))
    if OS == "Windows":
        if not shutil.which("winget"):
            print("  winget not found. Install Node.js LTS from nodejs.org and ffmpeg from gyan.dev/ffmpeg, then rerun.")
            return
        if ask("Install with winget?", yes):
            if not ok_node:
                sh(["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS", "--accept-package-agreements", "--accept-source-agreements"], check=False)
            if need_ff:
                sh(["winget", "install", "-e", "--id", "Gyan.FFmpeg", "--accept-package-agreements", "--accept-source-agreements"], check=False)
            print("  Close and reopen the terminal so PATH updates, then rerun this installer.")
    elif OS == "Darwin":
        if not shutil.which("brew"):
            print('  Homebrew not found. Install it from https://brew.sh then rerun (or install Node + ffmpeg yourself).')
            return
        if ask("Install with Homebrew?", yes):
            pk = (["node"] if not ok_node else []) + (["ffmpeg"] if need_ff else [])
            sh(["brew", "install", *pk], check=False)
    else:
        print("  Debian/Ubuntu:  sudo apt-get update && sudo apt-get install -y ffmpeg")
        print("  Node 18+:       https://nodejs.org (or nvm: nvm install --lts) - distro packages are often too old")
        if need_ff and shutil.which("apt-get") and ask("Run the apt-get command for ffmpeg now (sudo)?", yes):
            sh(["sudo", "apt-get", "update"], check=False)
            sh(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False)


def install_python(yes):
    missing = [p for p in PY_PKGS if not py_pkg(p)]
    if not missing:
        return
    print("\nMissing Python packages:", ", ".join(missing))
    if ask(f"pip install --user {' '.join(missing)}?", yes):
        r = sh([sys.executable, "-m", "pip", "install", "--user", "-U", *missing], check=False)
        if r.returncode != 0:
            # Homebrew / Debian Pythons refuse pip (PEP 668 "externally-managed-environment"); a --user install is still safe
            print("  pip refused - retrying as a user install with --break-system-packages")
            sh([sys.executable, "-m", "pip", "install", "--user", "-U", "--break-system-packages", *missing], check=False)


def install_skills(target):
    home = Path.home()
    dests = []
    if target in ("claude", "both"):
        dests.append(("Claude Code", home / ".claude" / "skills"))
    if target in ("codex", "both"):
        dests.append(("Codex", Path(os.environ.get("CODEX_HOME", home / ".codex")) / "skills"))
    for label, root in dests:
        root.mkdir(parents=True, exist_ok=True)
        print(f"\n{label}:")
        for name in SKILLS:
            dst = root / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(HERE / "skills" / name, dst, ignore=shutil.ignore_patterns("node_modules", ".DS_Store", "__pycache__", "out"))
            print("  installed", dst)


def remotion_skills():
    npx = shutil.which("npx")
    if not npx:
        print("npx not found; skip Remotion skills")
        return
    print("\nRemotion's official agent skills (downloaded from github.com/remotion-dev/skills):")
    sh([npx, "-y", "skills", "add", "remotion-dev/skills"], check=False)


def starter(dir_):
    root = Path(dir_).resolve()
    ep = root / "ep01"
    scripts = HERE / "skills" / "threejs-story-series" / "scripts"
    if not ep.exists():
        sh([sys.executable, str(scripts / "new_episode.py"), str(ep)])
    npm = shutil.which("npm")
    npx = shutil.which("npx")
    if not npm:
        print("npm missing - install Node first")
        return
    sh([npm, "install", "--no-audit", "--no-fund"], cwd=ep)
    sh([npx, "tsc", "--noEmit", "-p", "."], cwd=ep, check=False)
    sh([npx, "remotion", "still", "src/index.ts", "Film", "out/test-still.png", "--frame=60", "--gl=angle"], cwd=ep, check=False)
    print(f"\nStarter ready: {ep}\n  open the editor preview:  cd \"{ep}\" && npx remotion studio src/index.ts")
    print("  full demo (voice -> render -> mix): see QUICKSTART in README.md")


def demo(dir_):
    """starter + the full demo episode. Each step prints its command; a failed step stops with the reason."""
    ep = Path(dir_).resolve() / "ep01"
    S = HERE / "skills" / "threejs-story-series" / "scripts"
    py = sys.executable
    npx = shutil.which("npx")
    if not npx:
        sys.exit("npx missing - install Node.js 18+ first (rerun with --yes)")
    steps = [
        ("voice (edge-tts, needs internet)", [py, str(S / "tts.py"), "edge"]),
        ("transcribe (first run downloads a ~500 MB model)", [py, str(S / "transcribe.py"), "vo/takeA.mp3", "--lang", "th"]),
        ("align lines to the voice", [py, str(S / "align.py"), "vo/takeA.mp3"]),
        ("pauses -> src/lines.json", [py, str(S / "splice.py")]),
        ("sound effects", [py, str(S / "sound.py"), "sfx", "vo/sfx"]),
        ("room-tone bed", [py, str(S / "sound.py"), "room", "."]),
        ("render (2-6 min)", [npx, "remotion", "render", "src/index.ts", "Film", "out/raw.mp4", "--crf=20", "--concurrency=2", "--gl=angle"]),
        ("mix -> out/ep01-v1.mp4", [py, str(S / "mix.py")]),
        ("cover -> out/cover.png", [npx, "remotion", "still", "src/index.ts", "Cover", "out/cover.png", "--frame=600", "--gl=angle"]),
    ]
    for i, (label, cmd) in enumerate(steps, 1):
        print(f"\n[demo {i}/{len(steps)}] {label}")
        r = sh(cmd, check=False, cwd=ep)
        if r.returncode != 0:
            sys.exit(f"demo stopped at step {i} ({label}). Fix the error above, then rerun the same command from {ep}.")
    print(f"\nDemo done:\n  video  {ep / 'out' / 'ep01-v1.mp4'}\n  cover  {ep / 'out' / 'cover.png'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default="auto", choices=["auto", "claude", "codex", "both"])
    ap.add_argument("--doctor", action="store_true")
    ap.add_argument("--starter")
    ap.add_argument("--demo", metavar="DIR")
    ap.add_argument("--remotion-skills", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--no-deps", action="store_true", help="skip tool / pip installation")
    a = ap.parse_args()
    if a.doctor:
        sys.exit(0 if doctor() else 1)
    if a.target == "auto":
        a.target = auto_target()
        print(f"Skills target: {a.target} (auto; override with --target claude|codex|both)")
    net = online()
    if not net:
        print("\nWARNING: no internet from this shell. npm, pip, the voice and the whisper model need it.\n"
              "  Codex: allow network access for this command (or run in full-access mode). Then rerun.")
    doctor()
    if not a.no_deps:
        install_system(a.yes)
        install_python(a.yes)
    install_skills(a.target)
    if a.remotion_skills:
        remotion_skills()
    if a.starter or a.demo:
        starter(a.demo or a.starter)
    if a.demo:
        demo(a.demo)
    print("\nDone. Final check:")
    doctor()
    if SKIPPED:
        print("\nSkipped (needs --yes or a manual install):\n  " + "\n  ".join(SKIPPED))
    print("\nRestart Claude Code / Codex, then ask for example:\n  \"สร้างซีรีส์ใหม่ตามสกิล threejs-story-series เรื่อง … ตอนที่ 1\"\n  \"Make episode 1 of a new story series about …\"")


if __name__ == "__main__":
    main()
