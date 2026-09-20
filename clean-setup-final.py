#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
السكربت النهائي الشامل:
1. يسحب التوكن من أي نسخة قديمة
2. يوقف كل النسخ الشغالة
3. يمسح المجلدات القديمة (my-bot, mega-bot)
4. ينشئ النموذج النهائي (smart-bot)
5. يضيف كل المميزات
6. يشغّل البوت
"""
import os, sys, re, json, subprocess, shutil, urllib.request
from pathlib import Path

G='\033[92m'; R='\033[91m'; Y='\033[93m'; B='\033[94m'; C='\033[96m'; N='\033[0m'
def s(m): print(f"{B}[STEP]{N} {m}")
def ok(m): print(f"{G}[OK]{N} {m}")
def er(m): print(f"{R}[ERR]{N} {m}")
def inf(m): print(f"{Y}[INFO]{N} {m}")
def warn(m): print(f"{Y}[WARN]{N} {m}")

HOME = Path.home()
SMART_DIR = HOME / "smart-bot"
SMART_FILE = SMART_DIR / "bot.py"
FILES_DIR = SMART_DIR / "files"
DATA_FILE = SMART_DIR / "data.json"

OLD_DIRS = [
    HOME / "my-bot",
    HOME / "mega-bot",
]

# ============================================================
# 1. وقف كل النسخ
# ============================================================
def stop_all_bots():
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  🛑 1. إيقاف كل النسخ{N}")
    print(f"{B}{'='*55}{N}\n")

    stopped = 0
    patterns = ["bot.py", "mega-bot", "my-bot", "smart-bot"]
    for p in patterns:
        r = subprocess.run(f'pgrep -f "{p}"', shell=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if r.stdout.strip():
            subprocess.run(f'pkill -f "{p}"', shell=True)
            ok(f"تم إيقاف: {p}")
            stopped += 1

    if stopped == 0:
        inf("مفيش نسخ شغالة")

    import time
    time.sleep(1)

# ============================================================
# 2. سحب التوكن
# ============================================================
def extract_token():
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  🔑 2. سحب التوكن من النسخ القديمة{N}")
    print(f"{B}{'='*55}{N}\n")

    for d in OLD_DIRS:
        bot_file = d / "bot.py"
        if bot_file.exists():
            try:
                code = bot_file.read_text(encoding='utf-8')
                m = re.search(r'TOKEN\s*=\s*["\']([^"\']+)["\']', code)
                if m:
                    token = m.group(1)
                    if ':' in token:
                        ok(f"لقينا التوكن في: {d.name}")
                        inf(f"التوكن: {token[:15]}...")
                        return token
            except: pass

    # لو مفيش توكن محفوظ، اسأل
    warn("مفيش توكن محفوظ في النسخ القديمة")
    print(f"\n{Y}الصق توكن البوت من BotFather:{N}\n")
    while True:
        token = input(f"{B}التوكن: {N}").strip()
        if not token: er("التوكن مطلوب!"); continue
        if ':' not in token: er("التوكن غلط!"); continue
        return token

# ============================================================
# 3. مسح المجلدات القديمة
# ============================================================
def remove_old_folders():
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  🗑️ 3. مسح المجلدات القديمة{N}")
    print(f"{B}{'='*55}{N}\n")

    for d in OLD_DIRS:
        if d.exists():
            try:
                # نسخة احتياطية قبل المسح
                backup = d.with_name(f"{d.name}.bak")
                if not backup.exists():
                    shutil.copytree(d, backup)
                    ok(f"نسخة احتياطية: {backup.name}")

                shutil.rmtree(d)
                ok(f"تم مسح: {d.name}")
            except Exception as e:
                er(f"فشل مسح {d.name}: {e}")
        else:
            inf(f"مش موجود: {d.name}")

# ============================================================
# 4. إنشاء البوت النهائي
# ============================================================
BOT_CODE = r'''# -*- coding: utf-8 -*-
"""
🤖 البوت الذكي المتكامل — النموذج النهائي
"""
import telebot, os, json, shutil, subprocess, socket, random, threading, time as tm
from pathlib import Path
from datetime import datetime

TOKEN = "%%TOKEN%%"
BOT = telebot.TeleBot(TOKEN)

HOME = Path.home()
DOWNLOAD = HOME / "storage" / "downloads"
BOT_DIR = Path(__file__).parent
FILES_DIR = BOT_DIR / "files"
DATA_FILE = BOT_DIR / "data.json"
FILES_DIR.mkdir(exist_ok=True)

# ============ Helpers ============
def load_data():
    try: return json.loads(DATA_FILE.read_text())
    except: return {"todos": [], "notes": []}

def save_data(d):
    DATA_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2))

def human(n):
    for u in ["B","KB","MB","GB"]:
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

CATS = {
    "Images": [".jpg",".jpeg",".png",".gif",".webp",".bmp",".svg",".heic"],
    "Videos": [".mp4",".mkv",".avi",".mov",".webm",".3gp"],
    "Audio": [".mp3",".wav",".flac",".m4a",".ogg",".aac"],
    "Documents": [".pdf",".doc",".docx",".txt",".xls",".xlsx",".ppt",".pptx"],
    "Archives": [".zip",".rar",".7z",".tar",".gz"],
    "Apps": [".apk",".apks",".xapk"],
    "Code": [".py",".js",".html",".css",".json",".md",".sh"],
}

def get_cat(ext):
    for c, exts in CATS.items():
        if ext.lower() in exts: return c
    return "Others"

# ============ العمليات ============
def do_organize():
    if not DOWNLOAD.exists(): return "❌ مجلد Download مش موجود"
    moved = 0
    for item in DOWNLOAD.iterdir():
        if not item.is_file() or item.name.startswith('.'): continue
        ext = item.suffix
        if not ext: continue
        target = DOWNLOAD / get_cat(ext)
        target.mkdir(exist_ok=True)
        dest = target / item.name
        i = 1
        while dest.exists():
            dest = target / f"{item.stem}_{i}{ext}"; i += 1
        try: shutil.move(str(item), str(dest)); moved += 1
        except: pass
    return f"✅ تم نقل {moved} ملف"

def do_clean():
    if not DOWNLOAD.exists(): return "❌ مجلد Download مش موجود"
    count = 0
    for p in ["*.tmp", "*.log", "*.cache"]:
        for f in DOWNLOAD.rglob(p):
            try: f.unlink(); count += 1
            except: pass
    return f"🧹 تم حذف {count} ملف"

def do_stats():
    if not DOWNLOAD.exists(): return "❌ مجلد Download مش موجود"
    total = 0; size = 0
    for f in DOWNLOAD.rglob("*"):
        if f.is_file(): total += 1; size += f.stat().st_size
    return f"📊 إحصائيات\n\n📁 إجمالي: {total} ملف\n💾 المساحة: {human(size)}"

def do_list():
    if not DOWNLOAD.exists(): return "❌ مجلد Download مش موجود"
    files = [f for f in DOWNLOAD.iterdir() if f.is_file()][:20]
    if not files: return "📭 مفيش ملفات"
    txt = "📂 أول 20 ملف:\n\n"
    for f in files:
        try: sz = human(f.stat().st_size)
        except: sz = "?"
        txt += f"• {f.name} ({sz})\n"
    return txt

def do_battery():
    try:
        out = subprocess.check_output("termux-battery-status", shell=True, text=True, timeout=5)
        d = json.loads(out)
        return f"🔋 البطارية\n\n📊 {d.get('percentage')}%\n⚡ {d.get('status')}\n🌡️ {d.get('temperature')}°C"
    except:
        return "❌ محتاج pkg install termux-api"

def do_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return f"🌐 IP: {ip}"
    except: return "❌ خطأ"

def do_weather(city="Cairo"):
    try:
        import urllib.request
        url = f"https://wttr.in/{city}?format=3"
        with urllib.request.urlopen(url, timeout=10) as r:
            return f"🌤️ الطقس\n\n{r.read().decode('utf-8').strip()}"
    except: return "❌ فشل جلب الطقس"

def do_prayer():
    try:
        import urllib.request, json as j
        url = "http://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = j.loads(r.read().decode())
        t = data['data']['timings']
        names = {'Fajr':'الفجر','Dhuhr':'الظهر','Asr':'العصر','Maghrib':'المغرب','Isha':'العشاء'}
        txt = "🕌 مواقيت الصلاة (القاهرة)\n\n"
        for k in ['Fajr','Dhuhr','Asr','Maghrib','Isha']:
            txt += f"• {names[k]}: {t[k]}\n"
        return txt
    except: return "❌ فشل جلب المواقيت"

def do_currency():
    try:
        import urllib.request, json as j
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = j.loads(r.read().decode())
        egp = data['rates'].get('EGP', 0)
        sar = data['rates'].get('SAR', 0)
        aed = data['rates'].get('AED', 0)
        return f"💵 العملات\n\n🇪🇬 جنيه: {egp:.2f}\n🇸🇦 ريال: {sar:.2f}\n🇦🇪 درهم: {aed:.2f}"
    except: return "❌ فشل جلب الأسعار"

def do_qr(text):
    try:
        import urllib.parse
        encoded = urllib.parse.quote(text)
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"
    except: return None

def schedule_reminder(chat_id, text, seconds):
    def remind():
        tm.sleep(seconds)
        try: BOT.send_message(chat_id, f"🔔 تذكير!\n\n{text}")
        except: pass
    threading.Thread(target=remind, daemon=True).start()

# ============ الأوامر ============
@BOT.message_handler(commands=['start'])
def cmd_start(m):
    BOT.reply_to(m, """🤖 أهلاً بيك في البوت الذكي!

🗣️ اكتب بالعربي:
• نظم الملفات
• نظف الملفات
• إحصائيات
• اعرض الملفات
• البطارية
• الطقس
• مواقيت الصلاة
• العملات
• أضف مهمة مذاكرة
• المهام
• رقم عشوائي

📋 أو بالأوامر:
/stats /list /organize /clean
/weather /prayer /currency
/remind 5m نص
/alarm 07:00 نص
/qr نص

📎 أرسل أي ملف لحفظه""")

@BOT.message_handler(commands=['help', 'commands'])
def cmd_help(m): cmd_start(m)

@BOT.message_handler(commands=['stats'])
def cmd_stats(m): BOT.reply_to(m, do_stats())

@BOT.message_handler(commands=['list'])
def cmd_list(m): BOT.reply_to(m, do_list())

@BOT.message_handler(commands=['organize'])
def cmd_organize(m):
    BOT.reply_to(m, "⏳ جاري التنظيم...")
    BOT.reply_to(m, do_organize())

@BOT.message_handler(commands=['clean'])
def cmd_clean(m):
    BOT.reply_to(m, "⏳ جاري التنظيف...")
    BOT.reply_to(m, do_clean())

@BOT.message_handler(commands=['battery'])
def cmd_battery(m): BOT.reply_to(m, do_battery())

@BOT.message_handler(commands=['ip'])
def cmd_ip(m): BOT.reply_to(m, do_ip())

@BOT.message_handler(commands=['weather'])
def cmd_weather(m):
    city = m.text.replace('/weather','').strip() or "Cairo"
    BOT.reply_to(m, do_weather(city))

@BOT.message_handler(commands=['prayer'])
def cmd_prayer(m): BOT.reply_to(m, do_prayer())

@BOT.message_handler(commands=['currency'])
def cmd_currency(m): BOT.reply_to(m, do_currency())

@BOT.message_handler(commands=['qr'])
def cmd_qr(m):
    text = m.text.replace('/qr','').strip()
    if not text:
        BOT.reply_to(m, "📝 اكتب: /qr [نص]"); return
    url = do_qr(text)
    if url:
        try: BOT.send_photo(m.chat.id, url, caption=f"📱 QR Code\n\n{text[:100]}")
        except: BOT.reply_to(m, "❌ فشل إرسال الصورة")

@BOT.message_handler(commands=['remind'])
def cmd_remind(m):
    parts = m.text.replace('/remind','').strip().split(' ', 1)
    if len(parts) < 2:
        BOT.reply_to(m, "📝 /remind [مدة] [النص]\n\nأمثلة:\n/remind 5m شرب ماء\n/remind 30s تمرين\n/remind 1h اجتماع"); return
    dur, text = parts[0].lower(), parts[1]
    try:
        if dur.endswith('s'): sec = int(dur[:-1])
        elif dur.endswith('m'): sec = int(dur[:-1]) * 60
        elif dur.endswith('h'): sec = int(dur[:-1]) * 3600
        else: sec = int(dur)
        if not (1 <= sec <= 86400): raise ValueError()
        schedule_reminder(m.chat.id, text, sec)
        BOT.reply_to(m, f"✅ تم التذكير\n📝 {text}\n⏰ بعد {dur}")
    except: BOT.reply_to(m, "❌ صيغة غلط\nاستخدم: 5m, 30s, 1h")

@BOT.message_handler(commands=['alarm'])
def cmd_alarm(m):
    parts = m.text.replace('/alarm','').strip().split(' ', 1)
    if len(parts) < 2:
        BOT.reply_to(m, "📝 /alarm [وقت] [النص]\n\nأمثلة:\n/alarm 07:00 صحي\n/alarm 14:30 اجتماع"); return
    t_str, text = parts[0], parts[1]
    try:
        h, mn = map(int, t_str.split(':'))
        now = datetime.now()
        target = now.replace(hour=h, minute=mn, second=0, microsecond=0)
        if target <= now:
            from datetime import timedelta
            target += timedelta(days=1)
        sec = (target - now).total_seconds()
        schedule_reminder(m.chat.id, text, sec)
        BOT.reply_to(m, f"✅ تم الضبط\n📝 {text}\n⏰ {t_str}")
    except: BOT.reply_to(m, "❌ صيغة غلط\nاستخدم: 07:00 أو 14:30")

@BOT.message_handler(commands=['todos'])
def cmd_todos(m):
    d = load_data()
    ts = d.get("todos", [])
    if not ts: BOT.reply_to(m, "📋 مفيش مهام"); return
    txt = "📋 المهام:\n\n"
    for i, t in enumerate(ts, 1):
        txt += f"{'✅' if t.get('done') else '⏳'} {i}. {t['text']}\n"
    BOT.reply_to(m, txt)

@BOT.message_handler(commands=['add'])
def cmd_add(m):
    text = m.text.replace('/add','').strip()
    if not text: BOT.reply_to(m, "📝 /add مهمتك"); return
    d = load_data()
    d["todos"].append({"text": text, "done": False})
    save_data(d)
    BOT.reply_to(m, f"✅ تم إضافة: {text}")

@BOT.message_handler(commands=['done'])
def cmd_done(m):
    txt = m.text.replace('/done','').strip()
    if not txt: BOT.reply_to(m, "📝 /done رقم"); return
    try:
        n = int(txt) - 1
        d = load_data()
        if 0 <= n < len(d["todos"]):
            d["todos"][n]["done"] = True
            save_data(d)
            BOT.reply_to(m, f"✅ تم: {d['todos'][n]['text']}")
        else: BOT.reply_to(m, "❌ رقم غلط")
    except: BOT.reply_to(m, "❌ اكتب رقم")

@BOT.message_handler(commands=['random'])
def cmd_random(m): BOT.reply_to(m, f"🎲 {random.randint(1, 100)}")

# ============ الطلبات العربية ============
@BOT.message_handler(func=lambda m: True)
def smart_handler(m):
    text = (m.text or "").strip()
    low = text.lower()
    if low.startswith('/'): return

    # معلومات
    if any(w in text for w in ["نظم", "رتب", "تنظيم"]):
        BOT.reply_to(m, "⏳ جاري التنظيم...")
        BOT.reply_to(m, do_organize()); return
    if any(w in text for w in ["نظف", "امسح الملفات", "حذف مؤقت"]):
        BOT.reply_to(m, "⏳ جاري التنظيف...")
        BOT.reply_to(m, do_clean()); return
    if any(w in text for w in ["إحصائيات", "احصائيات", "المساحة", "stats"]):
        BOT.reply_to(m, do_stats()); return
    if any(w in text for w in ["الملفات", "اعرض", "list", "ايه عندي"]):
        BOT.reply_to(m, do_list()); return
    if any(w in text for w in ["البطارية", "بطارية", "battery"]):
        BOT.reply_to(m, do_battery()); return
    if any(w in text for w in ["IP", "ip", "الأي بي"]):
        BOT.reply_to(m, do_ip()); return

    # معلومات حية
    if any(w in text for w in ["الطقس", "طقس", "الجو"]):
        BOT.reply_to(m, do_weather()); return
    if any(w in text for w in ["مواقيت الصلاة", "الصلاة", "الصلوات"]):
        BOT.reply_to(m, do_prayer()); return
    if any(w in text for w in ["العملات", "الدولار", "سعر الدولار"]):
        BOT.reply_to(m, do_currency()); return

    # مهام
    if any(w in text for w in ["رقم عشوائي", "random"]):
        BOT.reply_to(m, f"🎲 {random.randint(1, 100)}"); return
    if any(w in text for w in ["المهام", "مهامي"]):
        cmd_todos(m); return
    if "أضف مهمة" in text or "اضف مهمة" in text:
        task = text.replace("أضف مهمة", "").replace("اضف مهمة", "").strip()
        if task:
            d = load_data()
            d["todos"].append({"text": task, "done": False})
            save_data(d)
            BOT.reply_to(m, f"✅ تم إضافة: {task}")
        else: BOT.reply_to(m, "📝 اكتب: أضف مهمة [نص]")
        return

    # تذكيرات
    if any(w in text for w in ["تذكير", "ذكرني"]):
        BOT.reply_to(m, "📝 استخدم:\n/remind 5m نص\n/alarm 07:00 نص"); return

    # رد افتراضي
    BOT.reply_to(m, f"💬 قلت: {text}\n\nجرب:\n• نظم الملفات\n• إحصائيات\n• الطقس\n• مواقيت الصلاة")

# ============ الملفات ============
@BOT.message_handler(content_types=['document','photo','video','audio'])
def handle_file(m):
    try:
        if m.document:
            fi = BOT.get_file(m.document.file_id)
            name = m.document.file_name or "file"
        elif m.photo:
            fi = BOT.get_file(m.photo[-1].file_id)
            name = f"photo_{m.message_id}.jpg"
        elif m.video:
            fi = BOT.get_file(m.video.file_id)
            name = f"video_{m.message_id}.mp4"
        else:
            fi = BOT.get_file(m.audio.file_id)
            name = f"audio_{m.message_id}.mp3"
        path = FILES_DIR / name
        path.write_bytes(BOT.download_file(fi.file_path))
        BOT.reply_to(m, f"✅ تم حفظ: {name}\n📁 {FILES_DIR}")
    except Exception as e:
        BOT.reply_to(m, f"❌ {e}")

print("=" * 55)
print("🤖 البوت الذكي المتكامل شغال")
print("=" * 55)
print("🗣️ يفهم العربي: نظم، إحصائيات، الطقس، الصلاة...")
print("CTRL+C للإيقاف")
BOT.infinity_polling()
'''

def create_final_bot(token):
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  📝 4. إنشاء البوت النهائي{N}")
    print(f"{B}{'='*55}{N}\n")

    SMART_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text('{"todos": [], "notes": []}')
    ok("المجلدات جاهزة")

    code = BOT_CODE.replace("%%TOKEN%%", token)
    SMART_FILE.write_text(code, encoding='utf-8')
    ok(f"bot.py ({len(code):,} حرف)")

    (SMART_DIR / "README.md").write_text(
        "# 🤖 البوت الذكي المتكامل\n\n"
        "بوت تيليجرام بكل المميزات.\n\n"
        "## التشغيل\n```bash\ncd ~/smart-bot\npython bot.py\n```\n",
        encoding='utf-8'
    )
    ok("README.md")

def run_bot():
    print(f"\n{G}{'='*55}{N}")
    print(f"{G}  🚀 5. تشغيل البوت{N}")
    print(f"{G}{'='*55}{N}\n")
    os.chdir(SMART_DIR)
    os.system(f'python {SMART_FILE}')

def main():
    print(f"\n{G}{'='*55}{N}")
    print(f"{G}  🌟 السكربت النهائي الشامل{N}")
    print(f"{G}{'='*55}{N}\n")
    inf("سحب التوكن + مسح القديم + إعادة البناء")

    # 1. إيقاف
    stop_all_bots()

    # 2. سحب التوكن
    token = extract_token()

    # 3. مسح القديم
    remove_old_folders()

    # 4. إنشاء
    create_final_bot(token)

    # 5. تشغيل
    run_bot()

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(f"\n{R}اتوقف{N}")
