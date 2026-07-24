import asyncio
import logging
import os
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

from config import Config
from connection import init_db
from bank import bank
from scoring import evaluate_all_finished_matches

# استيراد معالجات المستخدم (المنافس)
from user_handlers import (
    start_handler, todays_matches_handler, live_matches_handler, 
    user_profile_handler, leaderboard_handler, callback_query_handler, 
    text_message_handler
)

# استيراد معالجات المشرف
from admin_handlers import (
    admin_panel_handler, system_stats_handler, force_sync_and_eval_handler, 
    admin_users_handler, start_add_match_manual, start_set_result_manual,
    refresh_data_handler, admin_text_handler, admin_callback_handler
)
from state_manager import state_manager

# ---------------------------------------------------------
# 1. إعداد السجلات (Logging)
# ---------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 2. إنشاء تطبيق Flask وتلجرام
# ---------------------------------------------------------
app = Flask(__name__)
bot_token = (Config.BOT_TOKEN or "").strip()
telegram_app = None

if bot_token:
    try:
        telegram_app = Application.builder().token(bot_token).build()
        logger.info("✅ تم إنشاء تطبيق التلجرام بنجاح.")
    except Exception as e:
        logger.error(f"❌ خطأ أثناء إنشاء تطبيق التلجرام: {e}")


# ---------------------------------------------------------
# 3. معالجات مركزية موحدة (Master Handlers)
# ---------------------------------------------------------

async def master_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يفحص أولاً إن كانت الرسالة النصية تخص عملية للمشرف، وإن لم تكن يوجهها للمنافس"""
    is_admin_handled = await admin_text_handler(update, context)
    if not is_admin_handled:
        await text_message_handler(update, context)


async def master_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يفحص نقرات الأزرار الشفافة للمشرف أولاً، ثم للمنافسين"""
    is_admin_cb = await admin_callback_handler(update, context)
    if not is_admin_cb:
        await callback_query_handler(update, context)


# ---------------------------------------------------------
# 4. تسجيل كافة الأزرار والأوامر
# ---------------------------------------------------------

def setup_handlers(application: Application):
    if not application:
        return

    # الأوامر الرئيسية
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("admin", admin_panel_handler))

    # أزرار واجهة المنافس (المستخدم العادي)
    application.add_handler(MessageHandler(filters.Regex("^⚽ مباريات اليوم والتوقعات$"), todays_matches_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔴 المباريات المباشرة$"), live_matches_handler))
    application.add_handler(MessageHandler(filters.Regex("^📊 رصيدي وتوقعاتي$"), user_profile_handler))
    application.add_handler(MessageHandler(filters.Regex("^🏆 جدول الترتيب$"), leaderboard_handler))

    # زر دخول لوحة المشرف (يظهر للمشرفين فقط)
    application.add_handler(MessageHandler(filters.Regex("^🛠️ لوحة تحكم المشرف$"), admin_panel_handler))

    # أزرار لوحة تحكم المشرف المنفصلة
    application.add_handler(MessageHandler(filters.Regex("^➕ إضافة مباراة يدويًا$"), start_add_match_manual))
    application.add_handler(MessageHandler(filters.Regex("^📝 رصد نتيجة مباراة$"), start_set_result_manual))
    application.add_handler(MessageHandler(filters.Regex("^📊 إحصائيات النظام$"), system_stats_handler))
    application.add_handler(MessageHandler(filters.Regex("^👥 إدارة المستخدمين$"), admin_users_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔄 تحديث البيانات$"), refresh_data_handler))
    application.add_handler(MessageHandler(filters.Regex("^⚡ مزامنة وتقييم آلي$"), force_sync_and_eval_handler))
    
    # زر العودة للقائمة الرئيسية
    application.add_handler(MessageHandler(filters.Regex("^⬅️ القائمة الرئيسية$"), start_handler))

    # المعالجات الشاملة للنصوص والأزرار
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, master_text_handler))
    application.add_handler(CallbackQueryHandler(master_callback_handler))


if telegram_app:
    setup_handlers(telegram_app)

# ---------------------------------------------------------
# 5. المجدول الآلي للخدمات في الخلفية
# ---------------------------------------------------------

scheduler = None

def init_services():
    global scheduler
    try:
        init_db()
        if scheduler is None:
            scheduler = BackgroundScheduler(daemon=True)
            # مزامنة المباريات المباشرة كل دقيقتين
            scheduler.add_job(lambda: bank.sync_live_matches(), 'interval', minutes=2)
            # مزامنة مباريات اليوم كل ساعة
            scheduler.add_job(lambda: bank.sync_todays_matches(), 'interval', hours=1)
            
            # تنظيف الحالات المنتهية إن وجدت
            if hasattr(state_manager, 'cleanup_expired_states'):
                scheduler.add_job(state_manager.cleanup_expired_states, 'interval', minutes=30)

            scheduler.start()
            logger.info("✅ تم تشغيل قاعدة البيانات والمجدول الآلي بنجاح.")
    except Exception as e:
        logger.error(f"❌ خطأ أثناء تهيئة الخدمات: {e}")

init_services()

# ---------------------------------------------------------
# 6. معالجة تحديثات Webhook بشكل آمن
# ---------------------------------------------------------

def handle_async_update(update_json):
    if not telegram_app:
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if not telegram_app._initialized:
            loop.run_until_complete(telegram_app.initialize())
        update = Update.de_json(update_json, telegram_app.bot)
        loop.run_until_complete(telegram_app.process_update(update))
    except Exception as e:
        logger.error(f"❌ خطأ أثناء معالجة التحديث Async: {e}")
    finally:
        loop.close()

# ---------------------------------------------------------
# 7. مسارات السيرفر (Endpoints)
# ---------------------------------------------------------

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "bot_status": "online" if telegram_app else "token_missing"
    }), 200


@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "active"}), 200

    if not telegram_app:
        return jsonify({"error": "BOT_TOKEN missing"}), 500

    if request.headers.get("content-type") == "application/json":
        json_data = request.get_json(force=True)
        handle_async_update(json_data)
        return "OK", 200

    return "Forbidden", 403


if bot_token:
    app.add_url_rule(
        f"/{bot_token}",
        endpoint="bot_token_webhook",
        view_func=webhook,
        methods=["POST", "GET"]
    )

# ---------------------------------------------------------
# 8. تشغيل البوت (Polling للبيئة المحلية)
# ---------------------------------------------------------

if __name__ == "__main__":
    if telegram_app:
        logger.info("🚀 جاري تشغيل البوت بنظام Polling...")
        telegram_app.run_polling(drop_pending_updates=True)
