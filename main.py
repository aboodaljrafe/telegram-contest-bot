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

# 2. تهيئة التلجرام بآمان
bot_token = (Config.BOT_TOKEN or "").strip()
telegram_app = None

if bot_token:
    try:
        telegram_app = Application.builder().token(bot_token).build()
    except Exception as e:
        logger.error(f"❌ خطأ أثناء إنشاء تطبيق التلجرام: {e}")

# ---------------------------------------------------------
# تسجيل المعالجات والأزرار
# ---------------------------------------------------------

def setup_handlers(application: Application):
    if not application:
        return
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

if telegram_app:
    setup_handlers(telegram_app)

# ---------------------------------------------------------
# التهيئة التزامنية عند إقلاع السيرفر
# ---------------------------------------------------------

try:
    init_db()
    
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(lambda: bank.sync_live_matches(), 'interval', minutes=2)
    scheduler.add_job(lambda: bank.sync_todays_matches(), 'interval', hours=1)
    scheduler.add_job(state_manager.cleanup_expired_states, 'interval', minutes=30)
    scheduler.start()
    
    logger.info("✅ تم إقلاع المجدول وقاعدة البيانات بنجاح.")
except Exception as e:
    logger.error(f"⚠️ خطأ أثناء تهيئة الخدمات: {e}")

# ---------------------------------------------------------
# معالجة تحديثات Webhook بشكل آمن مع asyncio
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
    finally:
        loop.close()

# ---------------------------------------------------------
# مسارات السيرفر (Endpoints)
# ---------------------------------------------------------

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "bot": "online" if telegram_app else "token_missing"
    }), 200

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "active"}), 200

    if not telegram_app:
        return jsonify({"error": "BOT_TOKEN missing"}), 500

    if request.headers.get("content-type") == "application/json":
        json_data = request.get_json(force=True)
        try:
            handle_async_update(json_data)
        except Exception as e:
            logger.error(f"خطأ أثناء معالجة الـ Webhook: {e}")
        return "OK", 200

    return "Forbidden", 403

if bot_token:
    app.add_url_rule(
        f"/{bot_token}",
        endpoint="bot_token_webhook",
        view_func=webhook,
        methods=["POST", "GET"]
    )

if __name__ == "__main__":
    if telegram_app:
        telegram_app.run_polling(drop_pending_updates=True)
