import logging
from datetime import datetime, timedelta
import requests

from config import Config
from database.connection import get_db
from database.models import Match, SystemCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FootballDataBank:
    """
    خدمة إدارة جلب بيانات المباريات والإحصائيات من الـ API المجاني
    مع طبقة التخزين المؤقت (Caching) للتوفير في حدود الطلبات المسموحة.
    """

    def __init__(self):
        self.base_url = Config.FOOTBALL_API_URL
        self.headers = {
            "x-rapidapi-key": Config.FOOTBALL_API_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

    def get_cached_response(self, cache_key: str, max_age_seconds: int = Config.CACHE_TIMEOUT):
        """استرجاع الاستجابة المحفوظة موقتاً إن وجِدَت ولم تنتهي صلاحيتها"""
        with get_db() as db:
            cache = db.query(SystemCache).filter(SystemCache.key == cache_key).first()
            if cache:
                age = (datetime.utcnow() - cache.updated_at).total_seconds()
                if age < max_age_seconds:
                    return cache.data
        return None

    def save_cache_response(self, cache_key: str, data: dict):
        """حفظ رد الـ API في جدول الكاش محلياً"""
        with get_db() as db:
            cache = db.query(SystemCache).filter(SystemCache.key == cache_key).first()
            if cache:
                cache.data = data
                cache.updated_at = datetime.utcnow()
            else:
                cache = SystemCache(key=cache_key, data=data)
                db.add(cache)

    def sync_todays_matches(self, target_date: str = None) -> list:
        """
        جلب وحفظ مباريات اليوم (أو تاريخ معين YYYY-MM-DD) في قاعدة البيانات.
        """
        if not target_date:
            target_date = datetime.utcnow().strftime("%Y-%m-%d")

        cache_key = f"fixtures_{target_date}"
        cached_data = self.get_cached_response(cache_key, max_age_seconds=1800)  # كاش 30 دقيقة للمباريات القادمة

        if cached_data:
            fixtures = cached_data
        else:
            try:
                url = f"{self.base_url}/fixtures"
                params = {"date": target_date}
                response = requests.get(url, headers=self.headers, params=params, timeout=10)

                if response.status_code != 200:
                    logger.error(f"فشل جلب المباريات من الـ API (الكود: {response.status_code})")
                    return []

                data = response.json()
                fixtures = data.get("response", [])
                if fixtures:
                    self.save_cache_response(cache_key, fixtures)
            except requests.RequestException as e:
                logger.error(f"خطأ اتصالات عند جلب المباريات: {e}")
                return []

        saved_matches = []
        with get_db() as db:
            for item in fixtures:
                fixture_info = item.get("fixture", {})
                teams_info = item.get("teams", {})
                goals_info = item.get("goals", {})
                league_info = item.get("league", {})

                api_id = fixture_info.get("id")
                if not api_id:
                    continue

                # تحويل تاريخ ووقت المباراة
                raw_date = fixture_info.get("date", "")
                match_date_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else datetime.utcnow()
                status_short = fixture_info.get("status", {}).get("short", "NS")

                # البحث عن المباراة أو إضافتها
                match = db.query(Match).filter(Match.api_match_id == api_id).first()
                if not match:
                    match = Match(
                        api_match_id=api_id,
                        league_name=league_info.get("name", "دوري غير معروف"),
                        league_id=league_info.get("id"),
                        home_team=teams_info.get("home", {}).get("name", "المضيف"),
                        away_team=teams_info.get("away", {}).get("name", "الضيف"),
                        home_logo=teams_info.get("home", {}).get("logo"),
                        away_logo=teams_info.get("away", {}).get("logo"),
                        match_date=match_date_utc.replace(tzinfo=None),
                        status=status_short,
                        home_score=goals_info.get("home"),
                        away_score=goals_info.get("away")
                    )
                    db.add(match)
                else:
                    match.status = status_short
                    match.home_score = goals_info.get("home")
                    match.away_score = goals_info.get("away")

                saved_matches.append(match)

        return saved_matches

    def sync_live_matches(self):
        """
        جلب المباريات الجارية حالياً وتحديث نتائجها وإحصائياتها.
        """
        cache_key = "live_matches"
        cached_data = self.get_cached_response(cache_key, max_age_seconds=60)  # كاش دقيقة واحدة للمباشر

        if cached_data:
            live_fixtures = cached_data
        else:
            try:
                url = f"{self.base_url}/fixtures"
                params = {"live": "all"}
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                if response.status_code != 200:
                    return []
                data = response.json()
                live_fixtures = data.get("response", [])
                self.save_cache_response(cache_key, live_fixtures)
            except requests.RequestException as e:
                logger.error(f"خطأ في جلب المباريات المباشرة: {e}")
                return []

        with get_db() as db:
            for item in live_fixtures:
                fixture_info = item.get("fixture", {})
                goals_info = item.get("goals", {})
                api_id = fixture_info.get("id")

                match = db.query(Match).filter(Match.api_match_id == api_id).first()
                if match:
                    match.status = fixture_info.get("status", {}).get("short", "LIVE")
                    match.home_score = goals_info.get("home")
                    match.away_score = goals_info.get("away")

                    # تحديث إحصائيات المباراة الجارية تلقائياً
                    stats = self.fetch_match_statistics(api_id)
                    if stats:
                        match.statistics = stats

    def fetch_match_statistics(self, api_match_id: int) -> dict:
        """
        جلب الإحصائيات تفصيلياً (الاستحواذ، التسديدات، الكروت...)
        """
        cache_key = f"stats_{api_match_id}"
        cached_stats = self.get_cached_response(cache_key, max_age_seconds=300)
        if cached_stats:
            return cached_stats

        try:
            url = f"{self.base_url}/fixtures/statistics"
            params = {"fixture": api_match_id}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code != 200:
                return {}

            data = response.json().get("response", [])
            stats_formatted = {}
            for team_data in data:
                team_name = team_data.get("team", {}).get("name")
                statistics = {s["type"]: s["value"] for s in team_data.get("statistics", [])}
                stats_formatted[team_name] = statistics

            if stats_formatted:
                self.save_cache_response(cache_key, stats_formatted)
            return stats_formatted
        except requests.RequestException as e:
            logger.error(f"خطأ جلب إحصائيات المباراة {api_match_id}: {e}")
            return {}

    def fetch_player_of_the_match(self, api_match_id: int) -> str:
        """
        استخراج رجل المباراة (Man of the Match) تلقائياً بناءً على تقييمات اللاعبين.
        """
        try:
            url = f"{self.base_url}/fixtures/players"
            params = {"fixture": api_match_id}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code != 200:
                return "غير محدد"

            data = response.json().get("response", [])
            top_player = None
            top_rating = 0.0

            for team_data in data:
                for player_info in team_data.get("players", []):
                    for item in player_info.get("statistics", []):
                        games = item.get("games", {})
                        rating = games.get("rating")
                        if rating:
                            try:
                                r_float = float(rating)
                                if r_float > top_rating:
                                    top_rating = r_float
                                    top_player = player_info.get("player", {}).get("name")
                            except ValueError:
                                continue
            return top_player if top_player else "غير محدد"
        except Exception as e:
            logger.error(f"خطأ في تحديد رجل المباراة: {e}")
            return "غير محدد"


# كائن منفرد للاستخدام في جميع أجزاء المشروع
bank = FootballDataBank()
