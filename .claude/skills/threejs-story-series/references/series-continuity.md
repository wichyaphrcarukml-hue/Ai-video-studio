# Series continuity — episode to episode

- Start each episode by COPYING the previous one (`new_episode.py --from prev --ep N`): cast, sets, kit stay identical.
  Then update episode.json: `ep`, `title`, `rule`, red/amb keywords, `next.ep` (= N+1) and `next.line`, `coverFrame`.
  Cover text comes from episode.json — never hand-edit it, or the old episode number survives.
- The cold open of episode N continues the cliffhanger of N−1 in ONE line ("Because the fourth knock came from
  inside your room"), not a recap montage and not a card per beat.
- Keep a series bible (story-rule-script): cast + never-change details, who may die / who never dies, the season
  mystery and what each episode reveals, locations, recurring objects, gore level.
- After each episode add to the bible: what was revealed, objects introduced (they must come back), new characters.
- One new set piece per episode (a location or a mechanism), reuse everything else.
- Each new character: write the card, add to `cast.ts`, render `Turn-<id>`, compare with the card before shooting.
- End card always shows the NEXT number. Cover always shows THIS number + title on top.
- Versioning: fixes ship as -v2, -v3 next to v1; never overwrite the delivered file silently.
