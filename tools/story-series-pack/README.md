# Story Series Skill Pack — ซีรีส์เรื่องสั้นแนวตั้ง ตัวละคร 3D ทำด้วยโค้ดล้วน

สกิลชุดนี้สอน AI (Claude Code หรือ Codex) ให้ทำซีรีส์คลิปแนวตั้ง 9:16 แบบ "กฎเอาตัวรอด" เช่น
"ถ้ามีคนเคาะประตูตอนตีสอง อย่าตอบ" ตัวละคร 3D ขยับได้จริง ฉาก แสง กล้อง และเสียงประกอบ
**สร้างจากโค้ดทั้งหมด ไม่ใช้การเจนรูปหรือเจนวิดีโอ** ทำต่อเนื่องได้ตอนต่อตอน ตัวละครและฉากเหมือนเดิมทุกตอน
ลุคตั้งต้นเป็นแบบกลาง ๆ (ฉากจิ๋วโทนอุ่น ตัวละครหัวเล็กแขนขายาว การ์ดกระดาษครีม เสียงบรรยากาศห้อง)
เปลี่ยนสัดส่วนตัวละคร สี ฟอนต์ แสง ฉาก ภาษา และเสียงเป็นสไตล์ของคุณเองได้ทั้งหมด

## ให้ AI ติดตั้งให้ (ง่ายสุด)
แตก zip แล้วเปิด Claude Code หรือ Codex ในโฟลเดอร์นี้ (หรือโยน zip เข้าไปในแชท) แล้วพิมพ์
> ติดตั้งสกิลนี้ แล้วทำตัวอย่างให้ดูหน่อย

AI จะอ่าน `AGENTS.md` / `CLAUDE.md` แล้วรัน `install.py --yes --demo ./story-demo` ให้เอง
(กดอนุญาตคำสั่งที่มันขอ · Codex ต้องอนุญาตให้ใช้อินเทอร์เน็ต · ครั้งแรกใช้ 15–30 นาที โหลด ~1 GB)
ผลลัพธ์: `story-demo/ep01/out/ep01-v1.mp4` + `out/cover.png`
ใช้กับ claude.ai หน้าเว็บ / ChatGPT ไม่ได้ (ต้องรันบนเครื่องคุณ)

## มีอะไรในชุด
| สกิล | ทำอะไร |
|---|---|
| `threejs-story-series` | ขั้นตอนทำทั้งตอน: บท → เสียงพากย์ → ซับตรงเสียง → ช็อต 3D → ตรวจภาพ → เรนเดอร์ → เสียง/มิกซ์ → ปก รวมถึงการแก้ (ซับเพี้ยน ออกเสียงผิด เลือดลอย ช็อตแข็ง) มีโปรเจกต์ตั้งต้นพร้อมตอนตัวอย่าง 28 วิที่เรนเดอร์ได้ทันที |
| `story-rule-script` | สูตรเขียนบท ฮุก "ถ้า… อย่า…", ข้อเท็จจริงมีตัวเลข → การกระทำ, สัตว์คู่หู, ประโยคหักมุม "ทุกอย่างถูกหมด ยกเว้นเรื่องเดียว", cliffhanger, ไบเบิลซีรีส์ |
| `code-rig-characters` | ออกแบบตัวละครจาก "การ์ดตัวละคร" (ข้อความ) → rig 3D, ปรับสัดส่วน (ขา แขน ลำตัว ความหนา คอ ขนาดหัว), เพิ่มชุด/ทรงผม/พร็อพ, ท่าทาง (เดิน/วิ่งไม่ไถล, หมอบ, นั่ง, เคาะ), สัตว์เลี้ยง, แผ่นตรวจ 4 มุม |

## ติดตั้งเอง (ครั้งเดียว)
macOS / Linux
```bash
bash install.sh --starter ~/my-series
```
Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 --starter C:\my-series
```
ตัวติดตั้งจะ:
1. ตรวจและติดตั้ง Node.js 18+, ffmpeg (ผ่าน winget / Homebrew / apt — ถามก่อนทุกครั้ง)
2. ติดตั้ง Python packages: numpy, faster-whisper (ถอดเสียง), edge-tts (เสียงพากย์ฟรี)
3. คัดลอกสกิลทั้ง 3 ไปที่ `~/.claude/skills/` (`--target codex` หรือ `both` สำหรับ Codex)
4. (`--starter`) สร้างโปรเจกต์ตอนที่ 1 + `npm install` + เรนเดอร์ภาพทดสอบ
5. (`--demo DIR`) ทำตอนตัวอย่างให้จบเลย: เสียง → ซับ → เรนเดอร์ → มิกซ์ → ปก
6. (ไม่บังคับ `--remotion-skills`) เพิ่มสกิลทางการของ Remotion

ถ้ารันโดยไม่มีหน้าจอให้ตอบ y/N (เช่น AI รันให้) ต้องใส่ `--yes` ไม่งั้นจะข้ามการติดตั้งเครื่องมือและบอกว่าข้ามอะไรไป

ตรวจเครื่องอย่างเดียว: `python install.py --doctor`

## เริ่มใช้
เปิด Claude Code ในโฟลเดอร์ซีรีส์ แล้วสั่ง เช่น
- "สร้างซีรีส์ใหม่ เรื่องคนเฝ้าหอพักกะดึก 10 ตอน ทำไบเบิลกับตัวละครก่อน"
- "ทำตอนที่ 1 จากไบเบิล ใช้เสียง th-TH-PremwadeeNeural"
- "ตอน 3 ซับขึ้นไม่ตรงเสียง" / "แก้คำว่า … ให้ออกเสียงสั้น" / "ฉากวิ่งดูแข็ง ทำใหม่"

## QUICKSTART — ทำตอนตัวอย่างให้จบด้วยมือ (ทดสอบว่าเครื่องพร้อม)
```bash
cd ~/my-series/ep01
S=~/.claude/skills/threejs-story-series/scripts
python3 $S/tts.py edge                       # เสียงพากย์ → vo/takeA.mp3
python3 $S/transcribe.py vo/takeA.mp3        # ถอดเสียง (โหลดโมเดลครั้งแรก ~500 MB)
python3 $S/align.py vo/takeA.mp3             # ต้องได้ overlaps: 0
python3 $S/splice.py                         # → src/lines.json (เวลาที่ภาพใช้)
python3 $S/sound.py sfx vo/sfx && python3 $S/sound.py room .   # เสียงบรรยากาศห้อง (อยากได้เพลง: sound.py bgm .)
npx remotion render src/index.ts Film out/raw.mp4 --crf=20 --concurrency=2 --gl=angle
python3 $S/mix.py                            # → out/ep01-v1.mp4  (−14 LUFS)
npx remotion still src/index.ts Cover out/cover.png --frame=600 --gl=angle
```
Windows: ใช้ `python` แทน `python3` และ `$S = "$HOME\.claude\skills\threejs-story-series\scripts"`

## ทำให้เป็นสไตล์ของคุณ
ลุคตั้งต้นเป็นแค่จุดเริ่ม ควรเปลี่ยนก่อนทำตอนแรก (บอก AI ได้เลย เช่น "ตัวละครอ้วนกลม หัวโต สีพาสเทล ไม่เอาเบลอขอบ")
- สัดส่วนตัวละคร: `build` + `headS` ใน `src/rig/cast.ts` (ทั้งซีรีส์ใช้ชุดเดียวกัน) → ตรวจด้วย `Turn-<ชื่อ>`
- สี / ฟอนต์ / ซับ / การ์ด: `src/kit/ui.tsx`, `src/episode.json`, `src/ui/captions.tsx`, `src/ui/cards.tsx`
- แสง / เลนส์: ไฟและ `Glow` ในไฟล์ฉาก, เบลอขอบ `tilt` ของ `Shot` (`src/kit/three.tsx`), `Vig` / `Grain` ใน `Film.tsx`
- ฉาก: ไฟล์ใหม่ใน `src/sets/` (สร้างโลกครั้งเดียว ถ่ายหลายมุม)
- เสียง: เสียงพากย์ (edge, ElevenLabs ของคุณ, หรืออัดเอง), `sound.py room` หรือเพลง `sound.py bgm --key A --mood warm`, เสียงป๊อปใน `public/sfx`
- ภาษา: เขียนบทภาษาไหนก็ได้ ใช้เสียงและ `--lang` ให้ตรง
รายละเอียดใน `skills/threejs-story-series/references/style-guide.md`

## สิ่งที่ต้องมี
คอมพิวเตอร์ Windows 10+/macOS 12+/Linux, RAM 8 GB+, เนื้อที่ว่าง ~3 GB (node_modules + โมเดลถอดเสียง + ไฟล์เรนเดอร์),
อินเทอร์เน็ตตอนติดตั้งและตอนสร้างเสียงด้วย edge-tts. ไม่ต้องมีการ์ดจอแยก (เรนเดอร์ 30 วิ ≈ 2–4 นาที)

## หมายเหตุลิขสิทธิ์
ดู `LICENSE.md` — Remotion ฟรีสำหรับบุคคลและบริษัทไม่เกิน 3 คน บริษัทใหญ่กว่านั้นต้องซื้อ company licence

---

# English summary
Three skills that teach Claude Code / Codex to produce a vertical "survival rule" story series with real 3D
characters animated entirely in code (three.js + Remotion): no image or video generation. The base look is neutral
(warm miniature-diorama sets, slender plain-faced figures, cream paper cards, room-tone sound) and every part of it
is a knob, so each series can look like its own.
Easiest: open Claude Code or Codex in this folder and say "install this skill and show me an example" — the agent
follows AGENTS.md and runs `install.py --yes --demo ./story-demo`. By hand: `bash install.sh --demo ~/my-series`
(or `install.ps1` on Windows): it checks/installs Node 18+, ffmpeg, numpy, faster-whisper, edge-tts, copies the
skills to `~/.claude/skills` (Codex: `--target codex`), creates episode 1 and renders the demo end to end.
Agents must pass `--yes` (no keyboard for y/N prompts). Not for claude.ai web / ChatGPT: it renders on your machine.
