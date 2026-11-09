---
name: story-rule-script
description: >-
  Write scripts and series bibles for short vertical story reels in the "survival rule" format: a
  second-person narrator, a counter-instinct rule as the hook ("If X happens, don't Y"), real facts with
  numbers turned into actions, a sidekick animal that notices first, ticking timestamps, the twist line
  "You got everything right, except one thing" + a physical detail planted earlier, and a cliffhanger that
  becomes the next episode's hook. Works for horror/survival and for money/love/life topics (emotional twist).
  Use when the user wants a new episode script, a season outline, a series bible, or wants to fix a confusing
  episode. Output plugs into threejs-story-series (script.md table).
---

# Story rule scripts

## Output
1. `script.md` table for the episode (format below) + a 3-line note under it (what is fact vs fiction,
   what was planted for the twist, what the cliffhanger sets up).
2. For a new series: a series bible from `references/bible-template.md`.
3. Optional: caption draft for posting (hook line, a hint at the twist without spoiling it, a comment question,
   "(fiction)" when it is fiction, 5–7 hashtags, no emoji).

## The table (exact — the timing tools read it)
```
| # | VO | Subtitle |
|---|---|---|
| 1 | phrase phrase phrase | Full sentence in the second language. |
```
- One spoken sentence per row, 14–22 rows, ≈ 65–72 s when spoken.
- Separate phrases with spaces (one phrase = one caption), ≤ 7 words per phrase.
- Numbers as words in the VO (the subtitle may use digits). No number ranges ("80 to 85" → "over 80").
- Names and loan words spelled the way the voice must say them.

## Write it
Follow `references/formula.md` (hook formula, skeleton, sidekick, timestamps, twist, cliffhanger, voice).
Then run the checklist at the end of that file. Rewrite until every box is ticked.

## Clarity rules (from real viewer feedback)
- Each beat must be understandable from VO + picture alone. If a step needs a diagram, the step is too
  complicated: simplify the mechanism, or spend two lines on it (cause, then effect), not a text panel.
- One mechanism per episode. Name the thing once, then refer to it the same way every time.
- The cold open of a continuing episode restates the previous cliffhanger in one line and moves on.
- The twist must be SEEN (a detail on screen), not explained.

## Facts
Every fact with a number must be true and used immediately as an action. Check facts against a primary
source before production and keep the source in the episode notes. Pure fiction says "(fiction)" in the post.

## Series
- Keep the bible updated after every episode: what was revealed, which objects exist (they must pay off),
  who may die / who never dies, the gore level, the season mystery ladder.
- Each episode = self-contained (rule → plan → twist) AND one rung of the season mystery.
- Next episode's hook comes from this episode's cliffhanger, as a new "If…, don't…" rule.
