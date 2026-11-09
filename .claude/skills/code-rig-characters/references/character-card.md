# Character card (fill one per character, keep it in the series bible)

```
Name (as the voice says it):
Role in the story:                       (you / sidekick / friend / threat / adult)
Age band + height:                       (adult 0.86-0.94 · child ~0.68)
Figure:                                  (series build: SLIM, or your own numbers — same for the whole cast)
Silhouette in one line:                  (e.g. "ponytail + oversized grey hoodie + flashlight")
Palette: skin / hair / top / bottom / shoes / accent:
Hair:                                    short | pony | messy | spiky | bob (+ length, matte or glossy)
Outfit:                                  tee | hoodie | shirt | coat | scrubs | uniform | blouse (+skirt) | jersey | <new>
Face:                                    dots | big
Never-change details (2):                (seen in EVERY shot)
Prop:                                    (flashlight / phone / tape / keys / backpack / headphones / glasses / clip / <new>)
Default face:                            (calm: browUp 0.4 · scared: browUp 1, mouth 0.2 · angry: browUp -0.4)
Can die?:
```

## Example
```
Name: Mali            Role: the neighbour across the hall      Age: adult, 0.9      Figure: SLIM
Silhouette: short grey hair + round glasses + long cardigan look (shirt in a muted green)
Palette: skin #D3A07A / hair #8C8A86 / shirt #8FA58A / trousers #4E5056 / shoes #2A2420 / accent glasses
Hair: short, matte       Outfit: shirt       Face: dots
Never-change: round glasses; keys in the right hand      Prop: keys
Default face: worried (browUp 0.6)    Can die: no
```
→ `export const MALI: Look = { ...ADULT, top: "#8FA58A", pants: "#4E5056", holdR: "keys", height: 0.9 };`
