# ทำตอนบน Claude Code cloud session

เครื่องคลาวด์ไม่มีการ์ดจอ และออกเน็ตผ่าน HTTPS proxy ที่อนุญาตเฉพาะบางโฮสต์ ตัวติดตั้ง `install.py --demo`
จึงใช้ตรง ๆ ไม่ได้ โฟลเดอร์นี้รวมวิธีแก้ที่ใช้ได้จริงไว้ (บนคอมพิวเตอร์ตัวเองไม่ต้องใช้ ใช้ตัวติดตั้งปกติ)

## ใช้งาน
```bash
# สร้างตอนใหม่จาก template
python3 .claude/skills/threejs-story-series/scripts/new_episode.py series/ep01
# ทำทั้งตอน: เสียง → ซับ → เรนเดอร์ → มิกซ์ → ปก
bash tools/cloud/make_episode.sh series/ep01            # ค่าเริ่มต้น --lang th
```
ผลลัพธ์: `series/ep01/out/<ep>-v1.mp4` และ `out/cover.png`

## ต้องตั้งค่าก่อน: environment "Ai-video-studio"
ใช้ cloud environment ส่วนตัวชื่อ **Ai-video-studio** (ไม่ใช่ Default) ที่อนุญาตโฮสต์เหล่านี้:

| โฮสต์ | ใช้ทำอะไร |
|---|---|
| `speech.platform.bing.com` | เสียงพากย์ edge-tts |
| `huggingface.co`, `us.aws.cdn.hf.co`, `cdn-lfs.huggingface.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co`, `transfer.xethub.hf.co` | โหลดโมเดลถอดเสียง faster-whisper (~500 MB, ครั้งแรกของแต่ละเครื่อง) |

ฟอนต์ Google (`fonts.gstatic.com`) กับ npm / PyPI ผ่านได้อยู่แล้ว

## ปัญหาที่เจอและวิธีแก้
| อาการ | สาเหตุ | วิธีแก้ (ทำใน `make_episode.sh` แล้ว) |
|---|---|---|
| `tts.py edge` → `Cannot connect to host speech.platform.bing.com` | edge-tts (aiohttp) ไม่อ่าน `HTTPS_PROXY` และไม่เชื่อ CA ของ proxy | รันผ่าน `tools/cloud/tts_proxy.py` ซึ่งใส่ proxy + CA bundle ให้ |
| `transcribe.py` → `open() got an unexpected keyword argument 'metadata_errors'` | `av` 17+ ใช้กับ faster-whisper 1.2 ไม่ได้ | `pip install --user "av<17"` |
| `transcribe.py` → `ProxyError 403` / `us.aws.cdn.hf.co` | โฮสต์โหลดโมเดลไม่อยู่ใน allowlist | เพิ่มโฮสต์ในตารางด้านบน |
| `remotion` → `ENOTFOUND remotion.media` | Remotion พยายามโหลด Chrome ของตัวเอง | `--chrome-mode=chrome-for-testing --browser-executable=/opt/pw-browsers/chromium-*/chrome-linux64/chrome` |
| ฟอนต์ไม่ขึ้น `ERR_CERT_AUTHORITY_INVALID` | chrome-headless-shell ไม่อ่าน NSS store ที่มี CA ของ proxy | ใช้ Chromium ตัวเต็ม (ข้อบน) แทน headless shell |
| `Error creating WebGL context` | ไม่มีการ์ดจอ, `--gl=angle` / `swiftshader` ใช้ไม่ได้ | `--gl=swangle` |
| ติดตั้ง pip แล้วแต่ `import` ไม่เจอ | รัน Python ด้วย `-I` ซึ่งปิด user site-packages | อย่าใช้ `-I` กับสคริปต์ของสกิล |

ระยะเวลาโดยประมาณ (ตอน 28 วิ): เสียง+ซับ ~1 นาที (ไม่นับโหลดโมเดลครั้งแรก), เรนเดอร์ ~15–20 นาทีด้วย swangle
