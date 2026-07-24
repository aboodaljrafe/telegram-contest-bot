import asyncio
import logging
import os
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import Config
from connection import init_db
from bank import bank
from scoring import evaluate_all_finished_matches
from user_handlers import (
    start_handler, todays_matches_handler, live_matches_handler,
    user_profile_handler, leaderboard_handler, callback_query_handler, text_message_handler
)
from admin_handlers import (
    admin_panel_handler, system_stats_handler, force_sync_and_eval_handler,
    admin_users_handler, start_add_match_manual, start_set_result_manual,
    refresh_data_handler, admin_text_handler, admin_callback_handler
)
from state_manager import state_manager

# 1. Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Flask App
app = Flask(__name__)
bot_token = (Config.BOT_TOKEN or "").strip()

# 3. Telegram App
telegram_app = None
if bot_token:
    try:
        telegram_app = Application.builder().token(bot_token).build()
        logger.info("✅ تم إنشاء تطبيق التلجرام")
    except Exception as e:
        logger.error(f"❌ خطأ إنشاء التلجرام: {e}")

# 4. Handlers
async def master_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_text_handler(update, context):
        await text_message_handler(update, context)

async def master_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_callback_handler(update, context):
        await callback_query_handler(update, context)

def setup_handlers(application: Application):
    if not application: return
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("admin", admin_panel_handler))
    application.add_handler(MessageHandler(filters.Regex("^⚽ مباريات اليوم والتوقعات$"), todays_matches_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔴 المباريات المباشرة$"), live_matches_handler))
    application.add_handler(MessageHandler(filters.Regex("^📊 رصيدي وتوقعاتي$"), user_profile_handler))
    application.add_handler(MessageHandler(filters.Regex("^🏆 جدول الترتيب$"), leaderboard_handler))
    application.add_handler(MessageHandler(filters.Regex("^🛠️ لوحة تحكم المشرف$"), admin_panel_handler))
    application.add_handler(MessageHandler(filters.Regex("^➕ إضافة مباراة يدويًا$"), start_add_match_manual))
    application.add_handler(MessageHandler(filters.Regex("^📝 رصد نتيجة مباراة$"), start_set_result_manual))
    application.add_handler(MessageHandler(filters.Regex("^📊 إحصائيات النظام$"), system_stats_handler))
    application.add_handler(MessageHandler(filters.Regex("^👥 إدارة المستخدمين$"), admin_users_handler))
    application.add_handler(MessageHandler(filters.Regex("^🔄 تحديث البيانات$"), refresh_data_handler))
    application.add_handler(MessageHandler(filters.Regex("^⚡ مزامنة وتقييم آلي$"), force_sync_and_eval_handler))
    application.add_handler(MessageHandler(filters.Regex("^⬅️ القائمة الرئيسية$"), start_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, master_text_handler))
    application.add_handler(CallbackQueryHandler(master_callback_handler))

if telegram_app:
    setup_handlers(telegram_app)

# 5. Scheduler Jobs - معالجة آمنة
last_sync_info = {"live": "لم يتم بعد", "today": "لم يتم بعد", "eval": "لم يتم بعد"}
scheduler = BackgroundScheduler(daemon=True)

def safe_job(func, name):
    def wrapper():
        try:
            logger.info(f"⏳ [{name}] بدء المزامنة...")
            result = func()
            # إذا الدالة async
            if asyncio.iscoroutine(result):
                asyncio.run(result)
            last_sync_info[name] = "تم بنجاح"
            logger.info(f"✅ [{name}] انتهى بنجاح")
        except Exception as e:
            last_sync_info[name] = f"خطأ: {e}"
            logger.error(f"❌ [{name}] فشل: {e}", exc_info=True)
    return wrapper

def init_services():
    # يمنع التشغيل المكرر مع gunicorn
    if getattr(init_services, "_initialized", False):
        return
    try:
        init_db()
        logger.info("✅ قاعدة البيانات جاهزة")
        if not scheduler.running:
            scheduler.add_job(safe_job(bank.sync_live_matches, "live"), "interval", minutes=2, id="live", replace_existing=True)
            scheduler.add_job(safe_job(bank.sync_todays_matches, "today"), "interval", hours=1, id="today", replace_existing=True)
            scheduler.add_job(safe_job(evaluate_all_finished_matches, "eval"), "interval", minutes=5, id="eval", replace_existing=True)
            if hasattr(state_manager, "cleanup_expired_states"):
                scheduler.add_job(state_manager.cleanup_expired_states, "interval", minutes=30, id="cleanup", replace_existing=True)
            scheduler.start()
            logger.info("✅ المجدول الآلي اشتغل - ستبدأ طلبات football-data.org الآن")
        init_services._initialized = True
    except Exception as e:
        logger.error(f"❌ خطأ تهيئة الخدمات: {e}", exc_info=True)

# مهم جداً: نشغل الخدمات مباشرة عند استيراد الملف (هذا ما يصلح مشكلة gunicorn)
init_services()

# 6. Webhook Handler
def handle_async_update(update_json):
    if not telegram_app:
        return
    async def process():
        if not telegram_app._initialized:
            await telegram_app.initialize()
        update = Update.de_json(update_json, telegram_app.bot)
        await telegram_app.process_update(update)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process())
    except Exception as e:
        logger.error(f"❌ خطأ معالجة التحديث: {e}")
    finally:
        try: loop.close()
        except: pass

# 7. Flask Routes
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "bot": "online" if telegram_app else "token_missing",
        "scheduler": "running" if scheduler.running else "stopped",
        "last_sync": last_sync_info,
        "football_api": "connected" if os.getenv("FOOTBALL_API_KEY") else "MISSING_FOOTBALL_API_KEY"
    }), 200

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "active", "last_sync": last_sync_info}), 200
    if not telegram_app:
        return jsonify({"error": "BOT_TOKEN missing"}), 500
    json_data = request.get_json(force=True)
    handle_async_update(json_data)
    return "OK", 200

if bot_token:
    app.add_url_rule(f"/{bot_token}", endpoint="bot_token_webhook", view_func=webhook, methods=["POST"])

# 8. Local Run (Polling)
if __name__ == "__main__":
    logger.info("🚀 تشغيل محلي بنظام Polling...")
    if telegram_app:
        telegram_app.run_polling(drop_pending_updates=True)
