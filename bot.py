import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
from datetime import datetime, timedelta
import re

# التوكن وبيانات المشرف الصارمة
TOKEN = "8673575186:AAG2YvsMOxJu2Iw7Rr6oaiMeUdQVGMZuTHQ"
ADMIN_ID = 7394452907
ADMIN_USERNAME = "Aood71arf"

bot = telebot.TeleBot(TOKEN)

# بنك البيانات الكامل للمسابقات بعد تقسيم آسيا وأفريقيا
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
        "أوروبا 🇪🇺": ["ألبانيا🇦🇱", "أندورا🇦🇩", "أرمينيا🇦🇲", "النمسا🇦🇹", "أذربيجان🇦🇿", "بيلاروسيا🇧🇾", "بلجيكا🇧🇪", "البوسنة والهرسك🇧🇦", "بلغاريا🇧🇬", "كرواتيا🇭🇷", "قبرص🇨🇾", "جمهورية التشيك🇨🇿", "الدنمارك🇩🇰", "إنجلترا🇫🇴", "إستونيا🇪🇪", "جزر فارو🇫🇴", "فنلندا🇫🇮", "فرنسا🇫🇷", "جورجيا🇬🇪", "ألمانيا🇩🇪", "جبل طارق🇬🇮", "اليونان🇬رر", "المجر🇭🇺", "آيسلندا🇮🇸", "إسرائيل🇮🇱", "إيطاليا🇮🇹", "كازاخستان🇰🇿", "كوسوفو🇽🇰", "لاتفيا🇱🇻", "ليختنشتاين🇱🇮", "ليتوانيا🇱🇹", "لوكسمبورغ🇱🇺", "مالطا🇲🇹", "مولدوفا🇲🇩", "الجبل الأسود🇲🇪", "هولندا🇳🇱", "مقدونيا الشمالية🇲🇰", "أيرلندا الشمالية🇬🇧", "النرويج🇳🇴", "بولندا🇵🇱", "البرتغال🇵🇹", "جمهورية أيرلندا🇮🇪", "رومانيا🇷🇴", "روسيا🇷🇺", "سان مارينو🇸🇲", "اسكتلندا 🏴󠁧󠁢󠁳󠁣󠁴󠁿", "صربيا🇷🇸", "سلوفاكيا🇸🇰", "سلوفينيا🇸🇮", "إسبانيا🇪🇸", "السويد🇸🇪", "سويسرا🇨🇭", "تركيا🇹🇷", "أوكرانيا🇺🇦", "ويلز 🏴󠁧󠁢󠁷󠁬󠁳󠁿"],
        "أمريكا الجنوبية 🇦رج": ["الأرجنتين🇦🇷", "بوليفيا🇧🇴", "البرازيل🇧🇷", "تشيلي🇨🇱", "كولومبيا🇨🇴", "الإكوادور🇪🇨", "باراغواي🇵🇾", "بيرو🇵🇪", "أوروغواي🇺🇾", "فنزويلا🇻🇪"],
        "أفريقيا (قسم شمالي) 🦅": ["الجزائر🇩🇿", "مصر🇪🇬", "ليبيا🇱🇾", "المغرب🇲🇦", "موريتانيا🇲🇷", "تشاد🇹🇩", "مالي🇲🇱", "النيجر🇿🇼", "بوركينا فاسو🇧🇫"],
        "أفريقيا (قسم جنوبي) 🦁": ["أنغولا🇦🇴", "بنين🇧🇯", "بوتسوانا🇧🇼", "بوروندي🇧🇮", "الرأس الأخضر🇨🇻", "الكاميرون🇨🇲", "جمهورية أفريقيا الوسطى🇨🇫", "جزر القمر🇰🇲", "الكونغو🇨🇬", "جمهورية الكونغو الديمقراطية🇨🇩", "غينيا الاستوائية🇬🇶", "إريتريا🇪🇷", "إسواتيني🇸🇿", "إثيوبيا🇪🇹", "الغابون🇬🇦", "غامبيا🇬🇲", "غانا🇬🇭", "غينيا🇬🇳", "غينيا بيساو🇬🇼", "ساحل العاج🇨🇮", "كينيا🇰🇪", "ليسوتو🇱🇸", "ليبيريا🇱🇷", "مدغشقر🇲🇬", "مالاوي🇲🇼", "موريشيوس🇲🇺", "موزمبيق🇲🇿", "ناميبيا🇳🇦"],
        "أوقيانوسيا 🇳🇿": ["نيوزيلندا🇳🇿", "جزر سليمان🇸🇧", "تاهيتي🇵🇫", "فانواتو🇻🇺", "كاليدونيا الجديدة🇳🇨", "بابوا غينيا الجديدة🇵🇬", "فيجي 🇫ジム", "ساموا🇼🇸", "ساموا الأمريكية🇦🇸", "تونغا🇹🇴", "جزر كوك🇨🇰"],
        "أمريكا الشمالية 🇺🇸": ["الولايات المتحدة🇺🇸", "المكسيك🇲🇽", "كندا🇨🇦", "بنما🇵🇦", "كوستاريكا🇨🇷", "هندوراس🇭🇳", "جامايكا🇯🇲", "السلفادور🇸🇻", "غواتيمالا🇬🇹", "هايتي🇭🇹", "كوراساو🇨🇼", "ترينيداد وتوباغو🇹🇹", "نيكاراغوا🇳🇮", "سورينام🇸🇷"]
    }
}

ADMIN_SESSION = {}
USER_SESSION = {}

def is_admin(user):
    return user.id == ADMIN_ID or user.username == ADMIN_USERNAME

def init_db():
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY, 
                        username TEXT, 
                        full_name TEXT, 
                        phone_number TEXT,
                        points INTEGER DEFAULT 0)''')
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
                        category TEXT,
                        tournament_name TEXT,
                        team_name TEXT)''')
    
    try: cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE matches ADD COLUMN home_score INTEGER")
        cursor.execute("ALTER TABLE matches ADD COLUMN away_score INTEGER")
        cursor.execute("ALTER TABLE matches ADD COLUMN pen_home_score INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE matches ADD COLUMN pen_away_score INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    conn.commit()
    conn.close()

def load_dynamic_tournaments():
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT category, tournament_name, team_name FROM dynamic_teams")
        rows = cursor.fetchall()
        for cat, tour_name, team_name in rows:
            if cat in DATA_BANK:
                if tour_name not in DATA_BANK[cat]:
                    DATA_BANK[cat][tour_name] = []
                if team_name not in DATA_BANK[cat][tour_name]:
                    DATA_BANK[cat][tour_name].append(team_name)
    except sqlite3.OperationalError:
        pass
    conn.close()

init_db()
load_dynamic_tournaments()

def check_registration(message):
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, phone_number FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()
    
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
    msg = bot.send_message(message.chat.id, f"🎯 أهلاً بك *{name_text}*.\nالآن يرجى إرسال **رقم هاتفك المكون من 9 أرقام فقط** ليكون هو المعرّف الخاص بك في قاعدة البيانات:")
    bot.register_next_step_handler(msg, register_user_phone)

def register_user_phone(message):
    phone_text = message.text.strip() if message.text else ""
    if not phone_text.isdigit() or len(phone_text) != 9:
        msg = bot.send_message(message.chat.id, "❌ خطأ في التنسيق! يرجى إرسال رقم هاتف مكون من **9 أرقام فقط** (مثال: 777123456):")
        bot.register_next_step_handler(msg, register_user_phone)
        return
    
    uid = message.from_user.id
    full_name = USER_SESSION.get(uid, {}).get("reg_name", "مستخدم جديد")
    
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, username, full_name, phone_number, points) VALUES (?, ?, ?, ?, 0)",
                   (uid, message.from_user.username, full_name, phone_text))
    conn.commit()
    conn.close()
    
    if uid in USER_SESSION:
        del USER_SESSION[uid]
        
    bot.send_message(message.chat.id, f"✅ تم تسجيلك بنجاح!\n📝 الاسم الثلاثي: *{full_name}*\n🆔 معرّفك المحجوز (الهاتف): `{phone_text}`")
    
    points_explanation = (
        "💡 **كيف تحصل على النقاط؟**\n\n"
        "النقاط تُجمع. كل جزء صحيح من توقعك يمنحك نقاطاً — الفائز/التعادل، النتيجة الدقيقة، وركلات الترجيح تُحتسب كل على حدة:\n\n"
        "🟢 **+5 نقاط** ➖ إذا توقعت الفائز أو التعادل بشكل صحيح.\n\n"
        "🟢 **+15 نقطة** ➖ تُضاف إلى نقاط الفائز/التعادل عند توقع نتيجة المباراة بدقة.\n\n"
        "🔵 **+10 نقاط** ➖ في مباراة خروج مغلوب ذهبت إلى ركلات الترجيح، إذا توقعت فائز ركلات الترجيح بشكل صحيح. تُحتسب حتى لو لم تكن نتيجة المباراة دقيقة، طالما أن الفائز أو التعادل صحيح.\n\n"
        "🔵 **+15 نقطة** ➖ في مباراة خروج مغلوب ذهبت إلى ركلات الترجيح، إذا توقعت نتيجة ركلات الترجيح بدقة. تُحتسب حتى لو لم تكن نتيجة المباراة دقيقة. عند إدخال نتيجة ركلات الترجيح، يُحتسب فائز الركلات تلقائياً.\n\n"
        "🔥 **+30 نقطة** ➖ مكافأة إضافية عند توقع نتيجة المباراة وركلات الترجيح بدقة معاً.\n\n"
        "🔴 **0 نقاط** ➖ إذا كان توقعك للفائز أو التعادل خاطئاً."
    )
    bot.send_message(message.chat.id, points_explanation, parse_mode="Markdown")
    
    show_main_menu(message)

def show_main_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🗳️ التوقعات المتاحة"), KeyboardButton("📊 جدول الترتيب العام"))
    markup.add(KeyboardButton("🏆 مبارياتي الرابحة"), KeyboardButton("ℹ️ معلومات حسابي"))
    
    if is_admin(message.from_user):
        markup.add(KeyboardButton("⚙️ لوحة تحكم المشرف"))
        
    bot.send_message(message.chat.id, "📊 أهلاً بك في الواجهة الرئيسية للمسابقة. يرجى اختيار الإجراء من الأزرار بالأسفل:", reply_markup=markup)

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
        show_standings(message)
    elif message.text == "🏆 مبارياتي الرابحة":
        show_winning_matches(message)
    elif message.text == "ℹ️ معلومات حسابي":
        show_my_info(message)
    elif message.text == "⚙️ لوحة تحكم المشرف" and is_admin(message.from_user):
        show_admin_panel(message)

def show_available_matches(message):
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, category, sub_category, home_team, away_team, start_time, match_type FROM matches WHERE status='ACTIVE'")
    matches = cursor.fetchall()
    
    if not matches:
        bot.send_message(message.chat.id, "📭 لا توجد مباريات نشطة أو متاحة للتوقع حالياً.")
        conn.close()
        return
        
    markup = InlineKeyboardMarkup(row_width=1)
    now = datetime.now()
    
    for m in matches:
        match_id, cat, sub_cat, home, away, s_time, m_type = m
        match_dt = datetime.strptime(s_time, "%Y-%m-%d %H:%M")
        
        cursor.execute("SELECT home_pred, away_pred FROM predictions WHERE user_id=? AND match_id=?", (message.from_user.id, match_id))
        pred = cursor.fetchone()
        
        if now < match_dt:
            if pred:
                btn_text = f"✏️ تعديل: {home} [{pred[0]}-{pred[1]}] {away}"
            else:
                btn_text = f"⚽ توقع: {home} × {away}"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"usr_pred_{match_id}"))
            
    bot.send_message(message.chat.id, "🏟️ المباريات المتاحة للتوقع (يمكنك التعديل حتى موعد انطلاق المباراة الرسمي):", reply_markup=markup)
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("usr_pred_"))
def user_prediction_interface(call):
    match_id = int(call.data.split("_")[2])
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team, match_type, start_time FROM matches WHERE match_id=?", (match_id,))
    match = cursor.fetchone()
    
    if not match:
        bot.answer_callback_query(call.id, "المباراة غير موجودة.")
        conn.close()
        return
        
    home, away, m_type, s_time = match
    if datetime.now() > datetime.strptime(s_time, "%Y-%m-%d %H:%M"):
        bot.answer_callback_query(call.id, "🔒 عذراً، بدأت المباراة وتم إغلاق استقبال أو تعديل التوقعات تلقائياً!")
        conn.close()
        return

    cursor.execute("SELECT home_pred, away_pred, pen_home_pred, pen_away_pred FROM predictions WHERE user_id=? AND match_id=?", (call.from_user.id, match_id))
    current_pred = cursor.fetchone()
    conn.close()
    
    if current_pred:
        hp, ap, php, pap = current_pred
    else:
        hp, ap, php, pap = 0, 0, 0, 0
        
    USER_SESSION[call.from_user.id] = {"match_id": match_id, "hp": hp, "ap": ap, "php": php, "pap": pap, "type": m_type}
    render_prediction_keyboard(call.message, call.from_user.id, home, away)

def render_prediction_keyboard(message, user_id, home, away):
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
    
    if data['type'] == "خروج مغلوب (ترجيح)":
        markup.row(InlineKeyboardButton("🌟 توقع ركلات الترجيح 🌟", callback_data="none"))
        markup.row(
            InlineKeyboardButton(f"➕ ركلات {home}", callback_data="u_inc_ph"),
            InlineKeyboardButton(f"🥅 {data['php']} - {data['pap']} 🥅", callback_data="none"),
            InlineKeyboardButton(f"➕ ركلات {away}", callback_data="u_inc_pa")
        )
        markup.row(
            InlineKeyboardButton(f"➖ {home}", callback_data="u_dec_ph"),
            InlineKeyboardButton(f"➖ {away}", callback_data="u_dec_pa")
        )
        
    markup.row(InlineKeyboardButton("💾 حفظ وتثبيت التوقع الآن ✅", callback_data="u_save_pred"))
    
    bot.edit_message_text(f"🎯 **تحديد توقع مباراة:**\n🏟️ {home} × {away}\nقم باستخدام الأزرار لضبط النتيجة المتوقعة بالكامل:", 
                          message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("u_"))
def handle_user_adjustments(call):
    user_id = call.from_user.id
    if user_id not in USER_SESSION:
        bot.answer_callback_query(call.id, "انتهت الجلسة، الرجاء الضغط مجدداً.")
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
        conn = sqlite3.connect('contest_master.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO predictions (user_id, match_id, home_pred, away_pred, pen_home_pred, pen_away_pred) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, data['match_id'], data['hp'], data['ap'], data['php'], data['pap']))
        conn.commit()
        conn.close()
        bot.edit_message_text("✅ **تم حفظ وتحديث توقعك بنجاح!**\nتم تسجيل وحجز النتيجة في قاعدة البيانات وسيتم احتساب النقاط فور نهاية اللقاء الحقيقي.", call.message.chat.id, call.message.message_id)
        del USER_SESSION[user_id]
        return
        
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT home_team, away_team FROM matches WHERE match_id=?", (data['match_id'],))
    home, away = cursor.fetchone()
    conn.close()
    render_prediction_keyboard(call.message, user_id, home, away)

def show_standings(message):
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, points FROM users ORDER BY points DESC LIMIT 300")
    players = cursor.fetchall()
    conn.close()
    
    if not players:
        bot.send_message(message.chat.id, "📊 جدول الترتيب خالي حالياً.")
        return
        
    text = "🏆 **جدول الترتيب العام للمنافسين (تحديث أوتوماتيكي):**\n\n"
    for idx, player in enumerate(players, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"🏅 {idx}."
        text += f"{medal} {player[0]} ➖ `{player[1]}` نقطة\n"
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def show_winning_matches(message):
    conn = sqlite3.connect('contest_master.db')
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
        
    winning_text = "🏆 **سجل المباريات التي حصدت منها نقاطاً رابحة:**\n\n"
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
        else:
            if m_type != "خروج مغلوب (ترجيح)" or real_outcome != "DRAW":
                pts = 0
                
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
                
            winning_text += f"⚽ **{home} × {away}**\n" \
                            f"🏁 النتيجة الرسمية: `{score_str}`\n" \
                            f"🗳️ توقعك المسجل: `{pred_str}`\n" \
                            f"💰 النقاط المكتسبة: *+{pts}* نقطة\n" \
                            f"───────────────────\n"
                            
    if not has_winning:
        bot.send_message(message.chat.id, "ℹ️ لم تحقيق أي نقاط رابحة في المباريات التي تم رصدها حتى الآن.")
    else:
        bot.send_message(message.chat.id, winning_text, parse_mode="Markdown")

def show_my_info(message):
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, phone_number, points FROM users WHERE user_id=?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()
    
    full_name = user[0] if user else message.from_user.first_name
    phone_number = user[1] if user else "غير مسجل"
    points = user[2] if user else 0
    
    text = f"👤 **معلومات بطاقتك والمحرّف الخاص بك:**\n\n" \
           f"📝 الاسم الثلاثي: *{full_name}*\n" \
           f"🆔 المعرّف الرقمي المحجوز (الهاتف): `{phone_number}`\n" \
           f"💰 مجموع نقاطك الحالية: *{points}* نقطة"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def render_admin_panel_view(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة وجدولة مباراة جديدة", callback_data="adm_add_match"),
        InlineKeyboardButton("🏆 إضافة بطولة جديدة ✨", callback_data="adm_add_tournament"),
        InlineKeyboardButton("🏁 رصد نتيجة رسمية وحساب النقاط", callback_data="adm_settle_list"),
        InlineKeyboardButton("🗑️ حذف مباراة مرسلة بالكامل", callback_data="adm_delete_list")
    )
    bot.edit_message_text("⚙️ **لوحة التحكم الشاملة لمدير المنظومة:**", message.chat.id, message.message_id, reply_markup=markup)

def show_admin_panel(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة وجدولة مباراة جديدة", callback_data="adm_add_match"),
        InlineKeyboardButton("🏆 إضافة بطولة جديدة ✨", callback_data="adm_add_tournament"),
        InlineKeyboardButton("🏁 رصد نتيجة رسمية وحساب النقاط", callback_data="adm_settle_list"),
        InlineKeyboardButton("🗑️ حذف مباراة مرسلة بالكامل", callback_data="adm_delete_list")
    )
    bot.send_message(message.chat.id, "⚙️ **لوحة التحكم الشاملة لمدير المنظومة:**", reply_markup=markup)

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
        
    elif action == "adm_settle_list":
        conn = sqlite3.connect('contest_master.db')
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
        bot.edit_message_text("🏟️ اختر المباراة التي انتهت لإدخل النتيجة الرسمية وحساب النقاط تلقائياً للجميع:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif action == "adm_delete_list":
        conn = sqlite3.connect('contest_master.db')
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
        bot.edit_message_text("⚠️ اختر المباراة المراد حذفها نهائياً وإلغاء كافة التوقعات التابعة لها:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_cat_"))
def handle_tournament_category(call):
    if not is_admin(call.from_user): return
    uid = call.from_user.id
    if uid not in ADMIN_SESSION: ADMIN_SESSION[uid] = {}
    
    ADMIN_SESSION[uid]["t_category"] = call.data.replace("t_cat_", "")
    msg = bot.edit_message_text("✍️ **[خطوة 2 من 3]** أرسل الآن **اسم البطولة الجديدة** (مثال: دوري أبطال آسيا):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, process_tournament_name)

def process_tournament_name(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION:
        show_admin_panel(message)
        return
        
    tour_name = message.text.strip() if message.text else ""
    if not tour_name:
        msg = bot.send_message(message.chat.id, "❌ اسم غير صالح، يرجى إرسال اسم نصي للبطولة:")
        bot.register_next_step_handler(msg, process_tournament_name)
        return
        
    ADMIN_SESSION[uid]["t_name"] = tour_name
    
    msg = bot.send_message(message.chat.id, f"⚽ تم اعتماد اسم البطولة: *{tour_name}*\n\n"
                                           f"📋 **[خطوة 3 من 3]** قم الآن بإرسال **أسماء الفرق أو الأندية** التابعة لها.\n"
                                           f"⚠️ **ملاحظة هامة جداً:** يرجى كتابة كل فريق في **سطر منفصل** أو الفصل بينهم بـ **فاصلة (,)**\n\n"
                                           f"مثال:\nبرشلونة\nريال مدريد\nليفربول", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_tournament_teams)

def process_tournament_teams(message):
    uid = message.from_user.id
    if uid not in ADMIN_SESSION or "t_name" not in ADMIN_SESSION[uid]:
        show_admin_panel(message)
        return
        
    text = message.text.strip() if message.text else ""
    if not text:
        msg = bot.send_message(message.chat.id, "❌ لم تقم بإدخال أي فرق! يرجى إرسال أسماء الفرق مجدداً:")
        bot.register_next_step_handler(msg, process_tournament_teams)
        return
        
    teams = [t.strip() for t in re.split(r'[\n,]+', text) if t.strip()]
    
    if not teams:
        msg = bot.send_message(message.chat.id, "❌ عذراً لم يتم التعرف على الفرق، اكتبها سطراً بسطر:")
        bot.register_next_step_handler(msg, process_tournament_teams)
        return
        
    cat = ADMIN_SESSION[uid]["t_category"]
    tour_name = ADMIN_SESSION[uid]["t_name"]
    
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    for team in teams:
        cursor.execute("INSERT INTO dynamic_teams (category, tournament_name, team_name) VALUES (?, ?, ?)", (cat, tour_name, team))
    conn.commit()
    conn.close()
    
    load_dynamic_tournaments()
    
    bot.send_message(message.chat.id, f"🏆 **تمت إضافة البطولة بنجاح!**\n\n"
                                      f"🗂️ التصنيف العام: *{cat}*\n"
                                      f"🥇 اسم البطولة: *{tour_name}*\n"
                                      f"👥 عدد الفرق المدرجة: `{len(teams)}` فريق/منتخب.\n\n"
                                      f"💡 يمكنك الآن الدخول لقسم (إضافة وجدولة مباراة جديدة) وجدولة لقاءاتهم فوراً!", parse_mode="Markdown")
    
    if uid in ADMIN_SESSION:
        del ADMIN_SESSION[uid]
    show_main_menu(message)

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
    bot.edit_message_text(f"📁 **[الفريق الأول]** تصنيف *{cat}* ➖ اختر الفئة الفرعية:", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

def render_home_team_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_h"]
    sub = ADMIN_SESSION[uid]["sub_category_h"]
    markup = InlineKeyboardMarkup(row_width=2)
    for idx, team in enumerate(DATA_BANK[cat][sub]):
        markup.add(InlineKeyboardButton(team, callback_data=f"ax_sht_{idx}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_hsub"))
    bot.edit_message_text(f"🏠 **[الفريق الأول]** اختر الفريق أو المنتخب الأول (المستضيف) من فئة *{sub}*:", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

def render_away_cat_selection(message, uid):
    home_team = ADMIN_SESSION[uid]["home_team"]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏆 الدوريات والأندية", callback_data="ax_sac_الدوريات"),
               InlineKeyboardButton("🌍 القارات والمنتخبات", callback_data="ax_sac_القارات"))
    markup.add(InlineKeyboardButton("🔙 عودة لتغيير الفريق الأول", callback_data="ax_b_hteam"))
    bot.edit_message_text(f"🗂️ **[الفريق الثاني - الضيف]** اختر تصنيفه الآن\n💡 (الفريق الأول الحالي: *{home_team}*):", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

def render_away_sub_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_a"]
    markup = InlineKeyboardMarkup(row_width=2)
    for sub in DATA_BANK[cat].keys():
        markup.add(InlineKeyboardButton(sub, callback_data=f"ax_sas_{sub}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_acat"))
    bot.edit_message_text(f"📁 **[الفريق الثاني]** تصنيف *{cat}* ➖ اختر الفئة الفرعية للضيف:", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

def render_away_team_selection(message, uid):
    cat = ADMIN_SESSION[uid]["category_a"]
    sub = ADMIN_SESSION[uid]["sub_category_a"]
    home_team = ADMIN_SESSION[uid]["home_team"]
    markup = InlineKeyboardMarkup(row_width=2)
    for idx, team in enumerate(DATA_BANK[cat][sub]):
        if team != home_team:  
            markup.add(InlineKeyboardButton(team, callback_data=f"ax_sat_{idx}"))
    markup.add(InlineKeyboardButton("🔙 عودة للخلف", callback_data="ax_b_asub"))
    bot.edit_message_text(f"✈️ **[الفريق الثاني]** اختر الفريق أو المنتخب الثاني (الضيف) من فئة *{sub}*:", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

def render_match_type_selection(message, uid):
    home = ADMIN_SESSION[uid]["home_team"]
    away = ADMIN_SESSION[uid]["away_team"]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📋 مباراة دوري عادية", callback_data="ax_st_مباراة عادية"),
               InlineKeyboardButton("⚔️ خروج مغلوب (ترجيح)", callback_data="ax_st_خروج مغلوب (ترجيح)"))
    markup.add(InlineKeyboardButton("🔙 عودة لتغيير الفريق الثاني", callback_data="ax_b_ateam"))
    bot.edit_message_text(f"⚙️ **تحديد نظام الفرز الحسابي والاتحادي:**\n🏟️ المباراة المكونة: *{home}* × *{away}*\nاختر نوع ونظام النقاط المعتمد:", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

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
    
    bot.edit_message_text(f"📆 **ضبط الوقت والتاريخ للمباراة أوتوماتيكياً بالأزرار اليدوية:**\n\n🏟️ المباراة: {data['home_team']} × {data['away_team']}\n⏱️ تاريخ الإغلاق المحدد حالياً: `{current_set_time}`", message.chat.id, message.message_id, reply_markup=markup, parse_mode="Markdown")

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
        render_home_team_selection(call.message, uid)
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
        
        if data['category_h'] == data['category_a']:
            cat_str = data['category_h']
        else:
            cat_str = f"{data['category_h']} - {data['category_a']}"
            
        if data['sub_category_h'] == data['sub_category_a']:
            sub_cat_str = data['sub_category_h']
        else:
            sub_cat_str = f"{data['sub_category_h']} × {data['sub_category_a']}"
        
        conn = sqlite3.connect('contest_master.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO matches (category, sub_category, home_team, away_team, match_type, start_time) VALUES (?, ?, ?, ?, ?, ?)",
                       (cat_str, sub_cat_str, data['home_team'], data['away_team'], data['match_type'], time_str))
        conn.commit()
        conn.close()
        bot.edit_message_text(f"🚀 **تم جدولة ونشر المباراة بنجاح!**\nالمباراة: {data['home_team']} × {data['away_team']}\n⏱️ تاريخ الإغلاق: {time_str}", call.message.chat.id, call.message.message_id)
        del ADMIN_SESSION[admin_id]
        return
    render_time_adjustment_view(call.message, admin_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("as_"))
def admin_settle_interface(call):
    if not is_admin(call.from_user): return
    parts = call.data.split("_")
    match_id = int(parts[2])
    conn = sqlite3.connect('contest_master.db')
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
            InlineKeyboardButton(f"➖ {data['away']}", callback_data="s_dec_pa")
        )
    markup.row(InlineKeyboardButton("🏁 اعتماد النتيجة الرسمية وضخ النقاط 🚀", callback_data="s_finalize"))
    bot.edit_message_text(f"⚽ **إدخال النتيجة الرسمية النهائية:**\n🏟️ {data['home']} × {data['away']}\nاستخدم الأزرار لضبط النتيجة الحقيقية بدقة لفرز الفائزين تلقائياً:", message.chat.id, message.message_id, reply_markup=markup)

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
        real_pen_home = data['php']
        real_pen_away = data['pap']
        
        real_outcome = "HOME" if real_home_score > real_away_score else "AWAY" if real_away_score > real_home_score else "DRAW"
        
        conn = sqlite3.connect('contest_master.db')
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
            if not full_name:
                full_name = "مستخدم غير مسجل الاسم"
                
            calculated_points = 0
            u_outcome = "HOME" if u_hp > u_ap else "AWAY" if u_ap > u_hp else "DRAW"
            
            exact_match_score = False
            if u_outcome == real_outcome:
                calculated_points += 5
                if u_hp == real_home_score and u_ap == real_away_score:
                    calculated_points += 15
                    exact_match_score = True
            else:
                if data['type'] != "خروج مغلوب (ترجيح)" or real_outcome != "DRAW":
                    calculated_points = 0
                    
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
            report_lines.append(f"👤 {full_name} ➖ توقع: `{pred_str}` ➖ كسب: *+{calculated_points}* ن")
            
        cursor.execute("UPDATE matches SET status='FINISHED', home_score=?, away_score=?, pen_home_score=?, pen_away_score=? WHERE match_id=?", 
                       (real_home_score, real_away_score, real_pen_home, real_pen_away, match_id))
        conn.commit()
        conn.close()
        
        match_title = f"{data['home']} × {data['away']}"
        score_str = f"[{real_home_score} - {real_away_score}]"
        if data['type'] == "خروج مغلوب (ترجيح)" and real_outcome == "DRAW":
            score_str += f" (ركلات ترجيح: {real_pen_home}-{real_pen_away})"
            
        bot.edit_message_text(f"🎉 **تم حسم ورصد المباراة بنجاح!**\nتم تحديث الأرشيف وضخ نقاط كافة المتسابقين تلقائياً.", call.message.chat.id, call.message.message_id)
        
        report_header = f"📊 **تقرير توقعات المنافسين للمباراة:**\n⚽ {match_title}\n🏁 النتيجة الرسمية: `{score_str}`\n───────────────────\n"
        
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
                
        del ADMIN_SESSION[admin_id]
        return
    render_admin_settle_keyboard(call.message, admin_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ad_del_"))
def delete_match_completely(call):
    if not is_admin(call.from_user): return
    match_id = int(call.data.split("_")[2])
    conn = sqlite3.connect('contest_master.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM matches WHERE match_id=?", (match_id,))
    cursor.execute("DELETE FROM predictions WHERE match_id=?", (match_id,))
    conn.commit()
    conn.close()
    bot.edit_message_text("🗑️ **تم حذف المباراة وإلغاء كافة التوقعات المسجلة لها من النظام فوراً.**", call.message.chat.id, call.message.message_id)

if __name__ == '__main__':
    bot.infinity_polling(skip_pending=True)
