import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

class Config:
    # Telegram Bot Config
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

    # Database Config (Default SQLite for local testing, PostgreSQL for deployment)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///contest_bot.db")

    # Football API Config (e.g. API-Football or Football-Data.org)
    FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "YOUR_FREE_API_KEY")
    FOOTBALL_API_URL = os.getenv("FOOTBALL_API_URL", "https://v3.football.api-sports.io")

    # Webhook / Flask Config
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    PORT = int(os.getenv("PORT", 5000))

    # Cache Control (In seconds to avoid hitting API limits)
    CACHE_TIMEOUT = 300  # 5 minutes
