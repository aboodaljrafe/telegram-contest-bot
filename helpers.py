import re
from datetime import datetime
import html
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def escape_html_text(text: str) -> str:
    """
    تشفير نصوص HTML لتجنب انهيار البوت عند إرسال أسماء الفرق أو المستخدمين 
    التي تحتوى على رموز مثل (<, >, &).
    """
    if not text:
        return ""
    return html.escape(str(text))


def validate_phone_number(phone: str) -> bool:
    """
    التحقق من صحة رقم الهاتف للمستقبل (يدعم الأرقام الدولية والمحلية مع + أو بدونها).
    مثال: +966501234567 أو 0501234567
    """
    pattern = r"^\+?[1-9]\d{1,14}$"
    clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(re.match(pattern, clean_phone))


def format_match_status(status_code: str) -> str:
    """
    تحويل أكواد حالة المباراة من الـ API إلى مصطلحات عربية واضحة.
    """
    statuses = {
        "TBD": "⏳ لم يحدد الوقت",
        "NS": "⏳ لم تبدأ",
        "1H": "🟢 الشوط الأول",
        "HT": "⏸️ استراحة الشوطين",
        "2H": "🟢 الشوط الثاني",
        "ET": "⏱️ شوط إضافي",
        "BT": "⏱️ استراحة وقت إضافي",
        "P": "🥅 ركلات ترجيح",
        "SUSP": "⚠️ معلقة",
        "INT": "⚠️ توقفت",
        "FT": "🔴 انتهت",
        "AET": "🔴 انتهت (وقت إضافي)",
        "PEN": "🔴 انتهت (ركلات ترجيح)",
        "PST": "📅 تم تأجيلها",
        "CANC": "❌ تم إلغاؤها",
        "ABD": "❌ تم إلغاء اللقاء",
        "AWD": "🏆 فوز تقني",
        "WO": "🏆 انسحاب"
    }
    return statuses.get(status_code, f"🔄 {status_code}")


def format_datetime_to_arabic(dt: datetime) -> str:
    """
    تنسيق الوقت والتاريخ إلى صيغة عربية سهلة القراءة.
    مثال: 2026-07-24 18:30 -> 18:30 (24/07/2026)
    """
    if not dt:
        return "غير محدد"
    return dt.strftime("%H:%M (%Y/%m/%d)")


def truncate_string(text: str, max_length: int = 30) -> str:
    """
    قص النصوص الطويلة (مثل أسماء الفرق) لضمان عدم خروجها عن حدود أزرار تلجرام.
    """
    if not text:
        return ""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

