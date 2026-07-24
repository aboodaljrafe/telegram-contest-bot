import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from config import Config
from connection import get_db
from models import User, Match, Prediction
from bank import bank
from scoring import evaluate_all_finished_matches

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_admin(user_id: int, db_session=None) -> bool:
    if user_id in Config.ADMIN_IDS:
        return True
    if db_session:
        user = db_session.query(User).filter(User.id == user_id).first()
        return user.is_admin if user else False
    return False


def get_admin_keyboard():
    keyboard = [
        [KeyboardButton("📊 إحصائيات النظام"), KeyboardButton("⚡ مزامنة وتقييم آلي")],
        [KeyboardButton("👥 إدارة المستخدمين"), KeyboardButton("⬅️ القائمة الرئيسية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            await update.message.reply_text("❌ عذراً، لا تملك صلاحيات الوصول للوحة المشرفين.")
            return

    await update.message.reply_text(
        "🛠️ <b>لوحة تحكم المشرفين:</b>\n"
        "يمكنك من هنا متابعة النظام، إدارة المستخدمين، وتحديث البيانات وتقييم النقاط فورياً.",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


async def system_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

        total_users = db.query(User).count()
        total_matches = db.query(Match).count()
        total_predictions = db.query(Prediction).count()
        evaluated_matches = db.query(Match).filter(Match.is_evaluated == True).count()

        text = (
            "📊 <b>إحصائيات النظام الحالية:</b>\n\n"
            f"👤 <b>إجمالي المستخدمين:</b> {total_users}\n"
            f"⚽ <b>إجمالي المباريات المسجلة:</b> {total_matches}\n"
            f"✅ <b>المباريات المُقيّمة بالكامل:</b> {evaluated_matches}\n"
            f"🎯 <b>إجمالي التوقعات المُسجلة:</b> {total_predictions}\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")


async def force_sync_and_eval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

    msg = await update.message.reply_text("⏳ جاري المزامنة مع خادم المباريات وتقييم التوقعات...")
    try:
        bank.sync_todays_matches()
        bank.sync_live_matches()
        evaluate_all_finished_matches()
        await msg.edit_text("✅ تمت المزامنة واحتساب نقاط كافة المباريات المنتهية بنجاح!")
    except Exception as e:
        logger.error(f"خطأ المزامنة اليدوية: {e}")
        await msg.edit_text(f"❌ حدث خطأ أثناء المزامنة: {e}")


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

        latest_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()

        text = "👥 <b>أحدث 10 مستخدمين مسجلين:</b>\n\n"
        for u in latest_users:
            status = "🚫 محظور" if u.is_blocked else "✅ نشط"
            role = "👑 مشرف" if u.is_admin or u.id in Config.ADMIN_IDS else "👤 مشترك"
            text += f"• <b>{u.full_name}</b> (<code>{u.id}</code>) | {role} | {status}\n"

        await update.message.reply_text(text, parse_mode="HTML")
