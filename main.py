import os
import re
import sqlite3
import telebot
import copy
from flask import Flask, request, abort
from datetime import datetime, timedelta
from io import BytesIO
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

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
TOKEN = os.getenv("BOT_TOKEN", "8673575186:AAHSQEMnI4QlzazufdyWwwssSlbmptQVix4")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7394452907))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Aood71arf")

bot = telebot.TeleBot(TOKEN, threaded=False)

# ==========================================
# 🛡️ دالة تأمين النصوص ضد أخطاء الماركداون
# ==========================================
def escape_markdown(text):
    if not text:
        return ""
    for char in ['*', '_', '`', '[']:
        text = str(text).replace(char, f'\\{char}')
    return text

# ==========================================
# 🗄️ بنك البيانات الكامل للمسابقات
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
# ⚡ إدارة قاعدة البيانات بأعلى كفاءة
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
        bot.send_message(message.chat.id, "🚫 **عذراً، لقد تم حظر حسابك من المشاركة!**")
        return False
    
    if user and user[0] and user[1]:
        return True
    
    msg = bot.send_message(message.chat.id, "⚠️ **عذراً، هذا البوت خاص بالمنافسة المقفلة.**\nالرجاء إرسال اسمك الثلاثي كاملاً لبدء حجز حسابك:")
    bot.register_next_step_handler(msg, register_user_name)
    return False

def register_user_name(message):
    name_text = message.text.strip() if message.text else ""
    if len(name_text.split()) < 3:
        msg = bot.send_message(message.chat.id, "❌ يجب إرسال الاسم **ثلاثياً** بشكل صحيح، حاول مجدداً:")
        bot.register_next_step_handler(msg, register_user_name)
        return
    
    USER_SESSION[message.from_user.id] = {"reg_name": name_text}
    msg = bot.send_message(message.chat.id, f"🎯 أهلاً بك *{escape_markdown(name_text)}*.\nالآن يرجى إرسال **رقم هاتفك المكون من 9 أرقام (شبكات يمنية)**:")
    bot.register_next_step_handler(msg, register_user_phone)

def register_user_phone(message):
    phone_text = message.text.strip() if message.text else ""
    if not re.match(r'^7[01378]\d{7}$', phone_text):
        msg = bot.send_message(message.chat.id, "❌ خطأ في تنسيق الرقم! يرجى إرسال رقم يمني صحيح (9 أرقام يبدأ بـ 77، 73، 71، 70، أو 78):")
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
    bot.send_message(message.chat.id, f"✅ تم تسجيلك بنجاح!\n📝 الاسم الثلاثي: *{escape_markdown(full_name)}*\n🆔 المعرّف: `{phone_text}`")
    show_main_menu(message)

def show_main_menu(message):
    uid = message.from_user.id
    USER_SESSION.pop(uid, None)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🗳️ التوقعات المتاحة"), KeyboardButton("📊 جدول الترتيب العام"))
    markup.add(KeyboardButton("🏆 مبارياتي الرابحة"), KeyboardButton("ℹ️ معلومات حسابي"))
    if is_admin(message.from_user):
        markup.add(KeyboardButton("⚙️ لوحة تحكم المشرف"))
    bot.send_message(message.chat.id, "📊 القائمة الرئيسية للمسابقة:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if check_registration(message):
        show_main_menu(message)

# ==========================================
# 🗳️ واجهات التوقعات والترتيب المحدثة (Reply)
# ==========================================
def show_available_matches(message):
    load_dynamic_tournaments()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, home_team, away_team, start_time FROM matches WHERE status='ACTIVE'")
    matches = cursor.fetchall()
    
    buttons = []
    now = datetime.now()
    for m in matches:
        match_id, home, away, s_time = m
        try:
            match_dt = datetime.strptime(s_time, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if now < match_dt:
            cursor.execute("SELECT home_pred, away_pred FROM predictions WHERE user_id=? AND match_id=?", (message.from_user.id, match_id))
            pred = cursor.fetchone()
            if pred:
                buttons.append(f"⚽ {home} [{pred[0]}-{pred[1]}] {away} (ID:{match_id})")
            else:
                buttons.append(f"⚽ {home} × {away} (ID:{match_id})")
    conn.close()
    
    if not buttons:
        bot.send_message(message.chat.id, "📭 لا توجد مباريات نشطة للتوقع حالياً.")
        return
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for btn in buttons:
        markup.add(KeyboardButton(btn))
    markup.add(KeyboardButton("🔙 العودة للقائمة الرئيسية"))
    bot.send_message(message.chat.id, "🏟️ اختر المباراة لتسجيل أو تعديل توقعك بالكامل:", reply_markup=markup)

def user_prediction_flow_init(message, match_id):
    uid = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team, match_type, start_time FROM matches WHERE match_id=?", (match_id,))
    match = cursor.fetchone()
    conn.close()
    
    if not match:
        bot.send_message(message.chat.id, "❌ المباراة غير موجودة.")
        return
        
    home, away, m_type, s_time = match
    if datetime.now() > datetime.strptime(s_time, "%Y-%m-%d %H:%M"):
        bot.send_message(message.chat.id, "🔒 عذراً، بدأت المباراة وتم إغلاق استقبال التوقعات!")
        show_main_menu(message)
        return
        
    USER_SESSION[uid] = {'state': 'predicting_score', 'match_id': match_id, 'home': home, 'away': away, 'type': m_type}
    bot.send_message(message.chat.id, f"🎯 **توقع مباراة:**\n🏟️ {home} × {away}\nالرجاء إرسال نتيجة توقعك بالصيغة (أهداف المستضيف - أهداف الضيف)\nمثال: `2-1`", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للقائمة الرئيسية")), parse_mode="Markdown")

def process_user_score_input(message):
    uid = message.from_user.id
    session_data = USER_SESSION[uid]
    text = message.text.replace(" ", "")
    
    score_match = re.match(r'^(\d+)-(\d+)$', text)
    if not score_match:
        bot.send_message(message.chat.id, "❌ تنسيق غير صحيح! يرجى إرسال النتيجة بالصيغة المطلوبة (مثال: 2-1):")
        return
        
    hp = int(score_match.group(1))
    ap = int(score_match.group(2))
    match_id = session_data['match_id']
    m_type = session_data['type']
    
    if m_type == "خروج مغلوب (ترجيح)" and hp == ap:
        session_data['state'] = 'predicting_pen'
        session_data['hp'] = hp
        session_data['ap'] = ap
        bot.send_message(message.chat.id, f"🌟 لقد توقعت التعادل [{hp}-{ap}] في الوقت الأصلي.\nالرجاء إدخال توقع ركلات الترجيح بالصيغة (ركلات المستضيف - ركلات الضيف) مثال: `5-4`:")
        return
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO predictions (user_id, match_id, home_pred, away_pred, pen_home_pred, pen_away_pred) VALUES (?, ?, ?, ?, 0, 0)",
                   (uid, match_id, hp, ap))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"✅ **تم حفظ وتثبيت توقعك بنجاح!**\n💼 النتيجة: {hp} - {ap}")
    show_main_menu(message)

def process_user_penalties_input(message):
    uid = message.from_user.id
    session_data = USER_SESSION[uid]
    text = message.text.replace(" ", "")
    
    pen_match = re.match(r'^(\d+)-(\d+)$', text)
    if not pen_match:
        bot.send_message(message.chat.id, "❌ أرسل الركلات بالصيغة الصحيحة (مثال: 5-4):")
        return
        
    php = int(pen_match.group(1))
    pap = int(pen_match.group(2))
    
    if php == pap:
        bot.send_message(message.chat.id, "❌ لا يمكن انتهاء ركلات الترجيح بالتعادل! حدد الفائز:")
        return
        
    hp = session_data['hp']
    ap = session_data['ap']
    match_id = session_data['match_id']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO predictions (user_id, match_id, home_pred, away_pred, pen_home_pred, pen_away_pred) VALUES (?, ?, ?, ?, ?, ?)",
                   (uid, match_id, hp, ap, php, pap))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"✅ **تم تثبيت توقعك بالكامل شامل ركلات الترجيح!**\n💼 النتيجة: {hp}-{ap} (ركلات: {php}-{pap})")
    show_main_menu(message)

def show_standings_page(message, page=0):
    uid = message.from_user.id
    USER_SESSION[uid] = {'state': 'standings', 'page': page}
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
        bot.send_message(message.chat.id, "📊 جدول الترتيب خالي حالياً.")
        return
        
    text = f"🏆 **جدول الترتيب العام للمنافسين (الصفحة {page + 1}):**\n\n"
    for idx, player in enumerate(players, 1):
        global_rank = offset + idx
        medal = "🥇" if global_rank == 1 else "🥈" if global_rank == 2 else "🥉" if global_rank == 3 else f"🏅 {global_rank}."
        text += f"{medal} {escape_markdown(player[0])} ➖ `{player[1]}` نقطة\n"
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    nav_row = []
    if page > 0:
        nav_row.append(KeyboardButton("⬅️ الصفحة السابقة"))
    if offset + items_per_page < total_users:
        nav_row.append(KeyboardButton("➡️ الصفحة التالية"))
    if nav_row:
        markup.add(*nav_row)
    markup.add(KeyboardButton("🔙 العودة للقائمة الرئيسية"))
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

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
        bot.send_message(message.chat.id, "🏆 لا توجد مباريات منتهية قمت بتوقعها حالياً.")
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
        bot.send_message(message.chat.id, "ℹ️ لم يتم العثور على أي نقاط رابحة في سجلاتك حتى الآن.")
    else:
        bot.send_message(message.chat.id, winning_text, parse_mode="Markdown")

def show_my_info(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, phone_number, points FROM users WHERE user_id=?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()
    
    full_name, phone_number, points = user if user else (message.from_user.first_name, "غير مسجل", 0)
    text = f"👤 **معلومات حسابك الرقمي:**\n\n" \
           f"📝 الاسم الثلاثي: *{escape_markdown(full_name)}*\n" \
           f"📞 رقم الهاتف المسجّل: `{phone_number}`\n" \
           f"💰 رصيدك الإجمالي: *{points}* نقطة"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ==========================================
# ⚙️ لوحة تحكم المشرف الرئيسية (Reply)
# ==========================================
def show_admin_panel(message):
    uid = message.from_user.id
    ADMIN_SESSION.pop(uid, None)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("➕ إضافة وجدولة مباراة جديدة"),
        KeyboardButton("🏆 إضافة بطولة جديدة ✨"),
        KeyboardButton("🛠️ إدارة وحذف وتعديل البطولات والفرق"),
        KeyboardButton("🏁 رصد نتيجة رسمية وحساب النقاط"),
        KeyboardButton("🗑️ حذف مباراة مرسلة بالكامل"),
        KeyboardButton("👥 إدارة المنافسين والتحكم بالحسابات"),
        KeyboardButton("📢 إذاعة رسالة للمشتركين (Broadcast)"),
        KeyboardButton("💾 تحميل نسخة احتياطية للبيانات (Backup)"),
        KeyboardButton("🔙 العودة للقائمة الرئيسية")
    )
    bot.send_message(message.chat.id, "⚙️ **لوحة التحكم الشاملة لمدير المنظومة:**", reply_markup=markup)

def admin_manage_db_categories_text(message):
    uid = message.from_user.id
    ADMIN_SESSION[uid] = {'state': 'db_manage_cat'}
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🗂️ تصنيف: الدوريات والأندية"), KeyboardButton("🗂️ تصنيف: القارات والمنتخبات"))
    markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
    bot.send_message(message.chat.id, "🛠️ **إدارة بنك البيانات:** اختر التصنيف الأساسي للتحرير والتعديل:", reply_markup=markup)

def admin_settle_list_text(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, home_team, away_team FROM matches WHERE status='ACTIVE'")
    matches = cursor.fetchall()
    conn.close()
    if not matches:
        bot.send_message(message.chat.id, "❌ لا توجد مباريات نشطة بحاجة لرصد حالياً.")
        return
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for m in matches:
        markup.add(KeyboardButton(f"🏁 رصد: {m[1]} × {m[2]} (ID:{m[0]})"))
    markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
    bot.send_message(message.chat.id, "🏟️ اختر المباراة لإدخال النتيجة الرسمية وضخ النقاط الحالية للمنافسين:", reply_markup=markup)

def admin_delete_list_text(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, home_team, away_team FROM matches WHERE status='ACTIVE'")
    matches = cursor.fetchall()
    conn.close()
    if not matches:
        bot.send_message(message.chat.id, "❌ لا توجد مباريات نشطة لحذفها حالياً.")
        return
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for m in matches:
        markup.add(KeyboardButton(f"🗑️ حذف: {m[1]} × {m[2]} (ID:{m[0]})"))
    markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
    bot.send_message(message.chat.id, "⚠️ اختر المباراة لمسحها وإلغائها بشكل نهائي مع التوقعات الخاصة بها:", reply_markup=markup)

# ==========================================
# 👥 محرك إدارة المنافسين المتقدم (Reply)
# ==========================================
def show_admin_users_page(message, page=0):
    uid = message.from_user.id
    ADMIN_SESSION[uid] = {'state': 'users_list', 'page': page}
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
        bot.send_message(message.chat.id, "👥 قاعدة بيانات المنافسين فارغة تماماً حالياً.")
        return
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for tuid, name, pts, banned in users_list:
        prefix_icon = "🚫 " if banned == 1 else "👤 "
        markup.add(KeyboardButton(f"{prefix_icon}{name} (ID:{tuid})"))
        
    nav_row = []
    if page > 0:
        nav_row.append(KeyboardButton("⬅️ سابق المنافسين"))
    if offset + items_per_page < total_users:
        nav_row.append(KeyboardButton("تالي المنافسين ➡️"))
    if nav_row:
        markup.add(*nav_row)
    markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
    
    bot.send_message(message.chat.id, "👥 **إدارة حسابات المشتركين وسجلاتهم الإجمالية:**\nاختر اسماً من القائمة أدناه لعرض الخيارات والملف المخصص له:", reply_markup=markup)

def render_single_user_management(message, target_uid):
    uid = message.from_user.id
    page = ADMIN_SESSION[uid].get('page', 0)
    ADMIN_SESSION[uid] = {'state': 'manage_user', 'target_uid': target_uid, 'page': page}
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, username, phone_number, points, banned FROM users WHERE user_id=?", (target_uid,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        bot.send_message(message.chat.id, "❌ خطأ، لم يتم العثور على بيانات هذا المستخدم في النظام.")
        show_admin_users_page(message, page)
        return
        
    name, username, phone, points, banned = user
    ban_status = "🔴 محظور وموقوف نهائياً" if banned == 1 else "🟢 نشط وصلاحياته كاملة"
    user_handle = f"@{username}" if username else "لا يوجد معرّف اسمي"
    
    text = f"👤 **ملف إدارة المنافس الرقمي:**\n\n" \
           f"📝 الاسم الحالي: *{escape_markdown(name)}*\n" \
           f"🆔 الهوية الرقمية (Telegram ID): `{target_uid}`\n" \
           f"🌐 اليوزر نيم: {escape_markdown(user_handle)}\n" \
           f"📞 رقم الهاتف المسجّل: `{phone}`\n" \
           f"💰 رصيد النقاط الحالي: *{points}* نقطة\n" \
           f"🔒 حالة الحساب حالياً: *{ban_status}*"
           
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("✏️ تعديل اسم هذا المنافس"), KeyboardButton("💰 تعديل نقاط هذا المنافس"))
    toggle_ban_text = "🟢 إلغاء حظر الحساب" if banned == 1 else "🚫 تطبيق حظر الحساب"
    markup.add(KeyboardButton(toggle_ban_text))
    markup.add(KeyboardButton("🔙 قائمة المنافسين"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ==========================================
# 🏁 رصد نتائج المباريات الرسمية وحساب النقاط المعقد
# ==========================================
def admin_settle_flow_init(message, match_id):
    uid = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team, match_type FROM matches WHERE match_id=?", (match_id,))
    match = cursor.fetchone()
    conn.close()
    
    if not match:
        bot.send_message(message.chat.id, "❌ المباراة غير مسجلة.")
        return
        
    ADMIN_SESSION[uid] = {'state': 'settling_score', 'match_id': match_id, 'home': match[0], 'away': match[1], 'type': match[2]}
    bot.send_message(message.chat.id, f"⚽ **إدخال النتيجة الحقيقية الرسمية للفرز:**\n🏟️ {match[0]} × {match[1]}\nأرسل النتيجة بالصيغة (المستضيف - الضيف)، مثال: `3-1`", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")), parse_mode="Markdown")

def process_admin_settle_score(message):
    uid = message.from_user.id
    session_data = ADMIN_SESSION[uid]
    text = message.text.replace(" ", "")
    
    score_match = re.match(r'^(\d+)-(\d+)$', text)
    if not score_match:
        bot.send_message(message.chat.id, "❌ صيغة غير صحيحة، أرسل النتيجة مثل: 2-0")
        return
        
    hp = int(score_match.group(1))
    ap = int(score_match.group(2))
    match_id = session_data['match_id']
    m_type = session_data['type']
    
    if m_type == "خروج مغلوب (ترجيح)" and hp == ap:
        session_data['state'] = 'settling_pen'
        session_data['hp'] = hp
        session_data['ap'] = ap
        bot.send_message(message.chat.id, f"🥅 النتيجة تعادل [{hp}-{ap}]. أرسل نتيجة ركلات الترجيح الرسمية الآن بالصيغة 4-3:")
        return
        
    finalize_match_settlement(message, match_id, hp, ap, 0, 0)

def process_admin_settle_penalties(message):
    uid = message.from_user.id
    session_data = ADMIN_SESSION[uid]
    text = message.text.replace(" ", "")
    
    pen_match = re.match(r'^(\d+)-(\d+)$', text)
    if not pen_match:
        bot.send_message(message.chat.id, "❌ أرسل الركلات بالصيغة الصحيحة 5-3:")
        return
        
    php = int(pen_match.group(1))
    pap = int(pen_match.group(2))
    if php == pap:
        bot.send_message(message.chat.id, "❌ لا يمكن التعادل في ركلات الترجيح الرسمية! حدد الركلات الفائزة:")
        return
        
    hp = session_data['hp']
    ap = session_data['ap']
    match_id = session_data['match_id']
    
    finalize_match_settlement(message, match_id, hp, ap, php, pap)

def finalize_match_settlement(message, match_id, real_home_score, real_away_score, real_pen_home, real_pen_away):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT match_type, home_team, away_team FROM matches WHERE match_id=?", (match_id,))
    m_info = cursor.fetchone()
    m_type, home_t, away_t = m_info
    
    real_outcome = "HOME" if real_home_score > real_away_score else "AWAY" if real_away_score > real_home_score else "DRAW"
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
        
        if m_type == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
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
        if m_type == "خروج مغلوب (ترجيح)" and u_outcome == "DRAW":
            pred_str += f" (ترجيح: {u_php}-{u_pap})"
        report_lines.append(f"👤 {escape_markdown(full_name)} ➖ توقع: `{pred_str}` ➖ كسب: *+{calculated_points}* ن")
        
    cursor.execute("UPDATE matches SET status='FINISHED', home_score=?, away_score=?, pen_home_score=?, pen_away_score=? WHERE match_id=?", 
                   (real_home_score, real_away_score, real_pen_home, real_pen_away, match_id))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, "🎉 **تم حسم ورصد المباراة بنجاح وتحديث كافة أرصدة المتسابقين أوتوماتيكياً!**")
    score_str = f"[{real_home_score} - {real_away_score}]"
    if m_type == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
        score_str += f" (ركلات ترجيح: {real_pen_home}-{real_pen_away})"
        
    report_header = f"📊 **تقرير الفرز للمباراة:**\n⚽ {home_t} × {away_t}\n🏁 النتيجة الرسمية: `{score_str}`\n───────────────────\n"
    if not report_lines:
        bot.send_message(message.chat.id, report_header + "📭 لم يقم أي منافس بتوقع هذه المباراة.")
    else:
        current_msg = report_header
        for line in report_lines:
            if len(current_msg) + len(line) + 2 > 4000:
                bot.send_message(message.chat.id, current_msg, parse_mode="Markdown")
                current_msg = "📊 **تابع تقرير التوقعات:**\n───────────────────\n"
            current_msg += line + "\n"
        if current_msg:
            bot.send_message(message.chat.id, current_msg, parse_mode="Markdown")
            
    show_admin_panel(message)

def process_admin_wizard_time(message):
    uid = message.from_user.id
    state_data = ADMIN_SESSION[uid]
    text = message.text.strip()
    
    if text == "⏱️ بعد ساعتين تلقائياً":
        dt = datetime.now() + timedelta(hours=2)
        time_str = dt.strftime("%Y-%m-%d %H:%M")
    else:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
            time_str = text
        except ValueError:
            bot.send_message(message.chat.id, "❌ صيغة الوقت خاطئة! يرجى إدخال الوقت بالصيغة الدقيقة المطلوبة `YYYY-MM-DD HH:MM`:")
            return
            
    cat_str = state_data['cat_h'] if state_data['cat_h'] == state_data['cat_a'] else f"{state_data['cat_h']} - {state_data['cat_a']}"
    sub_cat_str = state_data['sub_h'] if state_data['sub_h'] == state_data['sub_a'] else f"{state_data['sub_h']} × {state_data['sub_a']}"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO matches (category, sub_category, home_team, away_team, match_type, start_time) VALUES (?, ?, ?, ?, ?, ?)",
                   (cat_str, sub_cat_str, state_data['home_team'], state_data['away_team'], state_data['match_type'], time_str))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"🚀 **تمت الجدولة والنشر بنجاح للمباراة!**\n🏟️ {state_data['home_team']} × {state_data['away_team']}\n⏱️ موعد الإغلاق: {time_str}")
    show_admin_panel(message)

def delete_match_completely(message, match_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matches WHERE match_id=?", (match_id,))
    cursor.execute("DELETE FROM predictions WHERE match_id=?", (match_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "🗑️ **تم حذف المباراة وكافة توقعاتها المرتبطة بها نهائياً من النظام.**")
    show_admin_panel(message)

def process_broadcast(message):
    if not is_admin(message.from_user): return
    broadcast_text = message.text.strip() if message.text else ""
    if broadcast_text == "🔙 العودة للوحة التحكم":
        show_admin_panel(message)
        return
    if not broadcast_text:
        bot.send_message(message.chat.id, "❌ تم إلغاء الإذاعة بسبب إرسال نص فارغ.")
        show_admin_panel(message)
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
            
    bot.send_message(message.chat.id, f"📢 **تمت الإذاعة الجماعية بنجاح!**\n\n🟢 تسليم ناجح: `{success}`\n🔴 تعذر الإرسال: `{failed}`", parse_mode="Markdown")
    show_admin_panel(message)

# ==========================================
# 🛑 البوابة الموحدة والذكية لفرز مدخلات النص والتحكم بالحالات (Master Text Router)
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle_text_buttons(message):
    if not check_registration(message):
        return
        
    uid = message.from_user.id
    text = message.text.strip() if message.text else ""
    
    # 1. أوامر الملاحة العالمية الموحدة للإلغاء والعودة الفورية
    if text == "🔙 العودة للقائمة الرئيسية":
        show_main_menu(message)
        return
    elif text == "🔙 العودة للوحة التحكم" and is_admin(message.from_user):
        show_admin_panel(message)
        return
        
    # 2. فحص حالات جلسات المستخدمين (User States)
    if uid in USER_SESSION:
        state_data = USER_SESSION[uid]
        state = state_data.get('state')
        if state == 'predicting_score':
            process_user_score_input(message)
            return
        elif state == 'predicting_pen':
            process_user_penalties_input(message)
            return
        elif state == 'standings':
            if text == "➡️ الصفحة التالية":
                show_standings_page(message, page=state_data.get('page', 0) + 1)
                return
            elif text == "⬅️ الصفحة السابقة":
                show_standings_page(message, page=max(0, state_data.get('page', 0) - 1))
                return

    # 3. فحص حالات جلسات المشرفين (Admin States)
    if is_admin(message.from_user) and uid in ADMIN_SESSION:
        state_data = ADMIN_SESSION[uid]
        state = state_data.get('state')
        
        # معالج جدولة المباريات (Match Wizard Steps)
        if state == 'wizard_cat_h':
            if text in DATA_BANK:
                state_data['cat_h'] = text
                state_data['state'] = 'wizard_sub_h'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for s in DATA_BANK[text].keys(): markup.add(KeyboardButton(s))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"📁 اختر الفئة الفرعية / البطولة للمستضيف:", reply_markup=markup)
            return
        elif state == 'wizard_sub_h':
            cat = state_data['cat_h']
            if text in DATA_BANK.get(cat, {}):
                state_data['sub_h'] = text
                state_data['state'] = 'wizard_team_h'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for t in DATA_BANK[cat][text]: markup.add(KeyboardButton(t))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"🏠 اختر الفريق المستضيف:", reply_markup=markup)
            return
        elif state == 'wizard_team_h':
            cat = state_data['cat_h']
            sub = state_data['sub_h']
            if text in DATA_BANK.get(cat, {}).get(sub, []):
                state_data['home_team'] = text
                state_data['state'] = 'wizard_cat_a'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for c in DATA_BANK.keys(): markup.add(KeyboardButton(c))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"🗂️ **[الفريق الثاني - الضيف]** اختر التصنيف الأساسي له:", reply_markup=markup)
            return
        elif state == 'wizard_cat_a':
            if text in DATA_BANK:
                state_data['cat_a'] = text
                state_data['state'] = 'wizard_sub_a'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for s in DATA_BANK[text].keys(): markup.add(KeyboardButton(s))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"📁 اختر الفئة الفرعية / البطولة للضيف:", reply_markup=markup)
            return
        elif state == 'wizard_sub_a':
            cat = state_data['cat_a']
            if text in DATA_BANK.get(cat, {}):
                state_data['sub_a'] = text
                state_data['state'] = 'wizard_team_a'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for t in DATA_BANK[cat][text]:
                    if t != state_data.get('home_team'): markup.add(KeyboardButton(t))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"✈️ اختر فريق الضيف من القائمة:", reply_markup=markup)
            return
        elif state == 'wizard_team_a':
            cat = state_data['cat_a']
            sub = state_data['sub_a']
            if text in DATA_BANK.get(cat, {}).get(sub, []):
                state_data['away_team'] = text
                state_data['state'] = 'wizard_type'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                markup.add(KeyboardButton("📋 مباراة دوري عادية"), KeyboardButton("⚔️ خروج مغلوب (ترجيح)"))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"⚙️ اختر نوع ونظام الفرز المناسب للمباراة:", reply_markup=markup)
            return
        elif state == 'wizard_type':
            if text in ["📋 مباراة دوري عادية", "⚔️ خروج مغلوب (ترجيح)"]:
                state_data['match_type'] = text
                state_data['state'] = 'wizard_time'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                markup.add(KeyboardButton("⏱️ بعد ساعتين تلقائياً"))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"📆 أرسل تاريخ ووقت إغلاق التوقعات بالصيغة التالية تماماً:\n`YYYY-MM-DD HH:MM`\nمثال: `2026-07-25 18:30`", reply_markup=markup, parse_mode="Markdown")
            return
        elif state == 'wizard_time':
            process_admin_wizard_time(message)
            return
            
        # معالج إدخال النتيجة الرسمية
        elif state == 'settling_score':
            process_admin_settle_score(message)
            return
        elif state == 'settling_pen':
            process_admin_settle_penalties(message)
            return
            
        # معالج إدارة المشتركين
        elif state == 'users_list':
            if text == "➡️ تالي المنافسين":
                show_admin_users_page(message, page=state_data.get('page', 0) + 1)
                return
            elif text == "⬅️ سابق المنافسين":
                show_admin_users_page(message, page=max(0, state_data.get('page', 0) - 1))
                return
            user_match = re.match(r'^.* \(ID:(\d+)\)$', text)
            if user_match:
                target_uid = int(user_match.group(1))
                render_single_user_management(message, target_uid)
                return
        elif state == 'manage_user':
            target_uid = state_data['target_uid']
            if text == "✏️ تعديل اسم هذا المنافس":
                state_data['state'] = 'edit_user_name'
                bot.send_message(message.chat.id, "✍️ أرسل الآن الاسم الثلاثي الجديد بالكامل للمنافس:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 قائمة المنافسين")))
                return
            elif text == "💰 تعديل نقاط هذا المنافس":
                state_data['state'] = 'edit_user_pts'
                bot.send_message(message.chat.id, "🔢 أرسل القيمة العددية الإجمالية الجديدة للنقاط:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 قائمة المنافسين")))
                return
            elif text in ["🚫 تطبيق حظر الحساب", "🟢 إلغاء حظر الحساب"]:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT banned FROM users WHERE user_id=?", (target_uid,))
                res = cursor.fetchone()
                if res:
                    new_ban = 1 if res[0] == 0 else 0
                    cursor.execute("UPDATE users SET banned=? WHERE user_id=?", (new_ban, target_uid))
                    conn.commit()
                    bot.send_message(message.chat.id, "🚫 تم حظر المشترك!" if new_ban==1 else "🟢 تم إلغاء حظر المشترك!")
                conn.close()
                render_single_user_management(message, target_uid)
                return
            elif text == "🔙 قائمة المنافسين":
                show_admin_users_page(message, page=state_data.get('page', 0))
                return
        elif state == 'edit_user_name':
            if text == "🔙 قائمة المنافسين":
                render_single_user_management(message, state_data['target_uid'])
                return
            if len(text.split()) < 3:
                bot.send_message(message.chat.id, "❌ يرجى كتابة اسم ثلاثي صحيح:")
                return
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET full_name=? WHERE user_id=?", (text, state_data['target_uid']))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, "✅ تم تحديث اسم المنافس بنجاح.")
            render_single_user_management(message, state_data['target_uid'])
            return
        elif state == 'edit_user_pts':
            if text == "🔙 قائمة المنافسين":
                render_single_user_management(message, state_data['target_uid'])
                return
            if not text.isdigit() and not (text.startswith('-') and text[1:].isdigit()):
                bot.send_message(message.chat.id, "❌ أرسل قيمة رقمية فقط:")
                return
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points=? WHERE user_id=?", (int(text), state_data['target_uid']))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, "✅ تم تعديل رصيد النقاط بنجاح.")
            render_single_user_management(message, state_data['target_uid'])
            return

        # معالج إضافة بطولة جديدة
        elif state == 'add_tour_cat':
            if text in ["🏆 الدوريات والأندية", "🌍 القارات والمنتخبات"]:
                state_data['t_category'] = "الدوريات" if "الدوريات" in text else "القارات"
                state_data['state'] = 'add_tour_name'
                bot.send_message(message.chat.id, "✍️ أرسل اسم البطولة الجديدة (مثال: دوري أبطال آسيا):", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")))
            return
        elif state == 'add_tour_name':
            state_data['t_name'] = text
            state_data['state'] = 'add_tour_teams'
            bot.send_message(message.chat.id, "📋 أرسل أسماء الفرق التابعة لها، بحيث يكون كل فريق في **سطر منفصل**:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")))
            return
        elif state == 'add_tour_teams':
            teams = [t.strip() for t in re.split(r'[\n,]+', text) if t.strip()]
            if not teams:
                bot.send_message(message.chat.id, "❌ الرجاء إدخال فرق صحيحة:")
                return
            cat = state_data['t_category']
            tour_name = state_data['t_name']
            conn = get_db()
            cursor = conn.cursor()
            for team in teams:
                cursor.execute("INSERT INTO dynamic_teams (category, tournament_name, team_name) VALUES (?, ?, ?)", (cat, tour_name, team))
            conn.commit()
            conn.close()
            load_dynamic_tournaments()
            bot.send_message(message.chat.id, f"🏆 تم حفظ البطولة [{tour_name}] بنجاح مع {len(teams)} فريق!")
            show_admin_panel(message)
            return

        # معالج التعديلات على البنك والهيكل (CRUD Database)
        elif state == 'db_manage_cat':
            if text in ["🗂️ تصنيف: الدوريات والأندية", "🗂️ تصنيف: القارات والمنتخبات"]:
                cat_key = "الدوريات" if "الدوريات" in text else "القارات"
                state_data['cat'] = cat_key
                state_data['state'] = 'db_manage_tour'
                load_dynamic_tournaments()
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for tour in DATA_BANK.get(cat_key, {}).keys():
                    markup.add(KeyboardButton(f"🏆 بطولة: {tour}"))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"💼 تصفح مسابقات قسم [{cat_key}] ➖ اختر بطولة لإدارتها:", reply_markup=markup)
            return
        elif state == 'db_manage_tour':
            cat_key = state_data['cat']
            tour_match = re.match(r'^🏆 بطولة: (.*)$', text)
            if tour_match:
                tour_name = tour_match.group(1)
                state_data['tour'] = tour_name
                state_data['state'] = 'db_tour_ops'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                markup.add(KeyboardButton("✏️ تعديل اسم البطولة"), KeyboardButton("🗑️ حذف البطولة بالكامل"))
                markup.add(KeyboardButton("👟 إدارة فرق البطولة"), KeyboardButton("➕ إضافة فريق جديد للبطولة"))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"🏆 **إدارة مسار البطولة:** {tour_name}\nاختر الإجراء المطلوب:", reply_markup=markup)
            return
        elif state == 'db_tour_ops':
            tour_name = state_data['tour']
            cat_key = state_data['cat']
            if text == "✏️ تعديل اسم البطولة":
                state_data['state'] = 'db_rename_tour'
                bot.send_message(message.chat.id, f"✍️ أرسل الآن الاسم الجديد البديل لبطولة *{escape_markdown(tour_name)}*:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")))
                return
            elif text == "🗑️ حذف البطولة بالكامل":
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dynamic_teams WHERE category=? AND tournament_name=?", (cat_key, tour_name))
                cursor.execute("INSERT OR REPLACE INTO tournament_mods (category, old_name, new_name, status) VALUES (?, ?, ?, 'DELETED')", (cat_key, tour_name, ''))
                conn.commit()
                conn.close()
                load_dynamic_tournaments()
                bot.send_message(message.chat.id, "🗑️ تم مسح وإلغاء البطولة بالكامل من النظام.")
                show_admin_panel(message)
                return
            elif text == "➕ إضافة فريق جديد للبطولة":
                state_data['state'] = 'db_add_team_name'
                bot.send_message(message.chat.id, f"⚽ أرسل اسم الفريق الجديد لضمه إلى بطولة {tour_name}:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")))
                return
            elif text == "👟 إدارة فرق البطولة":
                state_data['state'] = 'db_manage_teams_list'
                load_dynamic_tournaments()
                teams_list = DATA_BANK.get(cat_key, {}).get(tour_name, [])
                if not teams_list:
                    bot.send_message(message.chat.id, "📭 لا توجد فرق في هذه البطولة حالياً.")
                    return
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                for tm in teams_list: markup.add(KeyboardButton(f"⚽ فريق: {tm}"))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"💡 قائمة فرق [{tour_name}] ➖ اختر فريقاً لإدارته أو حذفه:", reply_markup=markup)
                return
        elif state == 'db_rename_tour':
            cat_key = state_data['cat']
            old_name = state_data['tour']
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE dynamic_teams SET tournament_name=? WHERE category=? AND tournament_name=?", (text, cat_key, old_name))
            cursor.execute("INSERT OR REPLACE INTO tournament_mods (category, old_name, new_name, status) VALUES (?, ?, ?, 'ACTIVE')", (cat_key, old_name, text))
            cursor.execute("UPDATE team_mods SET tournament=? WHERE category=? AND tournament=?", (text, cat_key, old_name))
            conn.commit()
            conn.close()
            load_dynamic_tournaments()
            bot.send_message(message.chat.id, "✅ تم حفظ التعديل بنجاح لمسمى البطولة.")
            show_admin_panel(message)
            return
        elif state == 'db_add_team_name':
            cat_key = state_data['cat']
            tour_name = state_data['tour']
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dynamic_teams (category, tournament_name, team_name) VALUES (?, ?, ?)", (cat_key, tour_name, text))
            conn.commit()
            conn.close()
            load_dynamic_tournaments()
            bot.send_message(message.chat.id, f"✅ تم إضافة الفريق [{text}] وتثبيته في البنك.")
            show_admin_panel(message)
            return
        elif state == 'db_manage_teams_list':
            team_match = re.match(r'^⚽ فريق: (.*)$', text)
            if team_match:
                state_data['team'] = team_match.group(1)
                state_data['state'] = 'db_team_ops'
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                markup.add(KeyboardButton("✏️ تعديل اسم الفريق"), KeyboardButton("🗑️ حذف الفريق من البطولة"))
                markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
                bot.send_message(message.chat.id, f"⚽ **خيارات الكيان:** {state_data['team']}\nاختر الإجراء:", reply_markup=markup)
            return
        elif state == 'db_team_ops':
            cat_key = state_data['cat']
            tour_name = state_data['tour']
            team_name = state_data['team']
            if text == "✏️ تعديل اسم الفريق":
                state_data['state'] = 'db_rename_team'
                bot.send_message(message.chat.id, f"✍️ أرسل المسمى البديل الجديد للفريق *{escape_markdown(team_name)}*:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")))
                return
            elif text == "🗑️ حذف الفريق من البطولة":
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dynamic_teams WHERE category=? AND tournament_name=? AND team_name=?", (cat_key, tour_name, team_name))
                cursor.execute("INSERT OR REPLACE INTO team_mods (category, tournament, old_name, new_name, status) VALUES (?, ?, ?, '', 'DELETED')", (cat_key, tour_name, team_name))
                conn.commit()
                conn.close()
                load_dynamic_tournaments()
                bot.send_message(message.chat.id, "🗑️ تم سحب الفريق بنجاح من مسار المسابقة.")
                show_admin_panel(message)
                return
        elif state == 'db_rename_team':
            cat_key = state_data['cat']
            tour_name = state_data['tour']
            old_team = state_data['team']
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE dynamic_teams SET team_name=? WHERE category=? AND tournament_name=? AND team_name=?", (text, cat_key, tour_name, old_team))
            cursor.execute("INSERT OR REPLACE INTO team_mods (category, tournament, old_name, new_name, status) VALUES (?, ?, ?, ?, 'ACTIVE')", (cat_key, tour_name, old_team, text))
            conn.commit()
            conn.close()
            load_dynamic_tournaments()
            bot.send_message(message.chat.id, "✅ تم تغيير اسم الفريق بنجاح.")
            show_admin_panel(message)
            return

    # 4. معالجة القوائم الرئيسية وأزرار التوجيه المكتوبة
    if text == "🗳️ التوقعات المتاحة":
        show_available_matches(message)
    elif text == "📊 جدول الترتيب العام":
        show_standings_page(message, page=0)
    elif text == "🏆 مبارياتي الرابحة":
        show_winning_matches(message)
    elif text == "ℹ️ معلومات حسابي":
        show_my_info(message)
    elif text == "⚙️ لوحة تحكم المشرف" and is_admin(message.from_user):
        show_admin_panel(message)
        
    # خيارات المشرف
    elif is_admin(message.from_user):
        if text == "➕ إضافة وجدولة مباراة جديدة":
            ADMIN_SESSION[uid] = {'state': 'wizard_cat_h'}
            markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for c in DATA_BANK.keys(): markup.add(KeyboardButton(c))
            markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
            bot.send_message(message.chat.id, "🗂️ **[الفريق الأول - المستضيف]** اختر التصنيف الأساسي له:", reply_markup=markup)
        elif text == "🏆 إضافة بطولة جديدة ✨":
            ADMIN_SESSION[uid] = {'state': 'add_tour_cat'}
            markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(KeyboardButton("🏆 الدوريات والأندية"), KeyboardButton("🌍 القارات والمنتخبات"))
            markup.add(KeyboardButton("🔙 العودة للوحة التحكم"))
            bot.send_message(message.chat.id, "🗂️ اختر التصنيف المعتمد لتسجيل البطولة الجديدة:", reply_markup=markup)
        elif text == "🛠️ إدارة وحذف وتعديل البطولات والفرق":
            admin_manage_db_categories_text(message)
        elif text == "🏁 رصد نتيجة رسمية وحساب النقاط":
            admin_settle_list_text(message)
        elif text == "🗑️ حذف مباراة مرسلة بالكامل":
            admin_delete_list_text(message)
        elif text == "👥 إدارة المنافسين والتحكم بالحسابات":
            show_admin_users_page(message, page=0)
        elif text == "📢 إذاعة رسالة للمشتركين (Broadcast)":
            msg = bot.send_message(message.chat.id, "📢 أرسل الآن نص الرسالة المراد إذاعتها لجميع المشتركين:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("🔙 العودة للوحة التحكم")))
            bot.register_next_step_handler(msg, process_broadcast)
        elif text == "💾 تحميل نسخة احتياطية للبيانات (Backup)":
            try:
                with open("contest_master.db", "rb") as db_file:
                    db_data = db_file.read()
                bio = BytesIO(db_data)
                bio.name = f"backup_{datetime.now().strftime('%Y_%m_%d_%H%M%S')}.db"
                bot.send_document(message.chat.id, bio, caption="💾 نسخة احتياطية لقاعدة البيانات لجميع المشتركين.")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ حدث خطأ:\n`{str(e)}`")
            show_admin_panel(message)

    # 5. الالتقاط الذكي للمباريات المحددة عبر الأزرار
    match_pred = re.match(r'^⚽ .* \(ID:(\d+)\)$', text)
    if match_pred:
        user_prediction_flow_init(message, int(match_pred.group(1)))
        return
        
    match_settle = re.match(r'^🏁 رصد: .* \(ID:(\d+)\)$', text)
    if match_settle and is_admin(message.from_user):
        admin_settle_flow_init(message, int(match_settle.group(1)))
        return
        
    match_del = re.match(r'^🗑️ حذف: .* \(ID:(\d+)\)$', text)
    if match_del and is_admin(message.from_user):
        delete_match_completely(message, int(match_del.group(1)))
        return

# ==========================================
# 🌐 إعدادات الـ Webhook لـ PythonAnywhere
# ==========================================
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
