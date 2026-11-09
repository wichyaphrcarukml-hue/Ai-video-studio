#!/usr/bin/env bash
# Build one story-series episode end to end on a Claude Code cloud session (no GPU, HTTPS proxy).
#   bash tools/cloud/make_episode.sh <episode-dir> [--lang th]
# Steps: deps check -> npm install -> voice -> transcribe -> align -> splice -> sfx/room -> render -> mix -> cover
# Output: <episode-dir>/out/<ep>-v1.mp4 and out/cover.png
set -euo pipefail

EP="$(cd "${1:?usage: make_episode.sh <episode-dir> [--lang th]}" && pwd)"; shift
LANG_ARGS=("$@"); [ ${#LANG_ARGS[@]} -eq 0 ] && LANG_ARGS=(--lang th)
HERE="$(cd "$(dirname "$0")" && pwd)"
S="${STORY_SCRIPTS:-$HOME/.claude/skills/threejs-story-series/scripts}"
[ -d "$S" ] || S="$(cd "$HERE/../.." && pwd)/.claude/skills/threejs-story-series/scripts"

# Python deps. av>=17 breaks faster-whisper 1.2 ("open() got an unexpected keyword argument 'metadata_errors'").
python3 -c "import faster_whisper, edge_tts, numpy, av; assert int(av.__version__.split('.')[0]) < 17" 2>/dev/null \
  || python3 -m pip install --user -q -U faster-whisper "edge-tts>=7" numpy "av<17"

# Remotion: use the preinstalled Chromium (its own download host is not reachable) and software WebGL (no GPU).
BROWSER="${REMOTION_BROWSER:-$(ls /opt/pw-browsers/chromium-*/chrome-linux*/chrome 2>/dev/null | head -1)}"
R=(--gl=swangle)
[ -n "$BROWSER" ] && R+=(--chrome-mode=chrome-for-testing "--browser-executable=$BROWSER")

cd "$EP"
NAME="$(basename "$EP")"
[ -d node_modules ] || npm install --no-audit --no-fund
mkdir -p out

echo "[1/8] voice";       python3 "$HERE/tts_proxy.py" "$S/tts.py" edge
echo "[2/8] transcribe";  python3 "$S/transcribe.py" vo/takeA.mp3 "${LANG_ARGS[@]}"
echo "[3/8] align";       python3 "$S/align.py" vo/takeA.mp3
echo "[4/8] splice";      python3 "$S/splice.py"
echo "[5/8] sound";       python3 "$S/sound.py" sfx vo/sfx && python3 "$S/sound.py" room .
echo "[6/8] render";      npx remotion render src/index.ts Film out/raw.mp4 --crf=20 --concurrency=2 "${R[@]}"
echo "[7/8] mix";         python3 "$S/mix.py"
echo "[8/8] cover";       npx remotion still src/index.ts Cover out/cover.png --frame=600 "${R[@]}"
echo "done: $EP/out ($NAME)"; ls -la out
