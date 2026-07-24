import sqlite3

# اسم ملف قاعدة البيانات المحلي
DB_NAME = "contest_master.db"

def get_db():
    """إنشاء وإرجاع اتصال بقاعدة البيانات مع تفعيل الصفوف كقواميس لتسهيل الاستعلام"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """إنشاء جداول النظام الأساسية تلقائياً إذا لم تكن موجودة"""
    with get_db() as conn:
        # 1. جدول المشتركين والمتسابقين
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone_number TEXT,
                points INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0
            )
        ''')
        
        # 2. جدول المباريات والبطولات
        conn.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT,
                away_team TEXT,
                match_type TEXT,
                start_time TEXT,
                status TEXT DEFAULT 'ACTIVE',
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                api_match_id INTEGER
            )
        ''')
        
        # 3. جدول توقعات المستخدمين للمباريات
        conn.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                user_id INTEGER,
                match_id INTEGER,
                pred_home INTEGER,
                pred_away INTEGER,
                PRIMARY KEY(user_id, match_id)
            )
        ''')
        
        conn.commit()
    print("✅ تم تهيئة قاعدة البيانات والجداول بنجاح.")

# تشغيل التهيئة عند استدعاء الملف مباشرة
if __name__ == "__main__":
    init_db()

