import asyncio
import logging
import os
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)

from config import Config

# استيراد مرن يتوافق مع هيكل الملفات
try:
    from database.connection import init_db
    from services.bank import bank
    from services.scoring import evaluate_all_finished_matches
    from handlers.user_handlers import (
        start_handler, refresh_data_handler, todays_matches_handler,
        live_matches_handler, user_profile_handler, leaderboard_handler,
        callback_query_handler
    )
    from handlers.admin_handlers import (
        admin_panel_handler, system_stats_handler,
        force_sync_and_eval_handler, admin_users_handler
    )
    from utils.state_manager import state_manager
except ModuleNotFoundError:
    from connection import init_db
    from bank import bank
    from scoring import evaluate_all_finished_matches
    from user_handlers import (
        start_handler, refresh_data_handler, todays_matches_handler,
        live_matches_handler, user_profile_handler, leaderboard_handler,
        callback_query_handler
    )
    from admin_handlers import (
        admin_panel_handler, system_stats_handler,
        force_sync_and_eval_handler, admin_users_handler
    )
    from state_manager import state_manager

# إعداد السجلات
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 1. إنشاء تطبيق Flask
app = Flask(__name__)

# 2. إنشاء تطبيق التلجرام
telegram_app = Application.builder().token(Config.BOT_TOKEN).build()

# ---------------------------------------------------------
# المهام المجدولة الآلية في الخلفية
# ---------------------------------------------------------

def scheduled_live_update_and_evaluation():
    try:
        bank.sync_live_matches()
        evaluate_all_finished_matches()
    except Exception as e:
        logger.error(f"خطأ في المهمة المجدولة: {e}")

def scheduled_daily_matches_sync():
    try:
        bank.sync_todays_matches()
    except Exception as e:
        logger.error(f"خطأ في مزامنة المباريات: {e}")

def setup_handlers(application: Application):
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("admin", admin_panel_handler))

    application.add_handler(MessageHandler(filters.Regex("^⚽ مباريات اليوم والتوقعات$"), todays_matches_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔴 المباريات المباشرة$"), live_matches_handler))
    application.add_handler(MessageHandler(filters.Regex("^📊 رصيدي وتوقعاتي$"), user_profile_handler))
    application.add_handler(MessageHandler(filters.Regex("^🏆 جدول الترتيب$"), leaderboard_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔄 تحديث البيانات$"), refresh_data_handler))

    application.add_handler(MessageHandler(filters.Regex("^📊 إحصائيات النظام$"), system_stats_handler))
    application.add_handler(MessageHandler(filters.Regex("^⚡ مزامنة وتقييم آلي$"), force_sync_and_eval_handler))
    application.add_handler(MessageHandler(filters.Regex("^👥 إدارة المستخدمين$"), admin_users_handler))
    application.add_handler(MessageHandler(filters.Regex("^⬅️ القائمة الرئيسية$"), start_handler))

    application.add_handler(CallbackQueryHandler(callback_query_handler))

# ---------------------------------------------------------
# التهيئة الأولية وتفعيل الـ Webhook
# ---------------------------------------------------------

async def initialize_app():
    init_db()
    setup_handlers(telegram_app)
    await telegram_app.initialize()

    # تفعيل الـ Webhook تلقائياً لدى تلجرام
    if Config.WEBHOOK_URL:
        base_url = Config.WEBHOOK_URL.rstrip("/")
        target_webhook = f"{base_url}/webhook"
        await telegram_app.bot.set_webhook(url=target_webhook)
        logger.info(f"🌐 تم تسجيل الـ Webhook بنجاح لدى تلجرام: {target_webhook}")

try:
    asyncio.run(initialize_app())

    # تشغيل المجدول الآلي
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(scheduled_live_update_and_evaluation, 'interval', minutes=2)
    scheduler.add_job(scheduled_daily_matches_sync, 'interval', hours=1)
    scheduler.add_job(state_manager.cleanup_expired_states, 'interval', minutes=30)
    scheduler.start()

    bank.sync_todays_matches()
    logger.info("✅ تم تهيئة البوت والمجدول بنجاح.")
except Exception as e:
    logger.error(f"⚠️ تنبيه أثناء التهيئة: {e}")

# ---------------------------------------------------------
# مسارات السيرفر (Endpoints)
# ---------------------------------------------------------

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "bot": "online"}), 200

@app.route("/webhook", methods=["POST", "GET"])
@app.route(f"/{Config.BOT_TOKEN}", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "webhook endpoint active"}), 200

    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = Update.de_json(json_string, telegram_app.bot)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.process_update(update))
        loop.close()

        return "OK", 200
    return "Forbidden", 403

if __name__ == "__main__":
    telegram_app.run_polling(drop_pending_updates=True)
