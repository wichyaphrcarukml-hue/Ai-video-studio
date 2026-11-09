# Ai-video-studio

Story-series skills (`threejs-story-series`, `story-rule-script`, `code-rig-characters`) live in `.claude/skills/`.
The original pack installer and README are in `tools/story-series-pack/`.

## Running on a Claude Code cloud session
No GPU, and outbound HTTPS goes through a proxy. Do not use `install.py --demo` or the skill's plain render
commands there. Use `bash tools/cloud/make_episode.sh <episode-dir>`; it applies these fixes:
- edge-tts via `tools/cloud/tts_proxy.py` (adds the proxy and its CA)
- `av<17` for faster-whisper
- Remotion flags: `--gl=swangle --chrome-mode=chrome-for-testing --browser-executable=<preinstalled Chromium>`

The session must run in the personal cloud environment "Ai-video-studio", which allows the edge-tts and
Hugging Face hosts. Details and the host list are in `tools/cloud/README.md`.
