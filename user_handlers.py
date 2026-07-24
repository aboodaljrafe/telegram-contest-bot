import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# استدعاءات مباشرة من المجلد الرئيسي
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


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    with get_db() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                full_name=user.full_name or user.first_name
            )
            db.add(db_user)
            db.commit()

    text = (
        f"أهلاً بك يا <b>{user.first_name}</b> في بوت توقعات المباريات! ⚽🏆\n\n"
        "اختر من القائمة أدناه لعرض المباريات والتوقع:"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_keyboard())


async def todays_matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            f"👤 <b>الملف الشخصي:</b> {user.full_name}\n"
            f"🏆 <b>مجموع النقاط:</b> {user.total_points}\n"
            f"🎯 <b>عدد التوقعات:</b> {len(predictions)}\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_db() as db:
        top_users = db.query(User).order_by(User.total_points.desc()).limit(10).all()
        text = "🏆 <b>جدول ترتيب أفضل 10 متوقعين:</b>\n\n"
        for idx, u in enumerate(top_users, start=1):
            text += f"{idx}. {u.full_name} - {u.total_points} نقطة\n"
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
