import logging
from datetime import datetime
import requests

from config import Config
from connection import get_db
from models import Match, SystemCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FootballDataBank:
    def __init__(self):
        self.base_url = Config.FOOTBALL_API_URL
        self.headers = {"X-Auth-Token": Config.FOOTBALL_API_KEY}

    def get_cached_response(self, cache_key: str, max_age_seconds: int = Config.CACHE_TIMEOUT):
        with get_db() as db:
            cache = db.query(SystemCache).filter(SystemCache.key == cache_key).first()
            if cache:
                age = (datetime.utcnow() - cache.updated_at).total_seconds()
                if age < max_age_seconds:
                    return cache.data
        return None

    def save_cache_response(self, cache_key: str, data: dict):
        with get_db() as db:
            cache = db.query(SystemCache).filter(SystemCache.key == cache_key).first()
            if cache:
                cache.data = data
                cache.updated_at = datetime.utcnow()
            else:
                cache = SystemCache(key=cache_key, data=data)
                db.add(cache)

    def _map_status(self, api_status: str) -> str:
        mapping = {
            "SCHEDULED": "NS", "TIMED": "NS", "IN_PLAY": "LIVE",
            "PAUSED": "HT", "FINISHED": "FT", "SUSPENDED": "SUSP",
            "POSTPONED": "PST", "CANCELLED": "CANC"
        }
        return mapping.get(api_status, api_status)

    def sync_todays_matches(self, target_date: str = None) -> list:
        if not target_date:
            target_date = datetime.utcnow().strftime("%Y-%m-%d")

        cache_key = f"fd_matches_{target_date}"
        cached_data = self.get_cached_response(cache_key, max_age_seconds=900)

        if cached_data:
            fixtures = cached_data
        else:
            try:
                url = f"{self.base_url}/matches"
                params = {"dateFrom": target_date, "dateTo": target_date}
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                if response.status_code != 200:
                    return []
                data = response.json()
                fixtures = data.get("matches", [])
                if fixtures:
                    self.save_cache_response(cache_key, fixtures)
            except Exception as e:
                logger.error(f"خطأ اتصال بـ API: {e}")
                return []

        saved_matches = []
        with get_db() as db:
            for item in fixtures:
                api_id = item.get("id")
                if not api_id:
                    continue

                match = db.query(Match).filter(Match.api_match_id == api_id).first()
                status = self._map_status(item.get("status", "SCHEDULED"))
                score_data = item.get("score", {}).get("fullTime", {})
                
                utc_date_str = item.get("utcDate", "")
                match_date = datetime.fromisoformat(utc_date_str.replace("Z", "+00:00")) if utc_date_str else datetime.utcnow()

                if not match:
                    match = Match(
                        api_match_id=api_id,
                        league_name=item.get("competition", {}).get("name", "بطولة عامة"),
                        home_team=item.get("homeTeam", {}).get("name", "المضيف"),
                        away_team=item.get("awayTeam", {}).get("name", "الضيف"),
                        home_logo=item.get("homeTeam", {}).get("crest"),
                        away_logo=item.get("awayTeam", {}).get("crest"),
                        match_date=match_date.replace(tzinfo=None),
                        status=status,
                        home_score=score_data.get("home"),
                        away_score=score_data.get("away")
                    )
                    db.add(match)
                else:
                    match.status = status
                    match.home_score = score_data.get("home")
                    match.away_score = score_data.get("away")

                saved_matches.append(match)

        return saved_matches

    def sync_live_matches(self):
        try:
            url = f"{self.base_url}/matches"
            params = {"status": "IN_PLAY"}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code != 200:
                return
            fixtures = response.json().get("matches", [])
            
            with get_db() as db:
                for item in fixtures:
                    match = db.query(Match).filter(Match.api_match_id == item.get("id")).first()
                    if match:
                        score_data = item.get("score", {}) .get("fullTime", {})
                        match.status = self._map_status(item.get("status"))
                        match.home_score = score_data.get("home")
                        match.away_score = score_data.get("away")
        except Exception as e:
            logger.error(f"خطأ التحديث المباشر: {e}")

bank = FootballDataBank()
