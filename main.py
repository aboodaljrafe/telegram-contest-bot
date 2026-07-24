import os
import re
import sqlite3
import requests
from flask import Flask, request, abort
import telebot
from telebot import types

# قراءة الإعدادات من بيئة السيرفر (Railway)
TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN, threaded=False)

DB_NAME = "contest_master.db"

# ==================== إدارة قاعدة البيانات ====================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone_number TEXT,
                points INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT,
                away_team TEXT,
                match_type TEXT,
                start_time TEXT,
                status TEXT DEFAULT 'ACTIVE',
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                api_match_id INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                user_id INTEGER,
                match_id INTEGER,
                pred_home INTEGER,
                pred_away INTEGER,
                PRIMARY KEY(user_id, match_id)
            )
        ''')
        conn.commit()

init_db()

# ==================== دوال المساعدة ====================
def validate_yemeni_phone(phone):
    # التحقق من أن رقم الهاتف يمني صحيح (9 أرقام تبدأ بـ 70, 71, 73, 77, 78)
    return bool(re.match(r'^7[01378][0-9]{7}$', phone))

def fetch_external_matches():
    """جلب المباريات تلقائياً من الـ API المجاني العالمي"""
    if not FOOTBALL_API_KEY:
        return []
    url = "https://api.football-data.org/v4/matches?status=SCHEDULED,LIVE"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("matches", [])
    except Exception as e:
        print(f"❌ API Error: {e}")
    return []

# ==================== معالجات البوت (Handlers) ====================

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    if not user:
        msg = bot.send_message(
            message.chat.id, 
            "👋 أهلاً بك في منصة المسابقات الرياضية وتوقعات كرة القدم.\n\nيرجى إرسال **اسمك الثلاثي** أولاً للمتابعة:"
        )
        bot.register_next_step_handler(msg, process_name)
    else:
        show_main_menu(message.chat.id, user['full_name'])

def process_name(message):
    name = message.text.strip()
    if len(name.split()) < 3:
        msg = bot.send_message(message.chat.id, "⚠️ الاسم قصير جداً. يرجى إدخال الاسم **الثلاثي** بشكل صحيح:")
        bot.register_next_step_handler(msg, process_name)
        return
    
    msg = bot.send_message(
        message.chat.id, 
        "📱 أرسل الآن رقم هاتفك اليمني (مثال: `771234567`):\n*ملاحظة: يجب أن يكون مكوناً من 9 أرقام ويبدأ بـ 70 أو 71 أو 73 أو 77 أو 78*:"
    )
    bot.register_next_step_handler(msg, lambda m: process_phone(m, name))

def process_phone(message, full_name):
    phone = message.text.strip()
    if not validate_yemeni_phone(phone):
        msg = bot.send_message(
            message.chat.id, 
            "❌ رقم الهاتف غير صحيح أو لا ينتمي لشبكات اليمن المعتمدة.\nأعد إرسال رقم هاتف صحيح:"
        )
        bot.register_next_step_handler(msg, lambda m: process_phone(m, full_name))
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, full_name, phone_number) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, phone)
        )
        conn.commit()
    
    bot.send_message(message.chat.id, "✅ تم تسجيل حسابك وتوثيقه بنجاح في النظام الشامل!")
    show_main_menu(message.chat.id, full_name)

def show_main_menu(chat_id, name):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚽ المباريات المتاحة للتوقعات"), 
        types.KeyboardButton("🏆 لوحة الصدارة والنقاط")
    )
    markup.add(types.KeyboardButton("👤 ملفي الشخصي"))
    if chat_id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ لوحة تحكم المشرف"))
    bot.send_message(chat_id, f"مرحباً بك يا **{name}** في القائمة الرئيسية:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "⚽ المباريات المتاحة للتوقعات")
def list_matches(message):
    with get_db() as conn:
        matches = conn.execute("SELECT * FROM matches WHERE status = 'ACTIVE'").fetchall()
    
    if not matches:
        bot.send_message(message.chat.id, "📭 لا توجد مباريات متاحة للتوقعات في الوقت الحالي. ترقب التحديثات القادمة!")
        return
    
    for m in matches:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"🎯 توقع نتيجة المباراة", callback_data=f"pred_{m['match_id']}"))
        bot.send_message(
            message.chat.id, 
            f"🏆 **مباراة تنافسية**\n⚽ **{m['home_team']}** 🆚 **{m['away_team']}**\n⏰ الموعد: {m['start_time']}", 
            parse_mode="Markdown", 
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("pred_"))
def handle_prediction_callback(call):
    match_id = int(call.data.split("_")[1])
    msg = bot.send_message(
        call.message.chat.id, 
        "✍️ أرسل توقعك للنتيجة النهائية الآن بالأرقام هكذا مثلاً: `2-1`\n*(حيث يسار الفاصل أهداف المستضيف ويمنه الضيف)*:", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, lambda m: save_prediction(m, match_id))

def save_prediction(message, match_id):
    text = message.text.strip()
    if not re.match(r'^\d+-\d+$', text):
        msg = bot.send_message(message.chat.id, "❌ الصيغة خاطئة. أرسل النتيجة بالأرقام مفصولة بشرطة هكذا: `2-1`")
        bot.register_next_step_handler(msg, lambda m: save_prediction(m, match_id))
        return
    
    h_score, a_score = map(int, text.split("-"))
    user_id = message.from_user.id
    
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO predictions (user_id, match_id, pred_home, pred_away) VALUES (?, ?, ?, ?)",
            (user_id, match_id, h_score, a_score)
        )
        conn.commit()
    
    bot.send_message(message.chat.id, f"✅ تم حفظ توقعك بنجاح للنتيجة ({h_score} - {a_score}). بالتوفيق!")

@bot.message_handler(func=lambda message: message.text == "🏆 لوحة الصدارة والنقاط")
def leaderboard(message):
    with get_db() as conn:
        top_users = conn.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT 10").fetchall()
    
    text = "🏆 **لوحة الشرف - أعلى المتسابقين نقاطاً:**\n\n"
    for idx, u in enumerate(top_users, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "▫️"
        text += f"{medal} **{idx}. {u['full_name']}** — {u['points']} نقطة\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👤 ملفي الشخصي")
def profile(message):
    user_id = message.from_user.id
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if user:
        bot.send_message(
            message.chat.id, 
            f"👤 **بيانات حسابك:**\n- الاسم: {user['full_name']}\n- الهاتف: {user['phone_number']}\n- رصيد النقاط: {user['points']} نقطة", 
            parse_mode="Markdown"
        )

# ==================== لوحة تحكم المشرف (Admin Panel) ====================

@bot.message_handler(func=lambda message: message.text == "⚙️ لوحة تحكم المشرف" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("➕ إضافة مباراة يدوياً"), 
        types.KeyboardButton("🔄 جلب المباريات من الشبكة (API)")
    )
    markup.add(types.KeyboardButton("🔙 العودة للقائمة الرئيسية"))
    bot.send_message(message.chat.id, "🛠️ أهلاً بك في لوحة تحكم المشرف المتقدمة:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "➕ إضافة مباراة يدوياً" and message.from_user.id == ADMIN_ID)
def admin_add_match(message):
    msg = bot.send_message(message.chat.id, "أرسل اسم الفريق المستضيف والضيف مفصولين بفاصلة (مثال: `ريال مدريد,برشلونة`):")
    bot.register_next_step_handler(msg, process_admin_teams)

def process_admin_teams(message):
    parts = message.text.split(",")
    if len(parts) != 2:
        msg = bot.send_message(message.chat.id, "❌ صيغة غير صحيحة. أرسل الفريقين هكذا: `ريال مدريد,برشلونة`")
        bot.register_next_step_handler(msg, process_admin_teams)
        return
    home, away = parts[0].strip(), parts[1].strip()
    msg = bot.send_message(message.chat.id, "أرسل موعد انطلاق المباراة (مثال: `اليوم الساعة 10:00 مساءً`):")
    bot.register_next_step_handler(msg, lambda m: save_new_match(m, home, away))

def save_new_match(message, home, away):
    time_str = message.text.strip()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO matches (home_team, away_team, match_type, start_time) VALUES (?, ?, ?, ?)",
            (home, away, "دوري عام", time_str)
        )
        conn.commit()
    bot.send_message(message.chat.id, f"✅ تمت إضافة المباراة بنجاح: {home} 🆚 {away}")

@bot.message_handler(func=lambda message: message.text == "🔄 جلب المباريات من الشبكة (API)" and message.from_user.id == ADMIN_ID)
def admin_fetch_api(message):
    matches = fetch_external_matches()
    if not matches:
        bot.send_message(message.chat.id, "⚠️ عذراً، لم يتم العثور على مباريات أو أن مفتاح الـ `FOOTBALL_API_KEY` غير مفعل في متغيرات السيرفر.")
        return
    count = 0
    with get_db() as conn:
        for m in matches[:5]:
            home = m['homeTeam']['name']
            away = m['awayTeam']['name']
            utc_time = m['utcDate']
            conn.execute(
                "INSERT INTO matches (home_team, away_team, match_type, start_time, api_match_id) VALUES (?, ?, ?, ?, ?)",
                (home, away, "رسمي API", utc_time, m['id'])
            )
            count += 1
        conn.commit()
    bot.send_message(message.chat.id, f"✅ تم جلب وإضافة {count} مباراة جديدة تلقائياً من الإنترنت بنجاح!")

@bot.message_handler(func=lambda message: message.text == "🔙 العودة للقائمة الرئيسية")
def back_home(message):
    user_id = message.from_user.id
    with get_db() as conn:
        user = conn.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,)).fetchone()
    name = user['full_name'] if user else "مشترك"
    show_main_menu(message.chat.id, name)


# ==================== إعدادات مسار الـ Webhook لـ Flask ====================
@app.route('/')
def index():
    return "🚀 Telegram Sports Contest Bot is running globally and securely 24/7!", 200

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
