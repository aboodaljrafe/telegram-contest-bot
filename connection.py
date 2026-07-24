import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ضبط إعدادات الاتصال لتناسب SQLite و PostgreSQL
connect_args = {"check_same_thread": False} if Config.DATABASE_URL.startswith("sqlite") else {}

# إنشاء المحرك مع حماية للاتصالات الميتة وإعادة التدوير
engine = create_engine(
    Config.DATABASE_URL,
    pool_pre_ping=True,       # يفحص سلامة الاتصال قبل تنفيذ أي استعلام
    pool_recycle=3600,         # يعيد فتح الاتصال كل ساعة لتجنب الفصل المفاجئ
    connect_args=connect_args
)

# مصنع الجلسات الآمن متعدد المسارات (Thread-Safe)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# القاعدة الأساسية لنماذج البيانات
Base = declarative_base()


def init_db():
    """إنشاء جميع الجداول تلقائياً عند التشغيل الأول"""
    try:
        import database.models  # تحميل النماذج لضمان التعرف عليها
        Base.metadata.create_all(bind=engine)
        logger.info("تم تهيئة جداول قاعدة البيانات بنجاح.")
    except SQLAlchemyError as e:
        logger.error(f"فشل في تهيئة قاعدة البيانات: {e}")
        raise e


@contextmanager
def get_db():
    """
    سياق معالجة أمان الجلسات (Context Manager).
    يقوم بحفظ التغيرات تلقائياً (Commit) وإذا حدث خطأ يرجع عنها (Rollback) ثم يغلق الجلسة.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"خطأ في جلسة قاعدة البيانات: {e}")
        raise
    finally:
        session.close()

