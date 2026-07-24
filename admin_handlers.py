import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import Config
from connection import get_db
from models import User, Match, Prediction
from bank import bank
from scoring import evaluate_all_finished_matches
from state_manager import state_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db):
            await update.message.reply_text("❌ عذراً، لا تملك صلاحيات الوصول للوحة المشرفين.")
            return

    # استيراد دالة الأزرار محلياً لتجنب الـ Circular Import
    from user_handlers import get_main_keyboard

    # إرسال الرسالة مع إرفاق لوحة أزرار المشرف المحدثة
    await update.message.reply_text(
        "🛠️ <b>تم تفعيل لوحة تحكم المشرفين!</b>\nظهرت لك الأزرار الجديدة في القائمة بالأسفل 👇",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin_user=True)
    )


# ---------------------------------------------------------
# 1. إضافة مباراة يدوياً (Flow)
# ---------------------------------------------------------

async def start_add_match_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db): return

    state_manager.set_state(user_id, "ADD_MATCH_HOME")
    await update.message.reply_text("➕ <b>خطوة 1/3:</b> أدخل اسم الفريق <b>المستضيف (صاحب الأرض)</b>:", parse_mode="HTML")


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    user_state = state_manager.get_state(user_id)

    if not user_state: return False

    st = user_state.get("state")
    data = user_state.get("data", {})

    # أ) استقبال اسم المستضيف
    if st == "ADD_MATCH_HOME":
        state_manager.set_state(user_id, "ADD_MATCH_AWAY", {"home": text})
        await update.message.reply_text(f"✅ المستضيف: <b>{text}</b>\n\n➕ <b>خطوة 2/3:</b> أدخل اسم الفريق <b>الضيف</b>:", parse_mode="HTML")
        return True

    # ب) استقبال اسم الضيف
    if st == "ADD_MATCH_AWAY":
        home_team = data.get("home")
        state_manager.set_state(user_id, "ADD_MATCH_DATE", {"home": home_team, "away": text})
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("اليوم 20:00", callback_data="set_date_today_20"), InlineKeyboardButton("اليوم 22:00", callback_data="set_date_today_22")],
            [InlineKeyboardButton("غداً 20:00", callback_data="set_date_tomorrow_20"), InlineKeyboardButton("غداً 22:00", callback_data="set_date_tomorrow_22")]
        ])
        await update.message.reply_text(
            f"✅ الضيف: <b>{text}</b>\n\n➕ <b>خطوة 3/3:</b> اختر موعد المباراة من الأزرار أو اكتبه بالشكل (YYYY-MM-DD HH:MM):",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return True

    # ج) استقبال الوقت والموعد نصياً
    if st == "ADD_MATCH_DATE":
        try:
            match_dt = datetime.strptime(text, "%Y-%m-%d %H:%M")
        except ValueError:
            await update.message.reply_text("❌ صيغة التاريخ خاطئة! اكتبه بالصيغة: <code>2026-07-24 21:00</code>", parse_mode="HTML")
            return True

        _create_manual_match(data.get("home"), data.get("away"), match_dt)
        state_manager.clear_state(user_id)
        await update.message.reply_text(f"✅ <b>تمت إضافة المباراة بنجاح!</b>\n⚔️ {data.get('home')} vs {data.get('away')}", parse_mode="HTML")
        return True

    # د) استقبال رصد النتيجة يدويًا
    if st.startswith("SET_SCORE_"):
        match_id = int(st.split("_")[2])
        try:
            parts = text.replace(" ", "").split("-")
            h_score, a_score = int(parts[0]), int(parts[1])
        except Exception:
            await update.message.reply_text("❌ صيغة النتيجة خاطئة! يرجى كتابتها بالشكل: 2-1")
            return True

        with get_db() as db:
            match = db.query(Match).filter(Match.id == match_id).first()
            if match:
                match.home_score = h_score
                match.away_score = a_score
                match.status = "FINISHED"
                match.is_evaluated = True
                db.commit()

        # تقييم النقاط تلقائياً فور رصد النتيجة
        evaluate_all_finished_matches()
        state_manager.clear_state(user_id)
        await update.message.reply_text(f"✅ <b>تم رصد النتيجة الرسمية وتقييم نقاط المنافسين بنجاح!</b>", parse_mode="HTML")
        return True

    return False


def _create_manual_match(home: str, away: str, dt: datetime):
    with get_db() as db:
        new_match = Match(
            api_match_id=int(datetime.utcnow().timestamp()),
            league_name="مباراة ودية / خاصة",
            home_team=home,
            away_team=away,
            match_date=dt,
            status="NS",
            is_evaluated=False
        )
        db.add(new_match)
        db.commit()


# ---------------------------------------------------------
# 2. رصد النتيجة يدويًا
# ---------------------------------------------------------

async def start_set_result_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        if not is_admin(user_id, db): return

        unclosed_matches = db.query(Match).filter(Match.is_evaluated == False).all()
        if not unclosed_matches:
            await update.message.reply_text("لا توجد مباريات معلقة بانتظار رصد النتيجة.")
            return

        keyboard = []
        for m in unclosed_matches:
            keyboard.append([InlineKeyboardButton(f"⚽ {m.home_team} vs {m.away_team}", callback_data=f"admin_select_m_{m.id}")])

        await update.message.reply_text("📝 <b>اختر المباراة لرصد نتيجتها الرسمية:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("set_date_"):
        user_state = state_manager.get_state(user_id)
        if user_state:
            match_dt = datetime.utcnow()
            home = user_state.get("data", {}).get("home")
            away = user_state.get("data", {}).get("away")
            _create_manual_match(home, away, match_dt)
            state_manager.clear_state(user_id)
            await query.edit_message_text(f"✅ <b>تمت إضافة المباراة بنجاح!</b>\n⚔️ {home} vs {away}", parse_mode="HTML")
        return True

    if data.startswith("admin_select_m_"):
        match_id = int(data.split("_")[3])
        state_manager.set_state(user_id, f"SET_SCORE_{match_id}")
        await query.edit_message_text("أرسل النتيجة الرسمية للمباراة بالشكل: (مضيف - ضيف) مثال: <b>2-1</b>", parse_mode="HTML")
        return True

    return False


async def system_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_db() as db:
        total_users = db.query(User).count()
        total_matches = db.query(Match).count()
        total_predictions = db.query(Prediction).count()
        await update.message.reply_text(f"📊 <b>إحصائيات النظام:</b>\n\n👤 المستخدمين: {total_users}\n⚽ المباريات: {total_matches}\n🎯 التوقعات: {total_predictions}", parse_mode="HTML")


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_db() as db:
        users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
        text = "👥 <b>أحدث 10 مستخدمين:</b>\n\n"
        for u in users:
            text += f"• <b>{u.full_name or 'بدون اسم'}</b> (<code>{u.id}</code>)\n"
        await update.message.reply_text(text, parse_mode="HTML")


async def force_sync_and_eval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank.sync_todays_matches()
    evaluate_all_finished_matches()
    await update.message.reply_text("✅ تمت المزامنة والتقييم بنجاح!")
