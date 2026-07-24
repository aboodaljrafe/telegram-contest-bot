import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_match_summary(home_team: str, away_team: str, home_score=None, away_score=None) -> str:
    if home_score is not None and away_score is not None:
        return f"{home_team} {home_score} - {away_score} {away_team}"
    return f"{home_team} vs {away_team}"
