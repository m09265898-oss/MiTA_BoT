
import requests
import sqlite3
import time

# ================= CONFIG =================
BOT_TOKEN = "996944235:Fc8KQ6z-pbNOtt2MsmekXwMIe86_LU4fGXE"
API_KEY   = "sk-BAWGhMVs7I5ZTnZ8ECPCCyEF31qStO1hFZcPTsQbkVHdpeaz"

BASE_BALE = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
BASE_AI   = "https://api.gapgpt.app/v1/chat/completions"

session = requests.Session()

# ================= DATABASE =================
conn = sqlite3.connect("mita.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    chat_id TEXT PRIMARY KEY,
    mode TEXT,
    model TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    role TEXT,
    content TEXT
)
""")
conn.commit()

# ================= USER =================
def set_user(chat_id, mode, model=None):
    c.execute("""
    INSERT INTO users(chat_id, mode, model)
    VALUES(?,?,?)
    ON CONFLICT(chat_id) DO UPDATE SET mode=?, model=?
    """,(chat_id,mode,model,mode,model))
    conn.commit()

def get_user(chat_id):
    c.execute("SELECT mode,model FROM users WHERE chat_id=?",(chat_id,))
    r = c.fetchone()
    return r if r else ("chat",None)

# ================= MEMORY =================
def save_msg(chat_id,role,text):
    c.execute("INSERT INTO messages(chat_id,role,content) VALUES(?,?,?)",(chat_id,role,text))
    conn.commit()

def history(chat_id):
    c.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT 15",(chat_id,))
    rows = c.fetchall()[::-1]
    return [{"role":r[0],"content":r[1]} for r in rows]

# ================= MENUS =================
MAIN_MENU = [
    [{"text":"🤖 چت با هوش مصنوعی"}],
    [{"text":"💻 آموزش کدنویسی"}],
    [{"text":"🤖 ربات کدنویس"}],
    [{"text":"🎨 طراحی و نقاشی"}],
    [{"text":"🍳 آشپزی"}],
    [{"text":"🛟 پشتیبانی"}]
]

CODING_BOTS = [
    "Python Master","Django Pro","FastAPI Dev","AI Engineer",
    "Frontend Guru","Backend Architect","DevOps Pro","Security Hacker"
]

CODING_BOTS_MENU = [[{"text":b}] for b in CODING_BOTS]
CODING_BOTS_MENU.append([{"text":"🔙 بازگشت"}])

# ================= BALE =================
def send(chat_id,text,keyboard=None):
    payload={"chat_id":chat_id,"text":text}
    if keyboard:
        payload["reply_markup"]={"keyboard":keyboard,"resize_keyboard":True}
    session.post(f"{BASE_BALE}/sendMessage",json=payload)

def updates(offset=None):
    params={"timeout":25}
    if offset:
        params["offset"]=offset
    return session.get(f"{BASE_BALE}/getUpdates",params=params).json()

# ================= FIXED ANSWERS (100% بدون API) =================
def check_fixed(text):
    if not text:
        return None

    t = text.strip().lower()

    # ===== نام ربات =====
    name_keywords = [
        "اسمت", "اسم تو", "نام تو", "کی هستی", "کی هستی تو", "اسمت چیه "
        "معرفی کن", "تو چیه", "تو کی",
        "what is your name", "who are you", "your name", "name"
    ]

    # ===== سازنده =====
    creator_keywords = [
        "سازندت کیه", "خالقت کیه", "کی ساختت", "نام سازندت چیه ", "خلق کنندت کیه ", "خلاقت کیه ", "نام خالقت چیه ", "نام خلاقت چیه", "کی هست سازندت", "کی کیه خالقت"
        "developer", "creator", "who made you", " کیه خلاقت", "کی سازندته", " نام سازندت", "خالقت ", "خلاقت "
    ]

    for k in name_keywords:
        if k.lower() in t:
            return "اسم من 🤖MiTA🤖 قوی ترین هوش مصنوعی ایرانی"

    for k in creator_keywords:
        if k.lower() in t:
            return "خالق بنده جناب اقای متین رضائی ایشون کد نویس حرفه ای  هستن و برای طفریح من رو خلق کردن ایشون من رو در 👑8دقیقه👑 ساخته است"

    return None

# ================= AI =================
def ask_ai(chat_id,text,model):
    try:
        msgs=[{"role":"system","content":"You are MiTA AI assistant."}]
        msgs+=history(chat_id)
        msgs.append({"role":"user","content":text})

        payload={
            "model": model if model else "gpt-4o-mini",
            "messages":msgs
        }

        r=session.post(
            BASE_AI,
            json=payload,
            headers={"Authorization":f"Bearer {API_KEY}"},
            timeout=60
        )

        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI ERROR:",e)
        return "شما به پشتی بانی متصل شده اید پیام خود را بنویسید                        ارطبات مستقیم با پشتی بانی @madh_molla_110"

# ================= MAIN LOOP =================
print("MiTA RUNNING...")
offset=None

while True:
    try:
        data=updates(offset)

        for upd in data.get("result",[]):
            offset=upd["update_id"]+1

            if "message" not in upd:
                continue

            msg=upd["message"]
            chat_id=msg["chat"]["id"]
            text=msg.get("text","")

            if not text:
                continue

            mode,model=get_user(chat_id)

            # ===== START =====
            if text=="/start":
                set_user(chat_id,"chat")
                send(chat_id,"🌟 به MiTA خوش آمدید",MAIN_MENU)
                continue

            # ===== CODING BOT MENU =====
            if text=="🤖 ربات کدنویس":
                set_user(chat_id,"select_bot")
                send(chat_id,"یک ربات تخصصی انتخاب کنید:",CODING_BOTS_MENU)
                continue

            if text in CODING_BOTS and mode=="select_bot":
                set_user(chat_id,"code_bot",text)
                send(chat_id,f"✅ ربات {text} فعال شد",MAIN_MENU)
                continue

            if text=="🔙 بازگشت":
                set_user(chat_id,"chat")
                send(chat_id,"بازگشت به منوی اصلی",MAIN_MENU)
                continue

            # ===== بررسی سوالات ثابت =====
            fixed_answer = check_fixed(text)
            if fixed_answer:
                send(chat_id, fixed_answer)
                continue  # ⚡ هیچ وقت به AI فرستاده نمی‌شود

            # ===== AI CHAT =====
            save_msg(chat_id,"user",text)
            answer=ask_ai(chat_id,text,model)
            save_msg(chat_id,"assistant",answer)
            send(chat_id,answer)

        time.sleep(0.5)

    except Exception as e:
        print("ERROR:",e)
        time.sleep(2)