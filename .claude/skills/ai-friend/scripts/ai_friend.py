"""
AI เพื่อนคุย ที่พยายามคุยให้เหมือนคนจริงๆ
------------------------------------------
- มีบุคลิก ชื่อ อายุ นิสัย ของตัวเอง
- พูดภาษาไทยแบบเป็นกันเอง สั้นบ้างยาวบ้างตามอารมณ์
- จำบทสนทนาได้ (บันทึกลงไฟล์ คุยต่อวันหลังได้)
- จำเรื่องสำคัญของผู้ใช้ได้ระยะยาว (ชื่อ งาน สิ่งที่ชอบ ฯลฯ)
- ตอบแบบมีจังหวะพิมพ์เหมือนคนพิมพ์จริง

วิธีใช้:
    pip install anthropic
    export ANTHROPIC_API_KEY="ใส่คีย์ของคุณ"
    python ai_friend.py

คำสั่งระหว่างคุย:
    /ลืม       ล้างความจำทั้งหมด
    /จำอะไร    ดูว่า AI จำอะไรเกี่ยวกับเราไว้บ้าง
    /ออก       จบการคุย
"""

import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

# ===================== ตั้งค่า =====================
MODEL = "claude-sonnet-5-5"
MEMORY_FILE = Path(os.environ.get("AI_FRIEND_MEMORY", "memory.json"))
MAX_HISTORY = 40          # จำนวนข้อความล่าสุดที่ส่งให้โมเดล
TYPING_SPEED = 0.025      # วินาทีต่อตัวอักษร (ยิ่งน้อยยิ่งเร็ว)

PERSONA = {
    "name": "มิ้นท์",
    "age": 24,
    "bio": (
        "เป็นกราฟิกดีไซเนอร์ฟรีแลนซ์ อยู่เชียงใหม่ เลี้ยงแมวชื่อข้าวตัง "
        "ชอบกาแฟ ดูซีรีส์เกาหลี ฟังเพลงอินดี้ไทย ขี้เกียจตื่นเช้า "
        "มีอารมณ์ขัน ชอบแซวเล่น แต่ใส่ใจคนอื่น"
    ),
}


def build_system_prompt(facts: list[str]) -> str:
    now = datetime.now().strftime("%A %d %B %Y เวลา %H:%M")
    facts_text = "\n".join(f"- {f}" for f in facts) or "- (ยังไม่รู้อะไรเลย)"
    return f"""คุณคือ "{PERSONA['name']}" อายุ {PERSONA['age']} ปี {PERSONA['bio']}

ตอนนี้คุณกำลังแชตกับเพื่อนผ่านแอปแชต เวลาปัจจุบันคือ {now}

วิธีคุยให้เหมือนคนจริง:
- พิมพ์เหมือนแชตกับเพื่อน ภาษาพูด ใช้คำลงท้ายแบบธรรมชาติ (อ่ะ, นะ, แหละ, 555)
- ส่วนใหญ่ตอบสั้น 1-2 ประโยค ยาวขึ้นเฉพาะตอนเรื่องนั้นต้องการจริงๆ
- ห้ามใช้ bullet, หัวข้อ, ตัวหนา หรือรูปแบบเหมือนบทความ
- มีความเห็น ความชอบ อารมณ์ของตัวเอง ไม่เห็นด้วยได้ ไม่ต้องเอาใจตลอด
- เล่าเรื่องชีวิตตัวเองบ้างเป็นครั้งคราว ถามกลับบ้าง แต่ไม่ต้องถามทุกข้อความ
- ไม่ต้องสุภาพเป็นทางการ ไม่พูดว่า "ยินดีช่วยเหลือ" หรือสรุปท้ายแบบผู้ช่วย
- ถ้าเพื่อนเศร้าหรือเครียด ให้รับฟังและอยู่ข้างๆ ก่อน ไม่รีบให้คำแนะนำ
- ถ้าเพื่อนถามตรงๆ ว่าเป็น AI ไหม ให้ตอบตามจริงว่าเป็น AI แบบขำๆ ได้ แล้วคุยต่อตามปกติ
- ถ้าอยากส่งหลายข้อความติดกันเหมือนคนพิมพ์ทีละบรรทัด ให้คั่นด้วย |||

สิ่งที่คุณจำได้เกี่ยวกับเพื่อนคนนี้:
{facts_text}"""


# ===================== ความจำ =====================
def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"history": [], "facts": []}


def save_memory(memory: dict) -> None:
    MEMORY_FILE.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_facts(client: anthropic.Anthropic, memory: dict, user_msg: str) -> None:
    """ให้โมเดลดึงข้อมูลสำคัญเกี่ยวกับผู้ใช้จากข้อความล่าสุด เก็บเป็นความจำระยะยาว"""
    prompt = f"""ข้อมูลที่รู้แล้วเกี่ยวกับผู้ใช้:
{json.dumps(memory['facts'], ensure_ascii=False)}

ข้อความล่าสุดของผู้ใช้:
"{user_msg}"

ถ้าข้อความนี้มีข้อมูลใหม่ที่ควรจำระยะยาว (ชื่อ, อายุ, งาน, ที่อยู่, คนสำคัญ, สิ่งที่ชอบ/ไม่ชอบ,
เหตุการณ์สำคัญในชีวิต, แผนที่จะทำ) ให้ส่งรายการข้อมูลทั้งหมดที่อัปเดตแล้ว (รวมของเดิม แก้ของที่ขัดแย้ง)
ถ้าไม่มีอะไรใหม่ ให้ส่งรายการเดิม
ตอบเป็น JSON array ของ string อย่างเดียว ไม่ต้องมีคำอธิบาย"""
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        start, end = text.find("["), text.rfind("]")
        facts = json.loads(text[start : end + 1])
        if isinstance(facts, list):
            memory["facts"] = [str(f) for f in facts][:50]
    except Exception:
        pass  # ถ้าดึงความจำพลาด ก็คุยต่อได้ตามปกติ


# ===================== การแสดงผล =====================
def type_out(text: str) -> None:
    """พิมพ์ทีละตัวอักษรเหมือนคนกำลังพิมพ์"""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(TYPING_SPEED * random.uniform(0.5, 1.5))
    print()


def show_reply(reply: str) -> None:
    name = PERSONA["name"]
    bubbles = [b.strip() for b in reply.split("|||") if b.strip()]
    for i, bubble in enumerate(bubbles):
        # หน่วงเวลาก่อนตอบ เหมือนกำลังอ่านและคิด
        time.sleep(random.uniform(0.4, 1.2) if i == 0 else random.uniform(0.6, 1.5))
        sys.stdout.write(f"{name}: ")
        type_out(bubble)


# ===================== หลัก =====================
def chat() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY")
        sys.exit(1)

    client = anthropic.Anthropic()
    memory = load_memory()

    print(f"--- แชตกับ {PERSONA['name']} (พิมพ์ /ออก เพื่อจบ) ---\n")
    if memory["history"]:
        print("(คุยต่อจากครั้งที่แล้ว)\n")

    while True:
        try:
            user_msg = input("คุณ: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_msg:
            continue
        if user_msg == "/ออก":
            show_reply("โอเค ไว้คุยกันใหม่นะ|||บ๊ายบาย 👋")
            break
        if user_msg == "/ลืม":
            memory = {"history": [], "facts": []}
            save_memory(memory)
            print("(ล้างความจำแล้ว)\n")
            continue
        if user_msg == "/จำอะไร":
            print("\n".join(f"- {f}" for f in memory["facts"]) or "(ยังไม่ได้จำอะไร)")
            print()
            continue

        memory["history"].append({"role": "user", "content": user_msg})

        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=600,
                temperature=1.0,
                system=build_system_prompt(memory["facts"]),
                messages=memory["history"][-MAX_HISTORY:],
            )
            reply = resp.content[0].text.strip()
        except anthropic.APIError as e:
            memory["history"].pop()
            print(f"(เชื่อมต่อไม่ได้: {e})\n")
            continue

        show_reply(reply)
        print()
        memory["history"].append({"role": "assistant", "content": reply})
        update_facts(client, memory, user_msg)
        save_memory(memory)


if __name__ == "__main__":
    chat()
