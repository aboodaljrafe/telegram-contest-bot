import os
import re
import sqlite3
import telebot
import copy
import threading
from flask import Flask
from datetime import datetime, timedelta
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# 🌐 إعداد خادم Flask لتأمين استمرارية السيرفر
# ==========================================
app = Flask(__name__)

@app.route('/')
def index():
    return "البوت يعمل بنجاح 24/7 دون انقطاع!", 200

# ==========================================
# 🔐 الإعدادات والتأمينات الأمنية
# ==========================================
TOKEN = os.getenv("BOT_TOKEN", "8673575186:AAG2YvsMOxJu2Iw7Rr6oaiMeUdQVGMZuTHQ")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7394452907))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Aood71arf")

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 🛡️ دالة تأمين النصوص ضد أخطاء الماركداون
# ==========================================
def escape_markdown(text):
    """تنظيف النصوص الديناميكية لمنع انهيار واجهة تيليجرام بسبب الرموز الخاصة"""
    if not text:
        return ""
    for char in ['*', '_', '`', '[']:
        text = str(text).replace(char, f'\\{char}')
    return text

# ==========================================
# 🗄️ بنك البيانات الكامل للمسابقات (Baseline Static)
# ==========================================
DATA_BANK = {
    "الدوريات": {
        "الدوري الإسباني": ["برشلونة", "ريال مدريد", "فياريال", "أتلتيكو مدريد", "ريال بيتيس", "سيلتا فيغو", "خيتافي", "رايو فايكانو", "فالنسيا", "ريال سوسيداد", "إسبانيول", "أتلتيك بلباو", "إشبيلية", "ديبورتيفو ألافيس", "إلتشي", "ليفانتي", "أوساسونا", "راسينغ سانتاندير", "ديبورتيفو لاكورونيا", "ألميريا", "مالقا", "لاس بالماس", "كاستييون"],
        "الدوري الإنجليزي": ["أرسنال", "مانشستر سيتي", "مانشستر يونايتد", "أستون فيلا", "ليفربول", "بورنموث", "سندرلاند", "برايتون", "تشيلسي", "كريستال بالاس", "إيفرتون", "فولهام", "نيوكاسل يونايتد", "نوتينغهام فورست", "توتنهام هوتسبير", "برينتفورد", "ليدز يونايتد", "كوفنتري سيتي", "إبسويتش تاون", "هال سيتي"],
        "الدوري الإيطالي": ["إنتر ميلان", "نابولي", "روما", "كومو", "أتالانتا", "ميلان", "يوفنتوس", "بولونيا", "كالياري", "لاتسيو", "ليتشي", "فيورنتينا", "فروسينوني", "مونزا", "جنوى", "بارما", "ساسوولو", "تورينو", "أودينيزي", "فينيسيا"],
        "الدوري الألماني": ["بايرن ميونخ", "بوروسيا دورتموند", "لايبزيغ", "شتوتغارت", "باير ليفركوزن", "هوفنهايم", "فرايبورغ", "آينتراخت فرانكفورت", "أوغسبورغ", "ماينتس 05", "يونيون برلين", "بوروسيا مونشنغلادباخ", "هامبورغ", "فيردر بريمن", "كولن", "شالكه 04", "بادربورن", "إلفيرسبيرغ"],
        "الدوري الفرنسي": ["باريس سان جيرمان", "لانس", "ليل", "أولمبيك ليون", "أولمبيك مارسيليا", "رين", "موناكو", "ستراسبورغ", "نيس", "بريست", "تولوز", "لو هافر", "أوكسير", "أنجيه", "لوريان", "تروا", "لومان", "باريس إف سي"],
        "الدوري السعودي": ["النصر", "الهلال", "الأهلي", "القادسية", "الاتحاد", "التعاون", "الاتفاق", "نيوم", "الحزم", "الفيحاء", "الفتح", "الخليج", "الشباب", "الخلود", "الرياض", "أبها", "الفيصلي", "الدرعية"],
        "أندية متفرقة أخرى": ["هولندا: أيندهوفن", "هولندا: فينورد", "هولندا: إيه زد ألكمار", "البرتغال: بورتو", "البرتغال: سبورتينغ لشبونة", "البرتغال: تورينسي", "بلجيكا: كلوب بروج", "التشيك: سلافيا براغ", "تركيا: غلطة سراي", "أوكرانيا: شاختار دونيتسك"]
    },
    "القارات": {
        "آسيا (قسم غربي) 🧭": ["السعودية🇸🇦", "الإمارات العربية المتحدة🇦🇪", "قطر🇶🇦", "البحرين🇧🇭", "عمان🇴🇲", "الكويت🇰🇼", "العراق🇮🇶", "الأردن🇯🇴", "فلسطين🇵🇸", "لبنان🇱🇧", "سوريا🇸🇾", "اليمن🇾🇪", "إيران🇮🇷", "أوزبكستان🇺🇿", "تركمانستان🇹🇲", "طاجيكستان🇹🇯", "قيرغيزستان🇰🇬", "أفغانستان🇦🇫", "الهند🇮🇳", "باكستان🇵🇰", "بنغلاديش🇧🇩", "نيبال🇳🇵", "بوتان🇧🇹", "سريلانكا🇱🇰", "جزر المالديف🇲🇻"],
        "آسيا (قسم شرقي) 🌏": ["اليابان🇯🇵", "كوريا الجنوبية🇰🇷", "الصين🇨🇳", "أستراليا🇦🇺", "كوريا الشمالية🇰🇵", "تايبيه الصينية🇹🇼", "هونغ كونغ 🇭🇰", "ماكاو🇲🇴", "منغوليا🇲🇳", "فيتنام🇻🇳", "تايلاند🇹🇭", "ماليزيا🇲🇾", "إندونيسيا🇮🇩", "الفلبين🇵🇭", "سنغافورة🇸🇬", "ميانمار🇲🇪", "كمبوديا🇰🇭", "لاوس🇱🇦", "بروناي🇧🇳", "تيمور الشرقية🇹🇱", "غوام🇬🇺", "جزر ماريانا الشمالية🇲🇵"],
        "أوروبا 🇪🇺": ["ألبانيا🇦🇱", "أندورا🇦🇩", "أرمينيا🇦🇲", "النمسا🇦🇹", "أذربيجان🇦🇿", "بيلاروسيا🇧🇾", "بلجيكا🇧🇪", "البوسنة والهرسك🇧🇦", "بلغاريا🇧🇬", "كرواتيا🇭🇷", "قبرص🇨🇾", "جمهورية التشيك🇨🇿", "الدنمارك🇩🇰", "إنجلترا🇫🇴", "إستونيا🇪🇪", "جزر فارو🇫🇴", "فنلندا🇫🇮", "فرنسا🇫🇷", "جورجيا🇬🇪", "ألمانيا🇩🇪", "جبل طارق🇬🇮", "اليونان🇬🇷", "المجر🇭🇺", "آيسلندا🇮🇸", "إسرائيل🇮🇱", "إيطاليا🇮🇹", "كازاخستان🇰🇿", "كوسوفو🇽🇰", "لاتفيا🇱🇻", "ليختنشتاين🇱🇮", "ليتوانيا🇱🇹", "لوكسمبورغ🇱🇺", "مالطا🇲🇹", "مولدوفا🇲🇩", "الجبل الأسود🇲🇪", "هولندا🇳🇱", "مقدونيا الشمالية🇲🇰", "أيرلندا الشمالية🇬بان", "النرويج🇳🇴", "بولندا🇵🇱", "البرتغال🇵🇹", "جمهورية أيرلندا🇮🇪", "رومانيا🇷🇴", "روسيا🇷🇺", "سان مارينو🇸🇲", "اسكتلندا 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "صربيا🇷🇸", "سلوفاكيا🇸🇰", "سلوفينيا🇸🇮", "إسبانيا🇪🇸", "السويد🇸🇪", "سويسرا🇨🇭", "تركيا🇹🇷", "أوكرانيا🇺🇦", "ويلز 🏴󠁧󠁢󠁷󠁬󠁳󠁿"],
        "أمريكا الجنوبية 🇦🇷": ["الأرجنتين🇦🇷", "بوليفيا🇧🇴", "البرازيل🇧🇷", "تشيلي🇨🇱", "كولومبيا🇨🇴", "الإكوادور🇪🇨", "باراغواي🇵🇾", "بيرو🇵🇪", "أوروغواي🇺🇾", "فنزويلا🇻🇪"],
        "أفريقيا (قسم شمالي) 🦅": ["الجزائر🇩🇿", "مصر🇪🇬", "ليبيا🇱🇾", "المغرب🇲🇦", "موريتانيا🇲🇷", "تشاد🇹🇩", "مالي🇲🇱", "النيجر🇿🇼", "بوركينا فاسو🇧🇫"],
        "أفريقيا (قسم جنوبي) 🦁": ["أنغولا🇦🇴", "بنين🇧じん", "بوتسوانا🇧🇼", "بوروندي🇧🇮", "الرأس الأخضر🇨вих", "الكاميرون🇨🇲", "جمهورية أفريقيا الوسطى🇨🇫", "جزر القمر🇰🇲", "الكونغو🇨🇬", "جمهورية الكونغو الديمقراطية🇨🇩", "غينيا الاستوائية🇬🇶", "إريتريا🇪🇷", "إسواتيني🇸🇿", "إثيوبيا🇪🇹", "الغابون🇬🇦", "غامبيا🇬🇲", "غانا🇬🇭", "غينيا🇬🇳", "غينيا بيساو🇬🇼", "ساحل العاج🇨🇮", "كينيا🇰🇪", "ليسوتو🇱🇸", "ليبيريا🇱🇷", "مدغشقر🇲🇬", "مالاوي🇲🇼", "موريشيوس🇲🇺", "موزمبيق🇲🇿", "ناميبيا🇳🇦"],
        "أوقيانوسيا 🇳🇿": ["نيوزيلندا🇳🇿", "جزر سليمان🇸🇧", "تاهيتي🇵🇫", "فانواتو🇻🇺", "كاليدونيا الجديدة🇳🇨", "بابوا غينيا الجديدة🇵🇬", "فيجي 🇫يج", "ساموا🇼🇸", "ساموا الأمريكية🇦🇸", "تونغا🇹🇴", "جزر كوك🇨🇰"],
        "أمريكا الشمالية 🇺🇸": ["الولايات المتحدة🇺🇸", "المكسيك🇲🇽", "كندا🇨🇦", "بنما🇵🇦", "كوستاريكا🇨🇷", "هندوراس🇭🇳", "جامايكا🇯🇲", "السلفادور🇸🇻", "غواتيمالا🇬🇹", "هايتي🇭🇹", "كوراساو🇨🇼", "ترينيداد وتوباغو🇹🇹", "نيكاراغوا🇳🇮", "سورينام🇸🇷"]
    }
}

STATIC_DATA_BANK = copy.deepcopy(DATA_BANK)

ADMIN_SESSION = {}
USER_SESSION = {}

def is_admin(user):
    return user.id == ADMIN_ID or user.username == ADMIN_USERNAME

# ==========================================
# ⚡ إدارة قاعدة البيانات بأعلى كفاءة وتأمين Concurrency
# ==========================================
def get_db():
    conn = sqlite3.connect('contest_master.db', timeout=15)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY, 
                        username TEXT, 
                        full_name TEXT, 
                        phone_number TEXT,
                        points INTEGER DEFAULT 0,
                        banned INTEGER DEFAULT 0)''')
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
                        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT, sub_category TEXT,
                        home_team TEXT, away_team TEXT,
                        match_type TEXT, start_time TEXT, status TEXT DEFAULT 'ACTIVE',
                        home_score INTEGER, away_score INTEGER,
                        pen_home_score INTEGER DEFAULT 0, pen_away_score INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
                        user_id INTEGER, match_id INTEGER,
                        home_pred INTEGER, away_pred INTEGER,
                        pen_home_pred INTEGER DEFAULT 0, pen_away_pred INTEGER DEFAULT 0,
                        PRIMARY KEY(user_id, match_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS dynamic_teams (
                        category TEXT, tournament_name TEXT, team_name TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS tournament_mods (
                        category TEXT, old_name TEXT, new_name TEXT, status TEXT DEFAULT 'ACTIVE')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS team_mods (
                        category TEXT, tournament TEXT, old_name TEXT, new_name TEXT, status TEXT DEFAULT 'ACTIVE')''')
                        
    conn.commit()
    conn.close()

def load_dynamic_tournaments():
    global DATA_BANK
    DATA_BANK = copy.deepcopy(STATIC_DATA_BANK)
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT category, old_name, new_name, status FROM tournament_mods")
        for cat, old_name, new_name, status in cursor.fetchall():
            if cat in DATA_BANK:
                if status == 'DELETED':
                    DATA_BANK[cat].pop(old_name, None)
                elif status == 'ACTIVE' and old_name in DATA_BANK[cat]:
                    DATA_BANK[cat][new_name] = DATA_BANK[cat].pop(old_name)

        cursor.execute("SELECT category, tournament, old_name, new_name, status FROM team_mods")
        for cat, tour, old_name, new_name, status in cursor.fetchall():
            if cat in DATA_BANK and tour in DATA_BANK[cat]:
                if status == 'DELETED':
                    if old_name in DATA_BANK[cat][tour]:
                        DATA_BANK[cat][tour].remove(old_name)
                elif status == 'ACTIVE':
                    if old_name in DATA_BANK[cat][tour]:
                        idx = DATA_BANK[cat][tour].index(old_name)
                        DATA_BANK[cat][tour][idx] = new_name

        cursor.execute("SELECT category, tournament_name, team_name FROM dynamic_teams")
        for cat, tour_name, team_name in cursor.fetchall():
            if cat in DATA_BANK:
                if tour_name not in DATA_BANK[cat]:
                    DATA_BANK[cat][tour_name] = []
                if team_name not in DATA_BANK[cat][tour_name]:
                    DATA_BANK[cat][tour_name].append(team_name)
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

init_db()
load_dynamic_tournaments()

# ==========================================
# 🔐 نظام التسجيل والتحقق الصارم
# ==========================================
def check_registration(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, phone_number, banned FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[2] == 1:
        bot.send_message(message.chat.id, "🚫 **عذراً، لقد تم حظر حسابك من المشاركة في هذه المنافسة من قبل المشرف!**")
        return False
    
    if user and user[0] and user[1]:
        return True
    
    msg = bot.send_message(message.chat.id, "⚠️ **عذراً، هذا البوت خاص بالمنافسة المقفلة.**\nالرجاء إرسال اسمك الثلاثي كاملاً لبدء حجز حسابك وسجلك الرقمي:")
    bot.register_next_step_handler(msg, register_user_name)
    return False

def register_user_name(message):
    name_text = message.text.strip() if message.text else ""
    if len(name_text.split()) < 3:
        msg = bot.send_message(message.chat.id, "❌ يجب إرسال الاسم **ثلاثياً** بشكل صحيح لتأمين الحجز، حاول مجدداً:")
        bot.register_next_step_handler(msg, register_user_name)
        return
    
    USER_SESSION[message.from_user.id] = {"reg_name": name_text}
    msg = bot.send_message(message.chat.id, f"🎯 أهلاً بك *{escape_markdown(name_text)}*.\nالآن يرجى إرسال **رقم هاتفك المكون من 9 أرقام فقط (شبكات يمنية)** ليكون معرّفك:")
    bot.register_next_step_handler(msg, register_user_phone)

def register_user_phone(message):
    phone_text = message.text.strip() if message.text else ""
    if not re.match(r'^7[01378]\d{7}$', phone_text):
        msg = bot.send_message(message.chat.id, "❌ خطأ في تنسيق الرقم! يرجى إرسال رقم هاتف يمني صحيح مكون من **9 أرقام ويبدأ بـ 77، 73، 71، 70، أو 78**:")
        bot.register_next_step_handler(msg, register_user_phone)
        return
    
    uid = message.from_user.id
    full_name = USER_SESSION.get(uid, {}).get("reg_name", "مستخدم جديد")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, username, full_name, phone_number, points) VALUES (?, ?, ?, ?, 0)",
                   (uid, message.from_user.username, full_name, phone_text))
    conn.commit()
    conn.close()
    
    USER_SESSION.pop(uid, None)
        
    bot.send_message(message.chat.id, f"✅ تم تسجيلك بنجاح!\n📝 الاسم الثلاثي: *{escape_markdown(full_name)}*\n🆔 معرّفك المحجوز: `{phone_text}`")
    show_main_menu(message)

def show_main_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🗳️ التوقعات المتاحة"), KeyboardButton("📊 جدول الترتيب العام"))
    markup.add(KeyboardButton("🏆 مبارياتي الرابحة"), KeyboardButton("ℹ️ معلومات حسابي"))
    
    if is_admin(message.from_user):
        markup.add(KeyboardButton("⚙️ لوحة تحكم المشرف"))
        
    bot.send_message(message.chat.id, "📊 أهلاً بك في الواجهة الرئيسية للمسابقة. يرجى اختيار الإجراء من الأسفل:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if check_registration(message):
        show_main_menu(message)

@bot.message_handler(func=lambda msg: True)
def handle_text_buttons(message):
    if not check_registration(message):
        return
        
    if message.text == "🗳️ التوقعات المتاحة":
        show_available_matches(message)
    elif message.text == "📊 جدول الترتيب العام":
        show_standings_page(message.chat.id, page=0)
    elif message.text == "🏆 مبارياتي الرابحة":
        show_winning_matches(message)
    elif message.text == "ℹ️ معلومات حسابي":
        show_my_info(message)
    elif message.text == "⚙️ لوحة تحكم المشرف" and is_admin(message.from_user):
        show_admin_panel(message)

# ==========================================
# 🗳️ محرك التوقعات وإدارة الواجهات الذكية
# ==========================================
def show_available_matches(message):
    load_dynamic_tournaments()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, category, sub_category, home_team, away_team, start_time, match_type FROM matches WHERE status='ACTIVE'")
    matches = cursor.fetchall()
    
    markup = InlineKeyboardMarkup(row_width=1)
    now = datetime.now()
    valid_matches_count = 0
    
    for m in matches:
        match_id, cat, sub_cat, home, away, s_time, m_type = m
        try:
            match_dt = datetime.strptime(s_time, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
            
        if now < match_dt:
            valid_matches_count += 1
            cursor.execute("SELECT home_pred, away_pred FROM predictions WHERE user_id=? AND match_id=?", (message.from_user.id, match_id))
            pred = cursor.fetchone()
            
            if pred:
                btn_text = f"✏️ تعديل: {home} [{pred[0]}-{pred[1]}] {away}"
            else:
                btn_text = f"⚽ توقع: {home} × {away}"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"usr_pred_{match_id}"))
            
    conn.close()
    
    if valid_matches_count == 0:
        bot.send_message(message.chat.id, "📭 لا توجد مباريات نشطة أو متاحة للتوقع حالياً.")
        return
        
    bot.send_message(message.chat.id, "🏟️ المباريات المتاحة للتوقع (التعديل متاح حتى موعد انطلاق اللقاء الرسمي):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("usr_pred_"))
def user_prediction_interface(call):
    match_id = int(call.data.split("_")[2])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team, match_type, start_time FROM matches WHERE match_id=?", (match_id,))
    match = cursor.fetchone()
    
    if not match:
        bot.answer_callback_query(call.id, "المباراة غير موجودة.")
        conn.close()
        return
        
    home, away, m_type, s_time = match
    if datetime.now() > datetime.strptime(s_time, "%Y-%m-%d %H:%M"):
        bot.answer_callback_query(call.id, "🔒 عذراً، بدأت المباراة وتم إغلاق استقبال التوقعات تلقائياً!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        conn.close()
        return

    cursor.execute("SELECT home_pred, away_pred, pen_home_pred, pen_away_pred FROM predictions WHERE user_id=? AND match_id=?", (call.from_user.id, match_id))
    current_pred = cursor.fetchone()
    conn.close()
    
    hp, ap, php, pap = current_pred if current_pred else (0, 0, 0, 0)
        
    USER_SESSION[call.from_user.id] = {"match_id": match_id, "hp": hp, "ap": ap, "php": php, "pap": pap, "type": m_type}
    render_prediction_keyboard(call.message, call.from_user.id, home, away)

def render_prediction_keyboard(message, user_id, home, away):
    if user_id not in USER_SESSION:
        return
    data = USER_SESSION[user_id]
    markup = InlineKeyboardMarkup()
    
    markup.row(
        InlineKeyboardButton(f"➕ {home}", callback_data="u_inc_h"),
        InlineKeyboardButton(f"⚽ {data['hp']} - {data['ap']} ⚽", callback_data="none"),
        InlineKeyboardButton(f"➕ {away}", callback_data="u_inc_a")
    )
    markup.row(
        InlineKeyboardButton(f"➖ {home}", callback_data="u_dec_h"),
        InlineKeyboardButton("🔄 ريستارت", callback_data="u_reset"),
        InlineKeyboardButton(f"➖ {away}", callback_data="u_dec_a")
    )
    
    if data['type'] == "خروج مغلوب (ترجيح)" and data['hp'] == data['ap']:
        markup.row(InlineKeyboardButton("🌟 توقع ركلات الترجيح 🌟", callback_data="none"))
        markup.row(
            InlineKeyboardButton(f"➕ ركلات {home}", callback_data="u_inc_ph"),
            InlineKeyboardButton(f"🥅 {data['php']} - {data['pap']} 🥅", callback_data="none"),
            InlineKeyboardButton(f"➕ ركلات {away}", callback_data="u_inc_pa")
        )
        markup.row(
            InlineKeyboardButton(f"➖ {home}", callback_data="u_dec_ph"),
            InlineKeyboardButton(" ", callback_data="none"),
            InlineKeyboardButton(f"➖ {away}", callback_data="u_dec_pa")
        )
        
    markup.row(InlineKeyboardButton("💾 حفظ وتثبيت التوقع الآن ✅", callback_data="u_save_pred"))
    
    try:
        bot.edit_message_text(f"🎯 **تحديد توقع مباراة:**\n🏟️ {home} × {away}\nقم باستخدام الأزرار لضبط النتيجة المتوقعة بالكامل:", 
                              message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("u_"))
def handle_user_adjustments(call):
    user_id = call.from_user.id
    if user_id not in USER_SESSION:
        bot.answer_callback_query(call.id, "انتهت الجلسة، الرجاء إعادة الضغط من زر التوقعات المتاحة.")
        return
        
    action = call.data
    data = USER_SESSION[user_id]
    
    if action == "u_inc_h": data['hp'] += 1
    elif action == "u_dec_h" and data['hp'] > 0: data['hp'] -= 1
    elif action == "u_inc_a": data['ap'] += 1
    elif action == "u_dec_a" and data['ap'] > 0: data['ap'] -= 1
    elif action == "u_inc_ph": data['php'] += 1
    elif action == "u_dec_ph" and data['php'] > 0: data['php'] -= 1
    elif action == "u_inc_pa": data['pap'] += 1
    elif action == "u_dec_pa" and data['pap'] > 0: data['pap'] -= 1
    elif action == "u_reset": data['hp'], data['ap'], data['php'], data['pap'] = 0, 0, 0, 0
    
    elif action == "u_save_pred":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT start_time FROM matches WHERE match_id=?", (data['match_id'],))
        db_match = cursor.fetchone()
        
        if not db_match or datetime.now() > datetime.strptime(db_match[0], "%Y-%m-%d %H:%M"):
            bot.answer_callback_query(call.id, "🔒 عذراً، انتهت المهلة المحددة! انطلقت المباراة وتم قفل استقبال البيانات.", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            conn.close()
            USER_SESSION.pop(user_id, None)
            return

        if data['hp'] != data['ap']:
            data['php'], data['pap'] = 0, 0

        cursor.execute("INSERT OR REPLACE INTO predictions (user_id, match_id, home_pred, away_pred, pen_home_pred, pen_away_pred) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, data['match_id'], data['hp'], data['ap'], data['php'], data['pap']))
        conn.commit()
        conn.close()
        bot.edit_message_text("✅ **تم حفظ وتثبيت توقعك بنجاح!**\nتم قيد النتيجة في سجلاتك الرقمية وسيتم احتساب النقاط عند انتهاء اللقاء.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        USER_SESSION.pop(user_id, None)
        return
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team FROM matches WHERE match_id=?", (data['match_id'],))
    home, away = cursor.fetchone()
    conn.close()
    render_prediction_keyboard(call.message, user_id, home, away)

# ==========================================
# 📊 نظام الصفحات لجدول الترتيب (Pagination)
# ==========================================
def show_standings_page(chat_id, page=0, message_id=None):
    items_per_page = 10
    offset = page * items_per_page
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT ? OFFSET ?", (items_per_page, offset))
    players = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    
    if not players and page == 0:
        bot.send_message(chat_id, "📊 جدول الترتيب خالي حالياً.")
        return
        
    text = f"🏆 **جدول الترتيب العام للمنافسين (الصفحة {page + 1}):**\n\n"
    for idx, player in enumerate(players, 1):
        global_rank = offset + idx
        medal = "🥇" if global_rank == 1 else "🥈" if global_rank == 2 else "🥉" if global_rank == 3 else f"🏅 {global_rank}."
        safe_name = escape_markdown(player[0])
        text += f"{medal} {safe_name} ➖ `{player[1]}` نقطة\n"
        
    markup = InlineKeyboardMarkup()
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"std_page_{page - 1}"))
    if offset + items_per_page < total_users:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"std_page_{page + 1}"))
        
    if nav_buttons:
        markup.row(*nav_buttons)
        
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException:
            pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("std_page_"))
def handle_standings_pagination(call):
    page = int(call.data.split("_")[2])
    show_standings_page(call.message.chat.id, page=page, message_id=call.message.message_id)

# ==========================================
# 🏆 عرض تفاصيل ومباريات الحساب
# ==========================================
def show_winning_matches(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.home_team, m.away_team, m.match_type, 
               m.home_score, m.away_score, m.pen_home_score, m.pen_away_score,
               p.home_pred, p.away_pred, p.pen_home_pred, p.pen_away_pred
        FROM matches m
        JOIN predictions p ON m.match_id = p.match_id
        WHERE m.status = 'FINISHED' AND p.user_id = ?
    ''', (message.from_user.id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(message.chat.id, "🏆 لا توجد مباريات منتهية قمت بتوقعها حالياً في سجلاتك.")
        return
        
    winning_text = "🏆 **سجل النقاط والمباريات المفرزة:**\n\n"
    has_winning = False
    
    for row in rows:
        home, away, m_type, r_h, r_a, r_ph, r_pa, u_h, u_a, u_ph, u_pa = row
        real_outcome = "HOME" if r_h > r_a else "AWAY" if r_a > r_h else "DRAW"
        u_outcome = "HOME" if u_h > u_a else "AWAY" if u_a > u_h else "DRAW"
        
        pts = 0
        exact_match_score = False
        
        if u_outcome == real_outcome:
            pts += 5
            if u_h == r_h and u_a == r_a:
                pts += 15
                exact_match_score = True
                
        if m_type == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
            real_pen_winner = "HOME" if r_ph > r_pa else "AWAY"
            u_pen_winner = "HOME" if u_ph > u_pa else "AWAY"
            exact_pen_score = False
            if u_pen_winner == real_pen_winner:
                pts += 10
                if u_ph == r_ph and u_pa == r_pa:
                    pts += 15
                    exact_pen_score = True
            if exact_match_score and exact_pen_score:
                pts += 30
                
        if pts > 0:
            has_winning = True
            score_str = f"[{r_h} - {r_a}]"
            pred_str = f"[{u_h} - {u_a}]"
            if m_type == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
                score_str += f" (ركلات {r_ph}-{r_pa})"
                pred_str += f" (توقعك {u_ph}-{u_pa})"
                
            winning_text += f"⚽ **{home} × {away}**\n🏁 النتيجة: `{score_str}`\n🗳️ توقعك: `{pred_str}`\n💰 نقاطك: *+{pts}* ن\n───────────────────\n"
                            
    if not has_winning:
        bot.send_message(message.chat.id, "ℹ️ لم يتم العثور على أي نقاط رابحة في المباريات التي توقعتها حتى الآن.")
    else:
        bot.send_message(message.chat.id, winning_text, parse_mode="Markdown")

def show_my_info(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, phone_number, points FROM users WHERE user_id=?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()
    
    full_name, phone_number, points = user if user else (message.from_user.first_name, "غير مسجل", 0)
    
    text = f"👤 **معلومات بطاقتك والمحرّف الرقمي الخاص بك:**\n\n" \
           f"📝 الاسم الثلاثي: *{escape_markdown(full_name)}*\n" \
           f"🆔 الهوية الرقمية (الهاتف): `{phone_number}`\n" \
           f"💰 رصيدك الإجمالي: *{points}* نقطة"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ==========================================
# ⚙️ لوحة الإدارة المتكاملة (Admin Panel)
# ==========================================
def show_admin_panel(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة وجدولة مباراة جديدة", callback_data="adm_add_match"),
        InlineKeyboardButton("🏆 إضافة بطولة جديدة ✨", callback_data="adm_add_tournament"),
        InlineKeyboardButton("🛠️ إدارة وحذف وتعديل البطولات والفرق", callback_data="adm_manage_db"),
        InlineKeyboardButton("🏁 رصد نتيجة رسمية وحساب النقاط", callback_data="adm_settle_list"),
        InlineKeyboardButton("🗑️ حذف مباراة مرسلة بالكامل", callback_data="adm_delete_list"),
        InlineKeyboardButton("👥 إدارة المنافسين والتحكم بالحسابات", callback_data="adm_manage_users"),
        InlineKeyboardButton("📢 إذاعة رسالة للمشتركين (Broadcast)", callback_data="adm_broadcast"),
        InlineKeyboardButton("💾 تحميل نسخة احتياطية للبيانات (Backup)", callback_data="adm_backup")
    )
    bot.send_message(message.chat.id, "⚙️ **لوحة التحكم الشاملة لمدير المنظومة:**", reply_markup=markup)

def render_admin_panel_view(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة وجدولة مباراة جديدة", callback_data="adm_add_match"),
        InlineKeyboardButton("🏆 إضافة بطولة جديدة ✨", callback_data="adm_add_tournament"),
        InlineKeyboardButton("🛠️ إدارة وحذف وتعديل البطولات والفرق", callback_data="adm_manage_db"),
        InlineKeyboardButton("🏁 رصد نتيجة رسمية وحساب النقاط", callback_data="adm_settle_list"),
        InlineKeyboardButton("🗑️ حذف مباراة مرسلة بالكامل", callback_data="adm_delete_list"),
        InlineKeyboardButton("👥 إدارة المنافسين والتحكم بالحسابات", callback_data="adm_manage_users"),
        InlineKeyboardButton("📢 إذاعة رسالة للمشتركين (Broadcast)", callback_data="adm_broadcast"),
        InlineKeyboardButton("💾 تحميل نسخة احتياطية للبيانات (Backup)", callback_data="adm_backup")
    )
    bot.edit_message_text("⚙️ **لوحة التحكم الشاملة لمدير المنظومة:**", message.chat.id, message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "adm_main_panel")
def return_to_admin_panel_callback(call):
    if not is_admin(call.from_user): return
    render_admin_panel_view(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def handle_admin_actions(call):
    if not is_admin(call.from_user): return
    action = call.data
    
    if action == "adm_add_match":
        ADMIN_SESSION[call.from_user.id] = {}
        render_home_cat_selection(call.message)
        
    elif action == "adm_add_tournament":
        ADMIN_SESSION[call.from_user.id] = {"action": "add_tournament"}
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏆 الدوريات والأندية", callback_data="t_cat_الدوريات"),
                   InlineKeyboardButton("🌍 القارات والمنتخبات", callback_data="t_cat_القارات"))
        markup.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="adm_main_panel"))
        bot.edit_message_text("🗂️ **[خطوة 1 من 3]** اختر التصنيف الأساسي للبطولة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif action == "adm_manage_db":
        admin_manage_db_categories(call)

    elif action == "adm_settle_list":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT match_id, home_team, away_team FROM matches WHERE status='ACTIVE'")
        matches = cursor.fetchall()
        conn.close()
        if not matches:
            bot.answer_callback_query(call.id, "لا توجد مباريات نشطة بحاجة لرصد.")
            return
        markup = InlineKeyboardMarkup(row_width=1)
        for m in matches:
            markup.add(InlineKeyboardButton(f"🏁 إنهاء وحسم: {m[1]} × {m[2]}", callback_data=f"as_score_{m[0]}"))
        markup.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="adm_main_panel"))
        bot.edit_message_text("🏟️ اختر المباراة لإدخال النتيجة الرسمية وضخ النقاط:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif action == "adm_delete_list":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT match_id, home_team, away_team FROM matches WHERE status='ACTIVE'")
        matches = cursor.fetchall()
        conn.close()
        if not matches:
            bot.answer_callback_query(call.id, "لا توجد مباريات نشطة لحذفها.")
            return
        markup = InlineKeyboardMarkup(row_width=1)
        for m in matches:
            markup.add(InlineKeyboardButton(f"🗑️ حذف نهائي: {m[1]} × {m[2]}", callback_data=f"ad_del_{m[0]}"))
        markup.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="adm_main_panel"))
        bot.edit_message_text("⚠️ اختر المباراة للمسح والإلغاء النهائي:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "adm_manage_users":
        show_admin_users_page(call.message.chat.id, page=0, message_id=call.message.message_id)

    elif action == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 أرسل الآن نص الرسالة المراد إذاعتها لجميع المشتركين المسجلين:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif action == "adm_backup":
        try:
            with open("contest_master.db", "rb") as db_file:
                db_data = db_file.read()
            bio = BytesIO(db_data)
            bio.name = f"backup_{datetime.now().strftime('%Y_%m_%d_%H%M%S')}.db"
            bot.send_document(call.message.chat.id, bio, caption="💾 نسخة احتياطية لقاعدة البيانات الحالية لجميع المشتركين.")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء محاولة عمل النسخة الاحتياطية:\n`{str(e)}`", parse_mode="Markdown")

# ==========================================
# 👥 محرك إدارة حسابات وبيانات المنافسين المتقدم
# ==========================================
def show_admin_users_page(chat_id, page=0, message_id=None):
    items_per_page = 8
    offset = page * items_per_page
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, full_name, points, banned FROM users ORDER BY points DESC LIMIT ? OFFSET ?", (items_per_page, offset))
    users_list = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    
    if not users_list and page == 0:
        bot.send_message(chat_id, "👥 قاعدة بيانات المنافسين فارغة تماماً حالياً.")
        return
        
    markup = InlineKeyboardMarkup(row_width=1)
    for uid, name, pts, banned in users_list:
        prefix_icon = "🚫 " if banned == 1 else "👤 "
        button_text = f"{prefix_icon}{name} ➖ ({pts} ن)"
        markup.add(InlineKeyboardButton(button_text, callback_data=f"au_v_{uid}_{page}"))
        
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"au_p_{page - 1}"))
    if offset + items_per_page < total_users:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"au_p_{page + 1}"))
    if nav_buttons:
        markup.row(*nav_buttons)
        
    markup.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="adm_main_panel"))
    
    text = "👥 **لوحة التحكم بالمنافسين وحساباتهم المفتوحة:**\nاختر منافساً من القائمة أدناه لعرض هويته وهاتفه، تعديل نقاطه يدوياً، تعديل اسمه، أو تطبيق قرار الحظر:"
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException:
            pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

def render_single_user_management(message, uid, page):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, username, phone_number, points, banned FROM users WHERE user_id=?", (uid,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        bot.send_message(message.chat.id, "❌ خطأ، لم يتم العثور على بيانات هذا المستخدم في النظام.")
        return
        
    name, username, phone, points, banned = user
    ban_status = "🔴 محظور وموقوف نهائياً" if banned == 1 else "🟢 نشط وصلاحياته كاملة"
    user_handle = f"@{username}" if username else "لا يوجد معرّف اسمي"
    
    text = f"👤 **ملف إدارة المنافس الرقمي:**\n\n" \
           f"📝 الاسم الحالي: *{escape_markdown(name)}*\n" \
           f"🆔 الهوية الرقمية (Telegram ID): `{uid}`\n" \
           f"🌐 اليوزر نيم: {escape_markdown(user_handle)}\n" \
           f"📞 رقم الهاتف المسجّل: `{phone}`\n" \
           f"💰 رصيد النقاط الحالي: *{points}* نقطة\n" \
           f"🔒 حالة الحساب حالياً: *{ban_status}*\n\n" \
           f"⚙️ استخدم الأزرار بالأسفل لإجراء التعديلات الفورية الصارمة:"
           
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✏️ تعديل الاسم", callback_data=f"au_editname_{uid}_{page}"),
        InlineKeyboardButton("💰 تعديل النقاط يدوي", callback_data=f"au_editpts_{uid}_{page}")
    )
    toggle_ban_text = "🟢 إلغاء الحظر عن المنافس" if banned == 1 else "🚫 حظر المنافس من البوت"
    markup.add(InlineKeyboardButton(toggle_ban_text, callback_data=f"au_toggleban_{uid}_{page}"))
    markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data=f"au_back_{page}"))
    
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("au_"))
def handle_user_management_callbacks(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    action = parts[1]
    
    if action == "p":
        page = int(parts[2])
        show_admin_users_page(call.message.chat.id, page=page, message_id=call.message.message_id)
        
    elif action == "v":
        uid = int(parts[2])
        page = int(parts[3])
        render_single_user_management(call.message, uid, page)
        
    elif action == "toggleban":
        uid = int(parts[2])
        page = int(parts[3])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
        res = cursor.fetchone()
        if res:
            new_ban = 1 if res[0] == 0 else 0
            cursor.execute("UPDATE users SET banned=? WHERE user_id=?", (new_ban, uid))
            conn.commit()
            bot.answer_callback_query(call.id, "🚫 تم حظر المشترك بنجاح!" if new_ban==1 else "🟢 تم إلغاء حظر المشترك!", show_alert=True)
        conn.close()
        render_single_user_management(call.message, uid, page)
        
    elif action == "editname":
        uid = int(parts[2])
        page = int(parts[3])
        ADMIN_SESSION[call.from_user.id] = {"edit_uid": uid, "page": page, "field": "name"}
        msg = bot.send_message(call.message.chat.id, "✍️ أرسل الآن الاسم الثلاثي الجديد بالكامل للمنافس:")
        bot.register_next_step_handler(msg, process_admin_edit_user)
        
    elif action == "editpts":
        uid = int(parts[2])
        page = int(parts[3])
        ADMIN_SESSION[call.from_user.id] = {"edit_uid": uid, "page": page, "field": "points"}
        msg = bot.send_message(call.message.chat.id, "🔢 أرسل القيمة العددية الإجمالية الجديدة للنقاط (مثال: 120 أو إدخال نقاط سالبة كـ -10):")
        bot.register_next_step_handler(msg, process_admin_edit_user)
        
    elif action == "back":
        page = int(parts[2])
        show_admin_users_page(call.message.chat.id, page=page, message_id=call.message.message_id)

def process_admin_edit_user(message):
    admin_id = message.from_user.id
    if not is_admin(message.from_user) or admin_id not in ADMIN_SESSION or "edit_uid" not in ADMIN_SESSION[admin_id]:
        return
        
    session_data = ADMIN_SESSION[admin_id]
    target_uid = session_data["edit_uid"]
    page = session_data["page"]
    field = session_data["field"]
    input_text = message.text.strip() if message.text else ""
    
    if not input_text:
        bot.send_message(message.chat.id, "❌ تم إلغاء الإجراء بسبب إدخال نص فارغ.")
        ADMIN_SESSION.pop(admin_id, None)
        return
        
    conn = get_db()
    cursor = conn.cursor()
    
    if field == "name":
        if len(input_text.split()) < 3:
            msg = bot.send_message(message.chat.id, "❌ يجب إدخال اسم ثلاثي صحيح لتفادي الانهيار الرقمي للمنافسة، أعد الإرسال مجدداً:")
            bot.register_next_step_handler(msg, process_admin_edit_user)
            conn.close()
            return
        cursor.execute("UPDATE users SET full_name=? WHERE user_id=?", (input_text, target_uid))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ تم بنجاح تعديل اسم المنافس إلى: *{escape_markdown(input_text)}*", parse_mode="Markdown")
        
    elif field == "points":
        if not input_text.isdigit() and not (input_text.startswith('-') and input_text[1:].isdigit()):
            msg = bot.send_message(message.chat.id, "❌ إدخال خاطئ! يرجى إرسال قيمة رقمية صحيحة فقط لحساب الرصيد الجديد:")
            bot.register_next_step_handler(msg, process_admin_edit_user)
            conn.close()
            return
        new_points = int(input_text)
        cursor.execute("UPDATE users SET points=? WHERE user_id=?", (new_points, target_uid))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ تم تحديث رصيد النقاط يدوياً إلى الإجمالي الجديد: `{new_points}` نقطة.")
        
    conn.close()
    ADMIN_SESSION.pop(admin_id, None)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👁️ استعراض الحساب المحدث الآن", callback_data=f"au_v_{target_uid}_{page}"))
    markup.add(InlineKeyboardButton("🔙 العودة لقائمة المنافسين", callback_data=f"au_back_{page}"))
    bot.send_message(message.chat.id, "⚙️ اختر الإجراء التالي لإدارة بيانات المشتركين وسجلاتهم بكل سهولة:", reply_markup=markup)

# ==========================================
# 📢 آلية الإذاعة الجماعية (Broadcast System)
# ==========================================
def process_broadcast(message):
    if not is_admin(message.from_user): return
    broadcast_text = message.text.strip() if message.text else ""
    if not broadcast_text:
        bot.send_message(message.chat.id, "❌ تم إلغاء الإذاعة بسبب إرسال نص فارغ.")
        return
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    success, failed = 0, 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 **إعلان هام من إدارة المسابقة:**\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
        except Exception:
            failed += 1
            
    bot.send_message(message.chat.id, f"📢 **تمت الإذاعة الجماعية بنجاح!**\n\n🟢 تسليم ناجح: `{success}`\n🔴 تعذر الإرسال (حظر البوت): `{failed}`", parse_mode="Markdown")

# ==========================================
# 🏆 معالج إضافة البطولات المخصصة وإدارة بنك البيانات (CRUD)
# ==========================================
def admin_manage_db_categories(call):
    if not is_admin(call.from_user): return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏆 الدوريات والأندية", callback_data="mdb_cat_الدوريات"),
               InlineKeyboardButton("🌍 القارات والمنتخبات", callback_data="mdb_cat_القارات"))
    markup.add(InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="adm_main_panel"))
    bot.edit_message_text("🛠️ **إدارة بنك البيانات والمسابقات:** اختر التصنيف المراد إدارته، حذفه أو التعديل عليه:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdb_cat_"))
def admin_manage_db_tournaments(call):
    if not is_admin(call.from_user): return
    cat = call.data.split("_")[2]
    load_dynamic_tournaments()
    
    markup = InlineKeyboardMarkup(row_width=2)
    if cat in DATA_BANK:
        for tour in DATA_BANK[cat].keys():
            markup.add(InlineKeyboardButton(tour, callback_data=f"mdb_tr_{cat}_{tour}"))
            
    markup.add(InlineKeyboardButton("➕ إضافة بطولة جديدة لهذا القسم", callback_data=f"mdb_addtour_{cat}"))
    markup.add(InlineKeyboardButton("🔙 العودة للخلف", callback_data="adm_manage_db"))
    bot.edit_message_text(f"🗂️ **تصفح بطولات قسم [{cat}]:** اختر بطولة لعرض خيارات التعديل، الحذف بالكامل أو إدارة أنديتها:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdb_addtour_"))
def admin_add_tour_from_manage(call):
    if not is_admin(call.from_user): return
    cat = call.data.split("_")[2]
    ADMIN_SESSION[call.from_user.id] = {"t_category": cat}
    msg = bot.edit_message_text("✍️ **[خطوة 2 من 3]** أرسل اسم البطولة الجديدة ليتم حجزها ومزامنتها بنجاح (مثال: دوري أبطال أوروبا):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_tournament_name)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdb_tr_"))
def admin_manage_single_tournament(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✏️ تعديل اسم هذه البطولة", callback_data=f"mdbt_edit_{cat}_{tour}"),
        InlineKeyboardButton("🗑️ حذف هذه البطولة بالكامل", callback_data=f"mdbt_del_{cat}_{tour}"),
        InlineKeyboardButton("👟 استعراض وإدارة الفرق الحالية", callback_data=f"mdbt_teams_{cat}_{tour}_0"),
        InlineKeyboardButton("➕ إضافة فريق جديد للبطولة", callback_data=f"mdbt_addteam_{cat}_{tour}"),
        InlineKeyboardButton("🔙 العودة لقائمة البطولات", callback_data=f"mdb_cat_{cat}")
    )
    bot.edit_message_text(f"🏆 **إدارة مسار البطولة:** {tour}\n💼 القسم الأساسي: {cat}\n\nاختر الإجراء الفوري والمطلوب تطبيقه:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbt_del_"))
def admin_delete_tournament(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dynamic_teams WHERE category=? AND tournament_name=?", (cat, tour))
    cursor.execute("INSERT OR REPLACE INTO tournament_mods (category, old_name, new_name, status) VALUES (?, ?, ?, 'DELETED')", (cat, tour, ''))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    bot.answer_callback_query(call.id, f"🗑️ تم حذف بطولة {tour} وكافة السجلات المرتبطة بها نهائياً!", show_alert=True)
    call.data = f"mdb_cat_{cat}"
    admin_manage_db_tournaments(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbt_edit_"))
def admin_edit_tournament_prompt(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    
    ADMIN_SESSION[call.from_user.id] = {"action": "rename_tournament", "cat": cat, "tour": tour}
    msg = bot.send_message(call.message.chat.id, f"✍️ أرسل الآن الاسم الجديد البديل لبطولة *{escape_markdown(tour)}*:")
    bot.register_next_step_handler(msg, process_rename_tournament)

def process_rename_tournament(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION or ADMIN_SESSION[uid].get("action") != "rename_tournament": return
    sess = ADMIN_SESSION[uid]
    new_name = message.text.strip() if message.text else ""
    if not new_name:
        bot.send_message(message.chat.id, "❌ اسم غير صالح. تم إلغاء العملية.")
        ADMIN_SESSION.pop(uid, None)
        return
        
    cat = sess["cat"]
    old_name = sess["tour"]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE dynamic_teams SET tournament_name=? WHERE category=? AND tournament_name=?", (new_name, cat, old_name))
    cursor.execute("INSERT OR REPLACE INTO tournament_mods (category, old_name, new_name, status) VALUES (?, ?, ?, 'ACTIVE')", (cat, old_name, new_name))
    cursor.execute("UPDATE team_mods SET tournament=? WHERE category=? AND tournament=?", (new_name, cat, old_name))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    bot.send_message(message.chat.id, f"✅ تم تعديل وتغيير اسم البطولة بنجاح إلى: *{escape_markdown(new_name)}*")
    ADMIN_SESSION.pop(uid, None)
    show_main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbt_addteam_"))
def admin_add_team_prompt(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    
    ADMIN_SESSION[call.from_user.id] = {"action": "add_single_team", "cat": cat, "tour": tour}
    msg = bot.send_message(call.message.chat.id, f"⚽ أرسل اسم النادي أو المنتخب الجديد المراد ضمه لبطولة *{escape_markdown(tour)}*:")
    bot.register_next_step_handler(msg, process_add_single_team)

def process_add_single_team(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION or ADMIN_SESSION[uid].get("action") != "add_single_team": return
    sess = ADMIN_SESSION[uid]
    team_name = message.text.strip() if message.text else ""
    if not team_name:
        bot.send_message(message.chat.id, "❌ الاسم فارغ! تم الإلغاء.")
        ADMIN_SESSION.pop(uid, None)
        return
        
    cat = sess["cat"]
    tour = sess["tour"]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO dynamic_teams (category, tournament_name, team_name) VALUES (?, ?, ?)", (cat, tour, team_name))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    bot.send_message(message.chat.id, f"✅ تم إضافة الفريق *{escape_markdown(team_name)}* بنجاح إلى البطولة المحددة!")
    ADMIN_SESSION.pop(uid, None)
    show_main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbt_teams_"))
def admin_manage_teams_page(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    page = int(parts[4])
    
    load_dynamic_tournaments()
    teams_list = DATA_BANK.get(cat, {}).get(tour, [])
    
    items_per_page = 10
    offset = page * items_per_page
    current_teams = teams_list[offset:offset+items_per_page]
    
    markup = InlineKeyboardMarkup(row_width=2)
    for team in current_teams:
        full_idx = teams_list.index(team)
        markup.add(InlineKeyboardButton(f"⚽ {team}", callback_data=f"mdbm_tm_{cat}_{tour}_{full_idx}_{page}"))
        
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"mdbt_teams_{cat}_{tour}_{page - 1}"))
    if offset + items_per_page < len(teams_list):
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"mdbt_teams_{cat}_{tour}_{page + 1}"))
    if nav_buttons:
        markup.row(*nav_buttons)
        
    markup.add(InlineKeyboardButton("🔙 عودة للبطولة", callback_data=f"mdb_tr_{cat}_{tour}"))
    bot.edit_message_text(f"💡 **استعراض فرق [{tour}] (صفحة {page+1}):**\nاختر الكيان/النادي المراد حذفه أو تعديل اسمه يدوياً:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbm_tm_"))
def admin_single_team_actions(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    full_idx = int(parts[4])
    page = int(parts[5])
    
    load_dynamic_tournaments()
    teams_list = DATA_BANK.get(cat, {}).get(tour, [])
    if full_idx >= len(teams_list):
        bot.answer_callback_query(call.id, "خطأ في جلب بيانات النادي.")
        return
        
    team_name = teams_list[full_idx]
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"✏️ تعديل اسم: {team_name}", callback_data=f"mdbtm_edit_{cat}_{tour}_{full_idx}_{page}"),
        InlineKeyboardButton(f"🗑️ حذف هذا الفريق من البطولة نهائياً", callback_data=f"mdbtm_del_{cat}_{tour}_{full_idx}_{page}"),
        InlineKeyboardButton("🔙 العودة لقائمة الفرق", callback_data=f"mdbt_teams_{cat}_{tour}_{page}")
    )
    bot.edit_message_text(f"⚽ **لوحة التحكم بالكيان:** {team_name}\n🏆 البطولة: {tour}\n💼 القسم: {cat}", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbtm_del_"))
def admin_delete_single_team(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    full_idx = int(parts[4])
    page = int(parts[5])
    
    load_dynamic_tournaments()
    teams_list = DATA_BANK.get(cat, {}).get(tour, [])
    if full_idx >= len(teams_list): return
    team_name = teams_list[full_idx]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dynamic_teams WHERE category=? AND tournament_name=? AND team_name=?", (cat, tour, team_name))
    cursor.execute("INSERT OR REPLACE INTO team_mods (category, tournament, old_name, new_name, status) VALUES (?, ?, ?, '', 'DELETED')", (cat, tour, team_name))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    bot.answer_callback_query(call.id, f"🗑️ تم سحب وإلغاء {team_name} من البطولة!", show_alert=True)
    call.data = f"mdbt_teams_{cat}_{tour}_{page}"
    admin_manage_teams_page(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mdbtm_edit_"))
def admin_edit_team_prompt(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    cat = parts[2]
    tour = parts[3]
    full_idx = int(parts[4])
    page = int(parts[5])
    
    load_dynamic_tournaments()
    teams_list = DATA_BANK.get(cat, {}).get(tour, [])
    if full_idx >= len(teams_list): return
    team_name = teams_list[full_idx]
    
    ADMIN_SESSION[call.from_user.id] = {"action": "rename_team", "cat": cat, "tour": tour, "old_team": team_name, "page": page}
    msg = bot.send_message(call.message.chat.id, f"✍️ أرسل الاسم الجديد المعدّل للفريق الحالي *{escape_markdown(team_name)}*:")
    bot.register_next_step_handler(msg, process_rename_team)

def process_rename_team(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION or ADMIN_SESSION[uid].get("action") != "rename_team": return
    sess = ADMIN_SESSION[uid]
    new_team_name = message.text.strip() if message.text else ""
    if not new_team_name:
        bot.send_message(message.chat.id, "❌ إدخال خاطئ. تم الإلغاء.")
        ADMIN_SESSION.pop(uid, None)
        return
        
    cat = sess["cat"]
    tour = sess["tour"]
    old_team = sess["old_team"]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE dynamic_teams SET team_name=? WHERE category=? AND tournament_name=? AND team_name=?", (new_team_name, cat, tour, old_team))
    cursor.execute("INSERT OR REPLACE INTO team_mods (category, tournament, old_name, new_name, status) VALUES (?, ?, ?, ?, 'ACTIVE')", (cat, tour, old_team, new_team_name))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    bot.send_message(message.chat.id, f"✅ تم تعديل المسمى بنجاح إلى: *{escape_markdown(new_team_name)}*")
    ADMIN_SESSION.pop(uid, None)
    show_main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_cat_"))
def handle_tournament_category(call):
    if not is_admin(call.from_user): return
    uid = call.from_user.id
    if uid not in ADMIN_SESSION: ADMIN_SESSION[uid] = {}
    
    ADMIN_SESSION[uid]["t_category"] = call.data.replace("t_cat_", "")
    msg = bot.edit_message_text("✍️ **[خطوة 2 من 3]** أرسل اسم البطولة الجديدة (مثال: دوري أبطال أوروبا):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_tournament_name)

def process_tournament_name(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION:
        show_admin_panel(message)
        return
        
    tour_name = message.text.strip() if message.text else ""
    if not tour_name:
        msg = bot.send_message(message.chat.id, "❌ اسم غير صالح، يرجى إعادة الإرسال:")
        bot.register_next_step_handler(msg, process_tournament_name)
        return
        
    ADMIN_SESSION[uid]["t_name"] = tour_name
    msg = bot.send_message(message.chat.id, f"📋 **[خطوة 3 من 3]** أرسل الآن **أسماء الفرق** التابعة لها.\n⚠️ اكتب كل فريق في **سطر منفصل**:")
    bot.register_next_step_handler(msg, process_tournament_teams)

def process_tournament_teams(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION or "t_name" not in ADMIN_SESSION[uid]:
        show_admin_panel(message)
        return
        
    text = message.text.strip() if message.text else ""
    if not text:
        msg = bot.send_message(message.chat.id, "❌ الرجاء إدخل فرق صحيحة:")
        bot.register_next_step_handler(msg, process_tournament_teams)
        return
        
    teams = [t.strip() for t in re.split(r'[\n,]+', text) if t.strip()]
    cat = ADMIN_SESSION[uid]["t_category"]
    tour_name = ADMIN_SESSION[uid]["t_name"]
    
    conn = get_db()
    cursor = conn.cursor()
    for team in teams:
        cursor.execute("INSERT INTO dynamic_teams (category, tournament_name, team_name) VALUES (?, ?, ?)", (cat, tour_name, team))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    bot.send_message(message.chat.id, f"🏆 **تمت إضافة البطولة بنجاح!**\n\n🗂️ التصنيف: *{cat}*\n🥇 البطولة: *{tour_name}*\n👥 عدد الفرق: `{len(teams)}` فريق.")
    ADMIN_SESSION.pop(uid, None)
    show_main_menu(message)

# ==========================================
# ⚽ نظام معالج جدولة المباريات (Match Wizard)
# ==========================================
def render_home_cat_selection(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏆 الدوريات والأندية", callback_data="ax_shc_الدوريات"),
               InlineKeyboardButton("🌍 القارات والمنتخبات", callback_data="ax_shc_القارات"))
    markup.add(InlineKeyboardButton("🔙 إلغاء والعودة للوحة التحكم", callback_data="adm_main_panel"))
    bot.edit_message_text("🗂️ **[الفريق الأول - المستضيف]** اختر التصنيف الأساسي:", message.chat.id, message.message_id, reply_markup=markup)

def render_home_sub_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_h"]
    markup = InlineKeyboardMarkup(row_width=2)
    for sub in DATA_BANK[cat].keys():
        markup.add(InlineKeyboardButton(sub, callback_data=f"ax_shs_{sub}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_hcat"))
    bot.edit_message_text(f"📁 **[الفريق الأول]** تصنيف *{cat}* ➖ اختر الفئة الفرعية:", message.chat.id, message.message_id, reply_markup=markup)

def render_home_team_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_h"]
    sub = ADMIN_SESSION[uid]["sub_category_h"]
    markup = InlineKeyboardMarkup(row_width=2)
    for idx, team in enumerate(DATA_BANK[cat][sub]):
        markup.add(InlineKeyboardButton(team, callback_data=f"ax_sht_{idx}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_hsub"))
    bot.edit_message_text(f"🏠 **[الفريق الأول]** اختر الفريق الأول (المستضيف) من فئة *{sub}*:", message.chat.id, message.message_id, reply_markup=markup)

def render_away_cat_selection(message, uid):
    home_team = ADMIN_SESSION[uid]["home_team"]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏆 الدوريات والأندية", callback_data="ax_sac_الدوريات"),
               InlineKeyboardButton("🌍 القارات والمنتخبات", callback_data="ax_sac_القارات"))
    markup.add(InlineKeyboardButton("🔙 عودة لتغيير الفريق الأول", callback_data="ax_b_hteam"))
    bot.edit_message_text(f"🗂️ **[الفريق الثاني - الضيف]** اختر تصنيفه الآن\n💡 (المستضيف الحالي: *{home_team}*):", message.chat.id, message.message_id, reply_markup=markup)

def render_away_sub_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_a"]
    markup = InlineKeyboardMarkup(row_width=2)
    for sub in DATA_BANK[cat].keys():
        markup.add(InlineKeyboardButton(sub, callback_data=f"ax_sas_{sub}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_acat"))
    bot.edit_message_text(f"📁 **[الفريق الثاني]** تصنيف *{cat}* ➖ اختر الفئة الفرعية للضيف:", message.chat.id, message.message_id, reply_markup=markup)

def render_away_team_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_a"]
    sub = ADMIN_SESSION[uid]["sub_category_a"]
    home_team = ADMIN_SESSION[uid]["home_team"]
    markup = InlineKeyboardMarkup(row_width=2)
    for idx, team in enumerate(DATA_BANK[cat][sub]):
        if team != home_team:  
            markup.add(InlineKeyboardButton(team, callback_data=f"ax_sat_{idx}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_asub"))
    bot.edit_message_text(f"✈️ **[الفريق الثاني]** اختر فريق الضيف من فئة *{sub}*:", message.chat.id, message.message_id, reply_markup=markup)

def render_match_type_selection(message, uid):
    home = ADMIN_SESSION[uid]["home_team"]
    away = ADMIN_SESSION[uid]["away_team"]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📋 مباراة دوري عادية", callback_data="ax_st_مباراة عادية"),
               InlineKeyboardButton("⚔️ خروج مغلوب (ترجيح)", callback_data="ax_st_خروج مغلوب (ترجيح)"))
    markup.add(InlineKeyboardButton("🔙 عودة لتغيير الفريق الثاني", callback_data="ax_b_ateam"))
    bot.edit_message_text(f"⚙️ **تحديد نظام الفرز:**\n🏟️ المباراة: *{home}* × *{away}*\nاختر نوع ونظام النقاط المعتمد:", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

def render_time_adjustment_view(message, admin_id):
    data = ADMIN_SESSION[admin_id]
    current_set_time = data["time"].strftime("%Y-%m-%d %H:%M")
    markup = InlineKeyboardMarkup()
    
    markup.row(
        InlineKeyboardButton("➕ 1 يوم", callback_data="at_p1d"), 
        InlineKeyboardButton("➕ 1 ساعة", callback_data="at_p1h"), 
        InlineKeyboardButton("➕ 15 دقيقة", callback_data="at_p15m"),
        InlineKeyboardButton("➕ 1 دقيقة", callback_data="at_p1m")
    )
    markup.row(
        InlineKeyboardButton("➖ 1 يوم", callback_data="at_m1d"), 
        InlineKeyboardButton("➖ 1 ساعة", callback_data="at_m1h"), 
        InlineKeyboardButton("➖ 15 دقيقة", callback_data="at_m15m"), 
        InlineKeyboardButton("➖ 1 دقيقة", callback_data="at_m1m")
    )
    markup.row(InlineKeyboardButton(f"🚀 اعتماد ونشر المباراة [{current_set_time}]", callback_data="at_confirm"))
    markup.row(InlineKeyboardButton("🔙 عودة لتغيير نوع المباراة", callback_data="ax_b_type"))
    
    bot.edit_message_text(f"📆 **ضبط الوقت والتاريخ للمباراة بالأزرار:**\n\n🏟️ المباراة: {data['home_team']} × {data['away_team']}\n⏱️ موعد الإغلاق: `{current_set_time}`", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ax_"))
def build_match_wizard(call):
    uid = call.from_user.id
    if not is_admin(call.from_user): return
    if uid not in ADMIN_SESSION: ADMIN_SESSION[uid] = {}
    action = call.data
    
    if action.startswith("ax_shc_"):
        ADMIN_SESSION[uid]["category_h"] = action.replace("ax_shc_", "")
        render_home_sub_selection(call.message, uid)
    elif action.startswith("ax_shs_"):
        ADMIN_SESSION[uid]["sub_category_h"] = action.replace("ax_shs_", "")
        render_home_sub_selection(call.message, uid)
    elif action.startswith("ax_sht_"):
        idx = int(action.replace("ax_sht_", ""))
        cat = ADMIN_SESSION[uid]["category_h"]
        sub = ADMIN_SESSION[uid]["sub_category_h"]
        ADMIN_SESSION[uid]["home_team"] = DATA_BANK[cat][sub][idx]
        render_away_cat_selection(call.message, uid)
    elif action.startswith("ax_sac_"):
        ADMIN_SESSION[uid]["category_a"] = action.replace("ax_sac_", "")
        render_away_sub_selection(call.message, uid)
    elif action.startswith("ax_sas_"):
        ADMIN_SESSION[uid]["sub_category_a"] = action.replace("ax_sas_", "")
        render_away_team_selection(call.message, uid)
    elif action.startswith("ax_sat_"):
        idx = int(action.replace("ax_sat_", ""))
        cat = ADMIN_SESSION[uid]["category_a"]
        sub = ADMIN_SESSION[uid]["sub_category_a"]
        ADMIN_SESSION[uid]["away_team"] = DATA_BANK[cat][sub][idx]
        render_match_type_selection(call.message, uid)
    elif action.startswith("ax_st_"):
        ADMIN_SESSION[uid]["match_type"] = action.replace("ax_st_", "")
        ADMIN_SESSION[uid]["time"] = datetime.now() + timedelta(hours=2)
        render_time_adjustment_view(call.message, uid)
        
    elif action == "ax_b_hcat": render_home_cat_selection(call.message)
    elif action == "ax_b_hsub": render_home_sub_selection(call.message, uid)
    elif action == "ax_b_hteam": render_home_team_selection(call.message, uid)
    elif action == "ax_b_acat": render_away_cat_selection(call.message, uid)
    elif action == "ax_b_asub": render_away_sub_selection(call.message, uid)
    elif action == "ax_b_ateam": render_away_team_selection(call.message, uid)
    elif action == "ax_b_type": render_match_type_selection(call.message, uid)

@bot.callback_query_handler(func=lambda call: call.data.startswith("at_"))
def adjust_match_time(call):
    admin_id = call.from_user.id
    if not is_admin(call.from_user): return
    action = call.data
    
    if action == "at_p1d": ADMIN_SESSION[admin_id]["time"] += timedelta(days=1)
    elif action == "at_m1d": ADMIN_SESSION[admin_id]["time"] -= timedelta(days=1)
    elif action == "at_p1h": ADMIN_SESSION[admin_id]["time"] += timedelta(hours=1)
    elif action == "at_m1h": ADMIN_SESSION[admin_id]["time"] -= timedelta(hours=1)
    elif action == "at_p15m": ADMIN_SESSION[admin_id]["time"] += timedelta(minutes=15)
    elif action == "at_m15m": ADMIN_SESSION[admin_id]["time"] -= timedelta(minutes=15)
    elif action == "at_p1m": ADMIN_SESSION[admin_id]["time"] += timedelta(minutes=1)
    elif action == "at_m1m": ADMIN_SESSION[admin_id]["time"] -= timedelta(minutes=1)
    elif action == "at_confirm":
        data = ADMIN_SESSION[admin_id]
        time_str = data["time"].strftime("%Y-%m-%d %H:%M")
        
        cat_str = data['category_h'] if data['category_h'] == data['category_a'] else f"{data['category_h']} - {data['category_a']}"
        sub_cat_str = data['sub_category_h'] if data['sub_category_h'] == data['sub_category_a'] else f"{data['sub_category_h']} × {data['sub_category_a']}"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO matches (category, sub_category, home_team, away_team, match_type, start_time) VALUES (?, ?, ?, ?, ?, ?)",
                       (cat_str, sub_cat_str, data['home_team'], data['away_team'], data['match_type'], time_str))
        conn.commit()
        conn.close()
        bot.edit_message_text(f"🚀 **تمت الجدولة والنشر بنجاح!**\nالمباراة: {data['home_team']} × {data['away_team']}\n⏱️ وقت الإغلاق: {time_str}", call.message.chat.id, call.message.message_id)
        ADMIN_SESSION.pop(admin_id, None)
        return
    render_time_adjustment_view(call.message, admin_id)

# ==========================================
# 🏁 رصد نتائج المباريات الرسمية وحساب النقاط المعقد
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("as_"))
def admin_settle_interface(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    match_id = int(parts[2])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team, match_type FROM matches WHERE match_id=?", (match_id,))
    match = cursor.fetchone()
    conn.close()
    
    ADMIN_SESSION[call.from_user.id] = {"match_id": match_id, "hp": 0, "ap": 0, "php": 0, "pap": 0, "type": match[2], "home": match[0], "away": match[1]}
    render_admin_settle_keyboard(call.message, call.from_user.id)

def render_admin_settle_keyboard(message, admin_id):
    data = ADMIN_SESSION[admin_id]
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(f"➕ {data['home']}", callback_data="s_inc_h"),
        InlineKeyboardButton(f"🏁 {data['hp']} - {data['ap']} 🏁", callback_data="none"),
        InlineKeyboardButton(f"➕ {data['away']}", callback_data="s_inc_a")
    )
    markup.row(
        InlineKeyboardButton(f"➖ {data['home']}", callback_data="s_dec_h"),
        InlineKeyboardButton(" ", callback_data="none"),
        InlineKeyboardButton(f"➖ {data['away']}", callback_data="s_dec_a")
    )
    
    if data['type'] == "خروج مغلوب (ترجيح)" and data['hp'] == data['ap']:
        markup.row(InlineKeyboardButton("🥅 ركلات الترجيح الرسمية 🥅", callback_data="none"))
        markup.row(
            InlineKeyboardButton(f"➕ ركلات {data['home']}", callback_data="s_inc_ph"),
            InlineKeyboardButton(f"🎯 {data['php']} - {data['pap']} 🎯", callback_data="none"),
            InlineKeyboardButton(f"➕ ركلات {data['away']}", callback_data="s_inc_pa")
        )
        markup.row(
            InlineKeyboardButton(f"➖ {data['home']}", callback_data="s_dec_ph"),
            InlineKeyboardButton(" ", callback_data="none"),
            InlineKeyboardButton(f"➖ {data['away']}", callback_data="s_dec_pa")
        )
    markup.row(InlineKeyboardButton("🏁 اعتماد النتيجة وضخ النقاط 🚀", callback_data="s_finalize"))
    bot.edit_message_text(f"⚽ **إدخال النتيجة الرسمية:**\n🏟️ {data['home']} × {data['away']}\nاستخدم الأزرار لتحديد النتيجة الحقيقية:", message.chat.id, message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("s_"))
def process_admin_settle_adjustments(call):
    if not is_admin(call.from_user): return
    admin_id = call.from_user.id
    action = call.data
    data = ADMIN_SESSION[admin_id]
    
    if action == "s_inc_h": data['hp'] += 1
    elif action == "s_dec_h" and data['hp'] > 0: data['hp'] -= 1
    elif action == "s_inc_a": data['ap'] += 1
    elif action == "s_dec_a" and data['ap'] > 0: data['ap'] -= 1
    elif action == "s_inc_ph": data['php'] += 1
    elif action == "s_dec_ph" and data['php'] > 0: data['php'] -= 1
    elif action == "s_inc_pa": data['pap'] += 1
    elif action == "s_dec_pa" and data['pap'] > 0: data['pap'] -= 1
    elif action == "s_finalize":
        match_id = data['match_id']
        real_home_score = data['hp']
        real_away_score = data['ap']
        
        real_pen_home = data['php'] if real_home_score == real_away_score else 0
        real_pen_away = data['pap'] if real_home_score == real_away_score else 0
        
        real_outcome = "HOME" if real_home_score > real_away_score else "AWAY" if real_away_score > real_home_score else "DRAW"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.user_id, u.full_name, p.home_pred, p.away_pred, p.pen_home_pred, p.pen_away_pred 
            FROM predictions p 
            LEFT JOIN users u ON p.user_id = u.user_id 
            WHERE p.match_id=?
        """, (match_id,))
        predictions = cursor.fetchall()
        
        report_lines = []
        
        for p in predictions:
            u_id, full_name, u_hp, u_ap, u_php, u_pap = p
            full_name = full_name if full_name else "مستخدم غير مسجل"
            calculated_points = 0
            u_outcome = "HOME" if u_hp > u_ap else "AWAY" if u_ap > u_hp else "DRAW"
            
            exact_match_score = False
            if u_outcome == real_outcome:
                calculated_points += 5
                if u_hp == real_home_score and u_ap == real_away_score:
                    calculated_points += 15
                    exact_match_score = True
            
            if data['type'] == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
                real_pen_winner = "HOME" if real_pen_home > real_pen_away else "AWAY"
                u_pen_winner = "HOME" if u_php > u_pap else "AWAY"
                exact_pen_score = False
                
                if u_pen_winner == real_pen_winner:
                    calculated_points += 10
                    if u_php == real_pen_home and u_pap == real_pen_away:
                        calculated_points += 15
                        exact_pen_score = True
                if exact_match_score and exact_pen_score:
                    calculated_points += 30
                    
            cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (calculated_points, u_id))
            
            pred_str = f"[{u_hp} - {u_ap}]"
            if data['type'] == "خروج مغلوب (ترجيح)" and u_outcome == "DRAW":
                pred_str += f" (ترجيح: {u_php}-{u_pap})"
            
            safe_report_name = escape_markdown(full_name)
            report_lines.append(f"👤 {safe_report_name} ➖ توقع: `{pred_str}` ➖ كسب: *+{calculated_points}* ن")
            
        cursor.execute("UPDATE matches SET status='FINISHED', home_score=?, away_score=?, pen_home_score=?, pen_away_score=? WHERE match_id=?", 
                       (real_home_score, real_away_score, real_pen_home, real_pen_away, match_id))
        conn.commit()
        conn.close()
        
        bot.edit_message_text("🎉 **تم حسم ورصد المباراة بنجاح وتحديث كافة أرصدة المتسابقين أوتوماتيكياً!**", call.message.chat.id, call.message.message_id)
        
        score_str = f"[{real_home_score} - {real_away_score}]"
        if data['type'] == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
            score_str += f" (ركلات ترجيح: {real_pen_home}-{real_pen_away})"
            
        report_header = f"📊 **تقرير الفرز للمباراة:**\n⚽ {data['home']} × {data['away']}\n🏁 النتيجة الرسمية: `{score_str}`\n───────────────────\n"
        
        if not report_lines:
            bot.send_message(call.message.chat.id, report_header + "📭 لم يقم أي منافس بتوقع هذه المباراة.")
        else:
            current_msg = report_header
            for line in report_lines:
                if len(current_msg) + len(line) + 2 > 4000:
                    bot.send_message(call.message.chat.id, current_msg, parse_mode="Markdown")
                    current_msg = "📊 **تابع تقرير التوقعات:**\n───────────────────\n"
                current_msg += line + "\n"
            if current_msg:
                bot.send_message(call.message.chat.id, current_msg, parse_mode="Markdown")
                
        ADMIN_SESSION.pop(admin_id, None)
        return
    render_admin_settle_keyboard(call.message, admin_id)

# ==========================================
# 🗑️ مسح وإلغاء المباريات
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("ad_del_"))
def delete_match_completely(call):
    if not is_admin(call.from_user): return
    match_id = int(call.data.split("_")[2])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matches WHERE match_id=?", (match_id,))
    cursor.execute("DELETE FROM predictions WHERE match_id=?", (match_id,))
    conn.commit()
    conn.close()
    bot.edit_message_text("🗑️ **تم حذف المباراة وكافة توقعاتها المرتبطة بها نهائياً من النظام.**", call.message.chat.id, call.message.message_id)

# ==========================================
# 🚀 محرك التشغيل اللانهائي (Background Threading)
# ==========================================
def run_bot():
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    # تشغيل البوت في خلفية النظام لكي لا يمنع Flask من العمل وتلقي المنافذ
    threading.Thread(target=run_bot, daemon=True).start()
    
    # السيرفر يبحث عن المنفذ المتغير، وإذا لم يجده يستخدم 5000 تلقائياً
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
