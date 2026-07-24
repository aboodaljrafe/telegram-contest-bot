import os

# محاولة تحميل ملف .env محلياً بدون إيقاف السيرفر في البيئات السحابية
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # تحويل آمن لمعرفات المشرفين
    ADMIN_IDS = []
    admin_raw = os.getenv("ADMIN_IDS", "")
    if admin_raw:
        for item in admin_raw.split(","):
            item = item.strip()
            if item.isdigit():
                ADMIN_IDS.append(int(item))

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///contest_bot.db")
    
    # إصلاح تلقائي لروابط PostgreSQL المتوافقة مع SQLAlchemy
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # إعدادات Football-Data.org
    FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
    FOOTBALL_API_URL = os.getenv("FOOTBALL_API_URL", "https://api.football-data.org/v4")
    
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    # تحويل آمن للمنفذ
    try:
        PORT = int(os.getenv("PORT", 5000))
    except (ValueError, TypeError):
        PORT = 5000

    CACHE_TIMEOUT = 300
