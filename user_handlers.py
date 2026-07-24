import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from connection import get_db
from models import User, Match, Prediction
from bank import bank
from state_manager import state_manager
from admin_handlers import is_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_main_keyboard(is_admin_user: bool = False):
    keyboard = [
        [KeyboardButton("⚽ مباريات اليوم والتوقعات"), KeyboardButton("🔴 المباريات المباشرة")],
        [KeyboardButton("📊 رصيدي وتوقعاتي"), KeyboardButton("🏆 جدول الترتيب")],
        [KeyboardButton("🔄 تحديث البيانات")]
    ]
    # إضافة صلاحيات المشرف في الأزرار الرئيسية مباشرة
    if is_admin_user:
        keyboard.append([KeyboardButton("➕ إضافة مباراة يدويًا"), KeyboardButton("📝 رصد نتيجة مباراة")])
        keyboard.append([KeyboardButton("📊 إحصائيات النظام"), KeyboardButton("👥 إدارة المستخدمين")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def build_prediction_keyboard(match_id: int, home_score: int, away_score: int):
    """إنشاء أزرار + و - التفاعلية لتوقع النتيجة"""
    keyboard = [
        [InlineKeyboardButton(f"🏠 المستضيف: {home_score}", callback_data="ignore")],
        [
            InlineKeyboardButton("➕ 1", callback_data=f"pred_h_up_{match_id}_{home_score}_{away_score}"),
            InlineKeyboardButton("➖ 1", callback_data=f"pred_h_dn_{match_id}_{home_score}_{away_score}")
        ],
        [InlineKeyboardButton(f"✈️ الضيف: {away_score}", callback_data="ignore")],
        [
            InlineKeyboardButton("➕ 1", callback_data=f"pred_a_up_{match_id}_{home_score}_{away_score}"),
            InlineKeyboardButton("➖ 1", callback_data=f"pred_a_dn_{match_id}_{home_score}_{away_score}")
        ],
        [InlineKeyboardButton("💾 حفظ وتأكيد التوقع", callback_data=f"pred_save_{match_id}_{home_score}_{away_score}")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------
# 1. معالج البداية والقائمة الرئيسية
# ---------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    with get_db() as db:
        db_user = db.query(User).filter(User.id == user_id).first()
        admin_flag = is_admin(user_id, db)

        if not db_user or not db_user.full_name or len(db_user.full_name.split()) < 3:
            if not db_user:
                db_user = User(id=user_id, username=update.effective_user.username, full_name=None)
                db.add(db_user)
                db.commit()

            state_manager.set_state(user_id, "AWAITING_FULL_NAME")
            await update.message.reply_text(
                "🔒 <b>مرحباً بك في بوت التوقعات!</b>\n\n"
                "لحفظ نقاطك وإدراجك في جدول المنافسين، يرجى كتابة <b>اسمك الثلاثي</b> أولاً للبدء:",
                parse_mode="HTML"
            )
            return

        await update.message.reply_text(
            f"أهلاً بك يا <b>{db_user.full_name}</b> ⚽🏆\nاختر من القائمة أدناه:",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(admin_flag)
        )


# ---------------------------------------------------------
# 2. عرض المباريات والتوقعات
# ---------------------------------------------------------

async def todays_matches_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.full_name or len(user.full_name.split()) < 3:
            await start_handler(update, context)
            return

        matches = db.query(Match).filter(Match.is_evaluated == False).all()
        if not matches:
            # محاولة المزامنة إذا كانت القاعدة فارغة
            matches = bank.sync_todays_matches()

        if not matches:
            await update.message.reply_text("لا توجد مباريات مسجلة حالياً.")
            return

        for match in matches:
            # التحقق من وجود توقع سابق للمستخدم
            user_pred = db.query(Prediction).filter(
                Prediction.user_id == user_id,
                Prediction.match_id == match.id
            ).first()

            pred_text = f"🎯 <b>توقعك الحالي:</b> {user_pred.predicted_home_score} - {user_pred.predicted_away_score}" if user_pred else "❌ <b>لم تتوقع بعد</b>"

            text = (
                f"🏆 <b>{match.league_name}</b>\n"
                f"⚔️ <b>{match.home_team}</b> vs <b>{match.away_team}</b>\n"
                f"⏰ الموعد: {match.match_date.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"📌 الحالة: {match.status}\n"
                f"{pred_text}\n"
            )
            
            btn_label = "✏️ تعديل التوقع" if user_pred else "🎯 توقع النتيجة"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn_label, callback_data=f"start_pred_{match.id}")]
            ])
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


# ---------------------------------------------------------
# 3. معالجة أزرار التفاعل (+ و - والتأكيد)
# ---------------------------------------------------------

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "ignore":
        await query.answer()
        return

    # بدء عملية التوقع أو التعديل
    if data.startswith("start_pred_"):
        match_id = int(data.split("_")[2])
        with get_db() as db:
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match or match.is_evaluated:
                await query.answer("⚠️ هذه المباراة تم رصد نتيجتها ولا يمكن التوقع عليها الآن.", show_alert=True)
                return

            existing = db.query(Prediction).filter(Prediction.user_id == user_id, Prediction.match_id == match_id).first()
            h_score = existing.predicted_home_score if existing else 0
            a_score = existing.predicted_away_score if existing else 0

            text = (
                f"🎯 <b>توقع مباراة:</b>\n"
                f"<b>{match.home_team}</b> vs <b>{match.away_team}</b>\n\n"
                "استخدم أزرار (➕ / ➖) لضبط النتيجة ثم اضغط حفظ:"
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=build_prediction_keyboard(match_id, h_score, a_score))
        return

    # التفاعل مع أزرار الزيادة والنقصان
    if data.startswith("pred_"):
        parts = data.split("_")
        action = parts[1] # h_up, h_dn, a_up, a_dn, save
        match_id = int(parts[2])
        h_score = int(parts[3])
        a_score = int(parts[4])

        if action == "h_up": h_score += 1
        elif action == "h_dn": h_score = max(0, h_score - 1)
        elif action == "a_up": a_score += 1
        elif action == "a_dn": a_score = max(0, a_score - 1)
        elif action == "save":
            with get_db() as db:
                match = db.query(Match).filter(Match.id == match_id).first()
                if match and match.is_evaluated:
                    await query.answer("❌ انتهى وقت التوقع لهذه المباراة!", show_alert=True)
                    return

                existing = db.query(Prediction).filter(Prediction.user_id == user_id, Prediction.match_id == match_id).first()
                if existing:
                    existing.predicted_home_score = h_score
                    existing.predicted_away_score = a_score
                else:
                    new_pred = Prediction(user_id=user_id, match_id=match_id, predicted_home_score=h_score, predicted_away_score=a_score)
                    db.add(new_pred)
                db.commit()

            await query.edit_message_text(f"✅ <b>تم حفظ توقعك بنجاح!</b>\nالنتيجة المتوقعة: ({match.home_team} {h_score} - {a_score} {match.away_team})", parse_mode="HTML")
            return

        # تحديث الأزرار بالقيم الجديدة
        await query.edit_message_reply_markup(reply_markup=build_prediction_keyboard(match_id, h_score, a_score))


# ---------------------------------------------------------
# 4. المعالجات النصية والميزات الأخرى
# ---------------------------------------------------------

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    user_state = state_manager.get_state(user_id)

    if user_state and user_state.get("state") == "AWAITING_FULL_NAME":
        if len(text.split()) < 3:
            await update.message.reply_text("⚠️ يرجى كتابة الاسم الثلاثي بوضوح (مثال: محمد أحمد علي):")
            return

        with get_db() as db:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                db_user.full_name = text
                db.commit()
                admin_flag = is_admin(user_id, db)

        state_manager.clear_state(user_id)
        await update.message.reply_text(
            f"✅ تم تسجيلك بنجاح بـاسم: <b>{text}</b>!",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(admin_flag)
        )


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
        predictions = db.query(Prediction).filter(Prediction.user_id == user_id).all()
        text = (
            f"👤 <b>اسم المنافس:</b> {user.full_name if user else 'غير معروف'}\n"
            f"🆔 <b>المعرف:</b> <code>{user_id}</code>\n"
            f"🏆 <b>إجمالي النقاط:</b> {user.total_points if user else 0}\n"
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
    await update.message.reply_text("✅ تم تحديث البيانات بنجاح!")
