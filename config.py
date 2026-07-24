import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env أثناء التطوير المحلي
load_dotenv()

class Config:
    # 1. توكن البوت المأخوذ من BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    # 2. الآيدي الرقمي للمشرف الأساسي
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

    # 3. مفتاح API لجلب البيانات من Football-Data.org (مجاني)
    FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")

    # 4. اسم قاعدة البيانات المحلية
    DATABASE_NAME = os.getenv("DATABASE_NAME", "contest_master.db")

    # 5. منفذ السيرفر (يقوم سيرفر Railway بتحديده تلقائياً)
    PORT = int(os.getenv("PORT", 5000))

    @classmethod
    def validate(cls):
        """التحقق من وجود المتغيرات الحساسة عند بدء التشغيل"""
        if not cls.BOT_TOKEN:
            raise ValueError("❌ خطأ حرج: لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")
        if cls.ADMIN_ID == 0:
            print("⚠️ تنبيه: لم يتم ضبط ADMIN_ID بشكل صحيح، لن تظهر لوحة المشرف.")

