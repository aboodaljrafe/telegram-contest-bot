import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from database.connection import get_db
from database.models import User, Match, Prediction
from services.bank import bank

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# لوحات التحكم بالأزرار (Keyboards)
# ---------------------------------------------------------

def get_main_keyboard():
    """لوحة التحكم الرئيسية بالأزرار الثابتة"""
    keyboard = [
        [KeyboardButton("⚽ مباريات اليوم والتوقعات"), KeyboardButton("🔴 المباريات المباشرة")],
        [KeyboardButton("📊 رصيدي وتوقعاتي"), KeyboardButton("🏆 جدول الترتيب")],
        [KeyboardButton("🔄 تحديث البيانات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ---------------------------------------------------------
# معالجات الأوامر والرسائل الأساسية
# ---------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل المستخدم وإظهار القائمة الرئيسية"""
    tg_user = update.effective_user

    with get_db() as db:
        user = db.query(User).filter(User.id == tg_user.id).first()
        if not user:
            user = User(
                id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name or "مشترك"
            )
            db.add(user)

    welcome_text = (
        f"أهلاً بك يا <b>{tg_user.first_name}</b> في بوت التوقعات والإحصائيات الكروية! 🏆⚽\n\n"
        "من خلال اللوحة في الأسفل، يمكنك:\n"
        "• التوقع للمباريات القادمة وكسب النقاط.\n"
        "• متابعة نتائج وإحصائيات المباريات المباشرة فورياً.\n"
        "• منافسة المشتركين في جدول الترتيب.\n\n"
        "اختر من الأزرار بالأسفل للبدء 👇"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


async def refresh_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """زر تحديث البيانات اليدوي"""
    msg = await update.message.reply_text("⏳ جاري تحديث بيانات المباريات والنتائج المباشرة...")
    
    # تحديث المباريات المباشرة ومباريات اليوم من الـ API
    bank.sync_todays_matches()
    bank.sync_live_matches()
    
    await msg.edit_text("✅ تم تحديث البيانات بنجاح! اختر القائمة التي تريد استعراضها.")


async def todays_matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استعراض مباريات اليوم مع أزرار التوقع والتفاصيل"""
    bank.sync_todays_matches()
    
    with get_db() as db:
        matches = db.query(Match).filter(
            Match.status.in_(["NS", "1H", "HT", "2H", "ET", "PEN", "FT"])
        ).order_by(Match.match_date.asc()).all()

        if not matches:
            await update.message.reply_text(
                "📅 لا توجد مباريات مسجلة لهذا اليوم حتى الآن. اضغط على 🔄 تحديث البيانات.",
                reply_markup=get_main_keyboard()
            )
            return

        text = "⚽ <b>مباريات اليوم والتوقعات:</b>\n\n"
        keyboard = []

        for m in matches:
            match_time = m.match_date.strftime("%H:%M UTC")
            status_symbol = "🟢 جارِ" if m.status in ["1H", "HT", "2H", "ET"] else ("🔴 انتهت" if m.status == "FT" else "⏳ لم تبدأ")
            
            score_str = f"[{m.home_score} - {m.away_score}]" if m.home_score is not None else "vs"
            text += f"🔹 <b>{m.league_name}</b>\n"
            text += f"⚔️ {m.home_team} {score_str} {m.away_team}\n"
            text += f"⏰ التوقيت: {match_time} | الحالة: {status_symbol}\n"
            text += "-----------------------------------\n"

            # إظهار زر التوقع فقط للمباريات التي لم تبدأ بعد
            if m.status == "NS":
                keyboard.append([InlineKeyboardButton(f"🎯 توقع: {m.home_team} vs {m.away_team}", callback_data=f"pred_select_{m.id}")])
            else:
                keyboard.append([InlineKeyboardButton(f"📊 إحصائيات: {m.home_team} vs {m.away_team}", callback_data=f"stats_{m.id}")])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def live_matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استعراض المباريات المباشرة حالياً"""
    bank.sync_live_matches()

    with get_db() as db:
        live_matches = db.query(Match).filter(
            Match.status.in_(["1H", "HT", "2H", "ET", "P", "LIVE"])
        ).all()

        if not live_matches:
            await update.message.reply_text(
                "🔴 لا توجد مباريات جارية في الوقت الحالي.",
                reply_markup=get_main_keyboard()
            )
            return

        text = "🔥 <b>المباريات الجارية حالياً:</b>\n\n"
        keyboard = []
        for m in live_matches:
            home_s = m.home_score if m.home_score is not None else 0
            away_s = m.away_score if m.away_score is not None else 0
            text += f"🏆 {m.league_name}\n"
            text += f"⚽ <b>{m.home_team}</b> {home_s} - {away_s} <b>{m.away_team}</b>\n"
            text += f"⏱️ الحالة: {m.status}\n\n"

            keyboard.append([InlineKeyboardButton(f"📊 إحصائيات {m.home_team} vs {m.away_team}", callback_data=f"stats_{m.id}")])

        keyboard.append([InlineKeyboardButton("🔄 تحديث المباشر", callback_data="refresh_live")])
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def user_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رصيد وتوقعات المشترك"""
    user_id = update.effective_user.id
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()

        if not user:
            await update.message.reply_text("عذراً، لم يتم العثور على حسابك. يرجى إرسال /start.")
            return

        profile_text = (
            f"👤 <b>الملف الشخصي:</b> {user.full_name}\n"
            f"💎 <b>مجموع النقاط:</b> {user.points} نقطة\n"
            f"🎯 <b>التوقعات الصحيحة بالكامل:</b> {user.correct_predictions}\n"
            f"📝 <b>إجمالي التوقعات:</b> {user.total_predictions}\n\n"
            "📋 <b>آخر التوقعات:</b>\n"
        )

        if not predictions:
            profile_text += "لم تقم بتقديم أي توقعات حتى الآن."
        else:
            for p in predictions[-5:]: # عرض آخر 5 توقعات
                m = p.match
                status = f"✅ (+{p.points_earned} نقطة)" if p.is_processed else "⏳ بانتظار النتيجة"
                profile_text += f"• {m.home_team} vs {m.away_team} | توقعك: [{p.predicted_home_score}-{p.predicted_away_score}] | {status}\n"

        await update.message.reply_text(profile_text, parse_mode="HTML")


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المتصدرين"""
    with get_db() as db:
        top_users = db.query(User).order_by(User.points.desc()).limit(10).all()

        text = "🏆 <b>جدول ترتيب المتصدرين:</b>\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for idx, u in enumerate(top_users):
            medal = medals[idx] if idx < len(medals) else "👤"
            text += f"{medal} <b>{u.full_name}</b> - {u.points} نقطة (توقع صحيح: {u.correct_predictions})\n"

        await update.message.reply_text(text, parse_mode="HTML")


# ---------------------------------------------------------
# معالج الضغط على الأزرار التفاعلية (Callback Query Handler)
# ---------------------------------------------------------

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # 1. إظهار خيارات التوقع لمباراة محدودة
    if data.startswith("pred_select_"):
        match_id = int(data.split("_")[2])
        with get_db() as db:
            m = db.query(Match).filter(Match.id == match_id).first()
            if not m or m.status != "NS":
                await query.edit_message_text("❌ انتهت فترة التوقع لهذه المباراة أو أنها بدأت بالفعل.")
                return

            keyboard = [
                [
                    InlineKeyboardButton("1 - 0", callback_data=f"setpred_{m.id}_1_0"),
                    InlineKeyboardButton("2 - 0", callback_data=f"setpred_{m.id}_2_0"),
                    InlineKeyboardButton("2 - 1", callback_data=f"setpred_{m.id}_2_1")
                ],
                [
                    InlineKeyboardButton("0 - 0", callback_data=f"setpred_{m.id}_0_0"),
                    InlineKeyboardButton("1 - 1", callback_data=f"setpred_{m.id}_1_1"),
                    InlineKeyboardButton("2 - 2", callback_data=f"setpred_{m.id}_2_2")
                ],
                [
                    InlineKeyboardButton("0 - 1", callback_data=f"setpred_{m.id}_0_1"),
                    InlineKeyboardButton("0 - 2", callback_data=f"setpred_{m.id}_0_2"),
                    InlineKeyboardButton("1 - 2", callback_data=f"setpred_{m.id}_1_2")
                ],
                [
                    InlineKeyboardButton("3 - 0", callback_data=f"setpred_{m.id}_3_0"),
                    InlineKeyboardButton("3 - 1", callback_data=f"setpred_{m.id}_3_1"),
                    InlineKeyboardButton("3 - 2", callback_data=f"setpred_{m.id}_3_2")
                ]
            ]
            text = f"🎯 <b>اختر توقعك لمباراة:</b>\n{m.home_team} vs {m.away_team}"
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    # 2. حفظ التوقع في قاعدة البيانات
    elif data.startswith("setpred_"):
        parts = data.split("_")
        match_id = int(parts[1])
        home_score = int(parts[2])
        away_score = int(parts[3])
        user_id = query.from_user.id

        with get_db() as db:
            m = db.query(Match).filter(Match.id == match_id).first()
            if not m or m.status != "NS":
                await query.edit_message_text("❌ لا يمكن التوقع، المباراة بدأت أو تم غلقها.")
                return

            # البحث عن توقع سابق لتحديثه أو إنشاء توقع جديد
            pred = db.query(Prediction).filter(
                Prediction.user_id == user_id,
                Prediction.match_id == match_id
            ).first()

            if pred:
                pred.predicted_home_score = home_score
                pred.predicted_away_score = away_score
            else:
                pred = Prediction(
                    user_id=user_id,
                    match_id=match_id,
                    predicted_home_score=home_score,
                    predicted_away_score=away_score
                )
                db.add(pred)

            await query.edit_message_text(
                f"✅ <b>تم تسجيل توقعك بنجاح!</b>\n"
                f"⚔️ {m.home_team} [{home_score} - {away_score}] {m.away_team}\n"
                f"بالتوفيق! 🍀",
                parse_mode="HTML"
            )

    # 3. عرض إحصائيات المباراة تفصيلياً ورجل المباراة
    elif data.startswith("stats_"):
        match_id = int(data.split("_")[1])
        with get_db() as db:
            m = db.query(Match).filter(Match.id == match_id).first()
            if not m:
                await query.edit_message_text("❌ لم يتم العثور على بيانات المباراة.")
                return

            # جلب الإحصائيات ورجل المباراة من الـ Bank
            stats = bank.fetch_match_statistics(m.api_match_id)
            motm = bank.fetch_player_of_the_match(m.api_match_id)

            text = f"📊 <b>إحصائيات المباراة:</b>\n"
            text += f"⚔️ <b>{m.home_team}</b> vs <b>{m.away_team}</b>\n"
            text += f"🏆 {m.league_name} | النتيجة: [{m.home_score if m.home_score is not None else 0} - {m.away_score if m.away_score is not None else 0}]\n"
            text += f"⭐ <b>رجل المباراة:</b> {motm}\n"
            text += "-----------------------------------\n"

            if stats:
                for team, s_data in stats.items():
                    text += f"🔹 <b>{team}:</b>\n"
                    text += f" • الاستحواذ: {s_data.get('Ball Possession', 'N/A')}\n"
                    text += f" • إجمالي التسديدات: {s_data.get('Total Shots', 'N/A')}\n"
                    text += f" • التسديدات على المرمى: {s_data.get('Shots on Goal', 'N/A')}\n"
                    text += f" • الكروت الصفراء: {s_data.get('Yellow Cards', 'N/A')}\n"
                    text += f" • الكروت الحمراء: {s_data.get('Red Cards', 'N/A')}\n\n"
            else:
                text += "\n⚠️ الإحصائيات التفصيلية غير متوفرة لهذه المباراة حالياً."

            await query.message.reply_text(text, parse_mode="HTML")

    # 4. تحديث قائمة المباشر
    elif data == "refresh_live":
        await live_matches_handler(update, context)
