import logging
from datetime import datetime, timedelta
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateManager:
    """
    مدير الحالات لتحديد حالة المشترك وحفظ البيانات المؤقتة للعمليات 
    (مثل خطوات التوقع أو أدخال البيانات) مع انتهاء صلاحية آلي للجلسات.
    """

    def __init__(self, default_ttl_minutes: int = 15):
        self._states = {}
        self._user_data = {}
        self._timestamps = {}
        self._default_ttl = timedelta(minutes=default_ttl_minutes)
        self._lock = Lock()

    def set_state(self, user_id: int, state: str, data: dict = None):
        """تعيين حالة جديدة للمستخدم وتسجيل وقت بدئها"""
        with self._lock:
            self._states[user_id] = state
            self._user_data[user_id] = data or {}
            self._timestamps[user_id] = datetime.utcnow() + self._default_ttl

    def get_state(self, user_id: int) -> str | None:
        """جلب حالة المستخدم الحالية مع التأكد من عدم انتهاء صلاحيتها"""
        with self._lock:
            if self._is_expired(user_id):
                self._clear_user_state_nolock(user_id)
                return None
            return self._states.get(user_id)

    def get_user_data(self, user_id: int) -> dict:
        """استرجاع البيانات المؤقتة للعملية الحالية"""
        with self._lock:
            if self._is_expired(user_id):
                self._clear_user_state_nolock(user_id)
                return {}
            return self._user_data.get(user_id, {})

    def update_user_data(self, user_id: int, **kwargs):
        """تحديث بيانات جلسة المستخدم وتمديد صلاحيتها"""
        with self._lock:
            if user_id in self._user_data and not self._is_expired(user_id):
                self._user_data[user_id].update(kwargs)
                self._timestamps[user_id] = datetime.utcnow() + self._default_ttl

    def clear_state(self, user_id: int):
        """حذف حالة وجلسة المستخدم تماماً"""
        with self._lock:
            self._clear_user_state_nolock(user_id)

    def _is_expired(self, user_id: int) -> bool:
        """فحص انتهاء وقت الجلسة"""
        if user_id not in self._timestamps:
            return True
        return datetime.utcnow() > self._timestamps[user_id]

    def _clear_user_state_nolock(self, user_id: int):
        """حذف بيانات الجلسة داخلياً بدون قفل"""
        self._states.pop(user_id, None)
        self._user_data.pop(user_id, None)
        self._timestamps.pop(user_id, None)

    def cleanup_expired_states(self):
        """دالة تنظيف تنفذ دورياً لتفريغ الجلسات المهملة من الذاكرة"""
        with self._lock:
            now = datetime.utcnow()
            expired_users = [u_id for u_id, expiry in self._timestamps.items() if now > expiry]
            for u_id in expired_users:
                self._clear_user_state_nolock(u_id)
            if expired_users:
                logger.info(f"تم مسح {len(expired_users)} جلسة منتهية الصلاحية من الذاكرة.")


# كائن عالمي متاح للاستخدام في أي مكان داخل البوت
state_manager = StateManager()
