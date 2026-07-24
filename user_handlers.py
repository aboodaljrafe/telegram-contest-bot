import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from connection import get_db
from models import User, Match, Prediction
from bank import bank
from state_manager import state_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_main_keyboard():
    keyboard = [
        [KeyboardButton("⚽ مباريات اليوم والتوقعات"), KeyboardButton("🔴 المباريات المباشرة")],
        [KeyboardButton("📊 رصيدي وتوقعاتي"), KeyboardButton("🏆 جدول الترتيب")],
        [KeyboardButton("🔄 تحديث البيانات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ---------------------------------------------------------
# 1. معالج البداية والتحقق من التسجيل والخصوصية
# ---------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    with get_db() as db:
        db_user = db.query(User).filter(User.id == user_id).first()
        
        # إذا لم يكن المستخدم موجوداً أو لم يسجل اسمه الثلاثي بعد
        if not db_user or not db_user.full_name or len(db_user.full_name.split()) < 3:
            if not db_user:
                db_user = User(
                    id=user_id,
                    username=update.effective_user.username,
                    full_name=None
                )
                db.add(db_user)
                db.commit()

            # تحديد حالة المستخدم بانتظار الاسم
            state_manager.set_state(user_id, "AWAITING_FULL_NAME")

            await update.message.reply_text(
                "🔒 <b>مرحباً بك في بوت التوقعات!</b>\n\n"
                "لحفظ نقاطك وإدراجك في جدول المنافسين، يرجى كتابة <b>اسمك الثلاثي</b> أولاً للبدء:",
                parse_mode="HTML"
            )
            return

        # إذا كان مسجلاً بالكامل
        await update.message.reply_text(
            f"أهلاً بك مجدداً يا <b>{db_user.full_name}</b> ⚽🏆\nاختر من القائمة أدناه:",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )


# ---------------------------------------------------------
# 2. استقبال النصوص (الاسم الثلاثي والتوقعات)
# ---------------------------------------------------------

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    user_state = state_manager.get_state(user_id)

    # أ) معالجة استقبال الاسم الثلاثي
    if user_state and user_state.get("state") == "AWAITING_FULL_NAME":
        name_parts = text.split()
        if len(name_parts) < 3:
            await update.message.reply_text(
                "⚠️ <b>الاسم غير مكتمل!</b>\nيرجى كتابة الاسم الثلاثي بوضوح (مثال: محمد أحمد علي):",
                parse_mode="HTML"
            )
            return

        # حفظ الاسم الثلاثي في جدول المنافسين
        with get_db() as db:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                db_user.full_name = text
                db.commit()

        # إنهاء الحالة وإظهار القائمة
        state_manager.clear_state(user_id)
        await update.message.reply_text(
            f"✅ تم تسجيلك بنجاح بـاسم: <b>{text}</b>!\nيمكنك الآن المشاركة في التوقعات والمنافسة.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        return

    # ب) معالجة استقبال توقع النتيجة (مثال: 2-1)
    if user_state and user_state.get("state") == "AWAITING_PREDICTION":
        match_id = user_state.get("data", {}).get("match_id")
        try:
            parts = text.replace(" ", "").split("-")
            if len(parts) != 2:
                raise ValueError()
            h_score, a_score = int(parts[0]), int(parts[1])
        except ValueError:
            await update.message.reply_text("❌ صيغة التوقع خاطئة! يرجى إرسال التوقع بالشكل: 2-1")
            return

        with get_db() as db:
            existing = db.query(Prediction).filter(
                Prediction.user_id == user_id,
                Prediction.match_id == match_id
            ).first()

            if existing:
                existing.predicted_home_score = h_score
                existing.predicted_away_score = a_score
            else:
                new_pred = Prediction(
                    user_id=user_id,
                    match_id=match_id,
                    predicted_home_score=h_score,
                    predicted_away_score=a_score
                )
                db.add(new_pred)
            db.commit()

        state_manager.clear_state(user_id)
        await update.message.reply_text("✅ تم تسجيل توقعك بنجاح! بالتوفيق 🎯")
        return


# ---------------------------------------------------------
# 3. بقية المعالجات المجهزة لحماية الخصوصية
# ---------------------------------------------------------

async def todays_matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.full_name or len(user.full_name.split()) < 3:
            await start_handler(update, context)
            return

    matches = bank.sync_todays_matches()
    if not matches:
        await update.message.reply_text("لا توجد مباريات مسجلة لهذا اليوم.")
        return

    for match in matches:
        text = (
            f"🏆 <b>{match.league_name}</b>\n"
            f"⚔️ {match.home_team} vs {match.away_team}\n"
            f"⏰ الموعد: {match.match_date.strftime('%H:%M UTC')}\n"
            f"📌 الحالة: {match.status}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 توقع النتيجة", callback_data=f"predict_{match.id}")]
        ])
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def live_matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_db() as db:
        live_matches = db.query(Match).filter(Match.status.in_(["LIVE", "HT"])).all()
        if not live_matches:
            await update.message.reply_text("لا توجد مباريات مباشرة حالياً.")
            return

        text = "🔴 <b>المباريات المباشرة الآن:</b>\n\n"
        for m in live_matches:
            h_score = m.home_score if m.home_score is not None else 0
            a_score = m.away_score if m.away_score is not None else 0
            text += f"⚽ {m.home_team} {h_score} - {a_score} {m.away_team}\n"
        await update.message.reply_text(text, parse_mode="HTML")


async def user_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await update.message.reply_text("لم يتم العثور على حسابك.")
            return

        predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()
        text = (
            f"👤 <b>اسم المنافس:</b> {user.full_name}\n"
            f"🆔 <b>المعرف:</b> <code>{user.id}</code>\n"
            f"🏆 <b>إجمالي النقاط:</b> {user.total_points}\n"
            f"🎯 <b>عدد التوقعات:</b> {len(predictions)}\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_db() as db:
        top_users = db.query(User).filter(User.full_name.isnot(None)).order_by(User.total_points.desc()).limit(10).all()
        text = "🏆 <b>جدول ترتيب أفضل 10 منافسين:</b>\n\n"
        for idx, u in enumerate(top_users, start=1):
            text += f"{idx}. <b>{u.full_name}</b> — {u.total_points} نقطة\n"
        await update.message.reply_text(text, parse_mode="HTML")


async def refresh_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank.sync_todays_matches()
    await update.message.reply_text("✅ تم تحديث بيانات المباريات بنجاح!")


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data and query.data.startswith("predict_"):
        match_id = int(query.data.split("_")[1])
        state_manager.set_state(query.from_user.id, "AWAITING_PREDICTION", {"match_id": match_id})
        await query.edit_message_text("أرسل توقعك للنتيجة بالشكل التالي: (مثال: 2-1)")
