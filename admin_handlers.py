import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import Config
from connection import get_db
from models import User, Match, Prediction
from bank import bank
from scoring import evaluate_all_finished_matches
from state_manager import state_manager

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# دالة التحقق من صلاحيات المشرف
# ---------------------------------------------------------
def is_admin(user_id: int, db_session=None) -> bool:
    raw_admin_ids = getattr(Config, 'ADMIN_IDS', [])
    admin_ids = []
    if isinstance(raw_admin_ids, str):
        admin_ids = [int(x.strip()) for x in raw_admin_ids.split(",") if x.strip().isdigit()]
    elif isinstance(raw_admin_ids, (list, set, tuple)):
        admin_ids = [int(x) for x in raw_admin_ids if str(x).isdigit()]

    if user_id in admin_ids:
        return True
    if db_session:
        user = db_session.query(User).filter(User.id == user_id).first()
        return bool(user and user.is_admin)
    return False


# ---------------------------------------------------------
# لوحة تحكم المشرف (Admin Panel)
# ---------------------------------------------------------
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

    text = (
        "🛠️ <b>لوحة تحكم المشرف</b>\n"
        "───────────────────\n"
        "أهلاً بك عزيزي المشرف، اختر الخدمة المطلوبة من القائمة التالية:"
    )

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("➕ إضافة مباراة يدويًا"), KeyboardButton("📝 رصد نتيجة مباراة")],
            [KeyboardButton("📊 إحصائيات النظام"), KeyboardButton("👥 إدارة المستخدمين")],
            [KeyboardButton("🔄 تحديث البيانات"), KeyboardButton("⚡ مزامنة وتقييم آلي")],
            [KeyboardButton("⬅️ القائمة الرئيسية")]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def refresh_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

    await update.message.reply_text("🔄 <b>جاري مزامنة وجلب أحدث البيانات...</b>", parse_mode="HTML")
    try:
        bank.sync_todays_matches()
        bank.sync_live_matches()
        await update.message.reply_text("✅ <b>تم تحديث المباشر ومباريات اليوم بنجاح!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"خطأ أثناء تحديث البيانات: {e}")
        await update.message.reply_text(f"❌ <b>حدث خطأ أثناء التحديث:</b> {e}", parse_mode="HTML")


# ---------------------------------------------------------
# 1. تدفق إضافة مباراة يدوياً (Manual Match Addition Flow)
# ---------------------------------------------------------
async def start_add_match_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

    state_manager.set_state(user_id, "ADD_MATCH_HOME")
    await update.message.reply_text(
        "➕ <b>خطوة 1/3:</b> أدخل اسم الفريق <b>المستضيف (صاحب الأرض)</b>:\n\n"
        "<i>(أرسل 'إلغاء' في أي وقت لإلغاء العملية)</i>",
        parse_mode="HTML"
    )


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.lower() in ["إلغاء", "الغي", "cancel"]:
        if state_manager.get_state(user_id):
            state_manager.clear_state(user_id)
            await update.message.reply_text("❌ <b>تم إلغاء العملية الجارية.</b>", parse_mode="HTML")
            return True
        return False

    user_state = state_manager.get_state(user_id)
    if not user_state:
        return False

    st = user_state.get("state")
    data = user_state.get("data", {})

    # أ) استقبال اسم الفريق المستضيف
    if st == "ADD_MATCH_HOME":
        state_manager.set_state(user_id, "ADD_MATCH_AWAY", {"home": text})
        await update.message.reply_text(
            f"✅ المستضيف: <b>{text}</b>\n\n➕ <b>خطوة 2/3:</b> أدخل اسم الفريق <b>الضيف</b>:",
            parse_mode="HTML"
        )
        return True

    # ب) استقبال اسم الفريق الضيف
    if st == "ADD_MATCH_AWAY":
        home_team = data.get("home")
        state_manager.set_state(user_id, "ADD_MATCH_DATE", {"home": home_team, "away": text})

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("اليوم 20:00 UTC", callback_data="set_date_today_20"),
                InlineKeyboardButton("اليوم 22:00 UTC", callback_data="set_date_today_22")
            ],
            [
                InlineKeyboardButton("غداً 20:00 UTC", callback_data="set_date_tomorrow_20"),
                InlineKeyboardButton("غداً 22:00 UTC", callback_data="set_date_tomorrow_22")
            ]
        ])
        await update.message.reply_text(
            f"✅ الضيف: <b>{text}</b>\n\n"
            f"➕ <b>خطوة 3/3:</b> اختر موعد المباراة من الأزرار الأدناه أو اكتبه يدوياً بأسلوب:\n"
            f"<code>YYYY-MM-DD HH:MM</code> (مثال: <code>2026-07-24 21:00</code>):",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return True

    # ج) استقبال وقت وموعد المباراة نصياً
    if st == "ADD_MATCH_DATE":
        try:
            match_dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
        except ValueError:
            await update.message.reply_text(
                "❌ <b>صيغة التاريخ خاطئة!</b>\nيرجى الكتابة بالصيغة: <code>2026-07-24 21:00</code>",
                parse_mode="HTML"
            )
            return True

        _create_manual_match(data.get("home"), data.get("away"), match_dt)
        state_manager.clear_state(user_id)
        await update.message.reply_text(
            f"✅ <b>تمت إضافة المباراة بنجاح!</b>\n\n"
            f"⚔️ <b>{data.get('home')}</b> vs <b>{data.get('away')}</b>\n"
            f"📅 המوعد: <code>{match_dt.strftime('%Y-%m-%d %H:%M UTC')}</code>",
            parse_mode="HTML"
        )
        return True

    # د) استقبال النتيجة يدويًا من قبل المشرف
    if st.startswith("SET_SCORE_"):
        match_id = int(st.split("_")[2])
        try:
            parts = text.replace(" ", "").split("-")
            h_score, a_score = int(parts[0]), int(parts[1])
        except Exception:
            await update.message.reply_text(
                "❌ <b>صيغة النتيجة خاطئة!</b>\nيرجى كتابتها بالشكل: <code>2-1</code> (مضيف - ضيف)",
                parse_mode="HTML"
            )
            return True

        with get_db() as db:
            match = db.query(Match).filter(Match.id == match_id).first()
            if match:
                match.home_score = h_score
                match.away_score = a_score
                match.status = "FINISHED"
                match.is_evaluated = True
                db.commit()

        evaluate_all_finished_matches()
        state_manager.clear_state(user_id)
        await update.message.reply_text(
            "🏆 <b>تم رصد النتيجة الرسمية وتقييم نقاط جميع المنافسين بنجاح!</b>",
            parse_mode="HTML"
        )
        return True

    return False


def _create_manual_match(home: str, away: str, dt: datetime):
    with get_db() as db:
        new_match = Match(
            api_match_id=int(datetime.now(timezone.utc).timestamp()),
            league_name="مباراة مخصصة",
            home_team=home,
            away_team=away,
            match_date=dt,
            status="NS",
            is_evaluated=False
        )
        db.add(new_match)
        db.commit()


# ---------------------------------------------------------
# 2. رصد النتيجة ومعالجة تفاعل التاريخ السريع
# ---------------------------------------------------------
async def start_set_result_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

        unclosed_matches = db.query(Match).filter(Match.is_evaluated == False).all()
        if not unclosed_matches:
            await update.message.reply_text("✨ <b>لا توجد مباريات معلقة بانتظار رصد النتيجة حالياً.</b>", parse_mode="HTML")
            return

        keyboard = []
        for m in unclosed_matches:
            keyboard.append([
                InlineKeyboardButton(
                    f"⚽ {m.home_team} vs {m.away_team}",
                    callback_data=f"admin_select_m_{m.id}"
                )
            ])

        await update.message.reply_text(
            "📝 <b>اختر المباراة المراد رصد نتيجتها الرسمية:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # معالجة أزرار التوقيت والتاريخ السريعة
    if data.startswith("set_date_"):
        user_state = state_manager.get_state(user_id)
        if user_state:
            now = datetime.now(timezone.utc)
            if data == "set_date_today_20":
                match_dt = now.replace(hour=20, minute=0, second=0, microsecond=0)
            elif data == "set_date_today_22":
                match_dt = now.replace(hour=22, minute=0, second=0, microsecond=0)
            elif data == "set_date_tomorrow_20":
                match_dt = (now + timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
            elif data == "set_date_tomorrow_22":
                match_dt = (now + timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
            else:
                match_dt = now

            home = user_state.get("data", {}).get("home")
            away = user_state.get("data", {}).get("away")

            _create_manual_match(home, away, match_dt)
            state_manager.clear_state(user_id)

            await query.edit_message_text(
                f"✅ <b>تمت إضافة المباراة بنجاح!</b>\n\n"
                f"⚔️ <b>{home}</b> vs <b>{away}</b>\n"
                f"📅 המوعد: <code>{match_dt.strftime('%Y-%m-%d %H:%M UTC')}</code>",
                parse_mode="HTML"
            )
        return True

    if data.startswith("admin_select_m_"):
        match_id = int(data.split("_")[3])
        state_manager.set_state(user_id, f"SET_SCORE_{match_id}")
        await query.edit_message_text(
            "🎯 أرسل النتيجة الرسمية للمباراة بالترتيب: <b>(المستضيف - الضيف)</b>\n\n"
            "مثال: <code>2-1</code>",
            parse_mode="HTML"
        )
        return True

    return False


# ---------------------------------------------------------
# 3. إحصائيات النظام وإدارة المستخدمين والمزامنة
# ---------------------------------------------------------
async def system_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

        total_users = db.query(User).count()
        total_matches = db.query(Match).count()
        total_predictions = db.query(Prediction).count()

        text = (
            "📊 <b>إحصائيات نظام البوت الرسمية:</b>\n"
            "───────────────────\n"
            f"👤 <b>إجمالي المنافسين:</b> {total_users}\n"
            f"⚽ <b>إجمالي المباريات:</b> {total_matches}\n"
            f"🎯 <b>إجمالي التوقعات:</b> {total_predictions}\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

        users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
        text = "👥 <b>أحدث 10 منافسين انضموا للبوت:</b>\n───────────────────\n"
        for u in users:
            name = u.full_name or 'بدون اسم'
            text += f"• <b>{name}</b> | <code>{u.id}</code>\n"

        await update.message.reply_text(text, parse_mode="HTML")


async def force_sync_and_eval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            return

    await update.message.reply_text("⚡ <b>جاري تنفيذ المزامنة والتقييم الآلي فوراً...</b>", parse_mode="HTML")
    try:
        bank.sync_todays_matches()
        evaluate_all_finished_matches()
        await update.message.reply_text("✅ <b>تمت عملية المزامنة وحساب تقييم التوقعات بنجاح!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"خطأ أثناء التقييم والمزامنة: {e}")
        await update.message.reply_text(f"❌ <b>حدث خطأ:</b> {e}", parse_mode="HTML")
