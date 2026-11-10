---
name: ai-friend
description: >-
  Thai-language AI chat friend ("มิ้นท์") that talks like a real person: its own persona (name, age,
  personality), casual spoken Thai with short/long replies by mood, conversation history saved to a file
  so chats resume later, long-term facts about the user (name, job, likes...) extracted after each message,
  and typing-speed output split into several chat bubbles (|||). Use when the user wants to run, chat with,
  customize (persona, model, typing speed, memory file) or extend the AI friend / เพื่อนคุย AI.
---

# AI เพื่อนคุย (ai-friend)

Terminal chatbot in `scripts/ai_friend.py` (Anthropic Python SDK).

## Run
```bash
pip install anthropic
export ANTHROPIC_API_KEY="..."          # never paste the key into chat or commit it
python .claude/skills/ai-friend/scripts/ai_friend.py
```
It needs an interactive terminal (it reads `input()`), so the user runs it themselves; Claude can
edit/customize it. In a cloud session, `api.anthropic.com` access and the key must be provided by the
environment.

In-chat commands: `/ลืม` wipe memory · `/จำอะไร` show remembered facts · `/ออก` quit.

## Memory
`memory.json` in the current directory (override with `AI_FRIEND_MEMORY=/path/file.json`):
`{"history": [...messages], "facts": [...strings]}`. Last `MAX_HISTORY` (40) messages go to the model;
facts (max 50) are refreshed by a second model call after every user message. `memory.json` is
git-ignored — it holds personal chat data.

## Customize (top of the script)
- `PERSONA` — name, age, bio (the system prompt is built from it in `build_system_prompt`).
- `MODEL`, `MAX_HISTORY`, `TYPING_SPEED`.
- Style rules live in `build_system_prompt`: casual Thai, 1–2 sentences usually, no bullets/headings,
  own opinions, listen first when the friend is sad, admit being an AI if asked directly, `|||` splits bubbles.

## Web chat
`web/ai-friend-chat.html` is the same friend as a claude.ai Artifact page (published at
https://claude.ai/artifact/UgbGX4nax7LHMPHmEK8VPx, private to the owner until shared). No API key: it uses
the artifact `sample` capability (the viewer's own Claude account, `modelTier: "quick"`), and keeps each
viewer's chat + facts privately in `db` at `data/users/<id>/friend` (falls back to browser storage).
Same persona and system prompt as the script; replies split on `|||` play as separate bubbles with a typing
indicator. To change it, edit the file and republish with the Artifact tool using the same file path or the URL
above (capabilities: sample, db, user).
