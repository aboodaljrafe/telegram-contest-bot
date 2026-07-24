import logging
from connection import get_db
from models import Match, Prediction, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_points(predicted_home: int, predicted_away: int, actual_home: int, actual_away: int) -> int:
    if predicted_home == actual_home and predicted_away == actual_away:
        return 3  # النتيجة الدقيقة
    
    pred_diff = predicted_home - predicted_away
    actual_diff = actual_home - actual_away
    
    if (pred_diff > 0 and actual_diff > 0) or (pred_diff < 0 and actual_diff < 0) or (pred_diff == 0 and actual_diff == 0):
        return 1  # الفريق الفائز أو التعادل
    
    return 0  # توقع خاطئ


def evaluate_all_finished_matches():
    with get_db() as db:
        unprocessed_matches = db.query(Match).filter(
            Match.status == "FT",
            Match.is_evaluated == False,
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()

        for match in unprocessed_matches:
            predictions = db.query(Prediction).filter(Prediction.match_id == match.id).all()
            for pred in predictions:
                points = calculate_points(
                    pred.predicted_home_score,
                    pred.predicted_away_score,
                    match.home_score,
                    match.away_score
                )
                pred.points_earned = points
                
                user = db.query(User).filter(User.id == pred.user_id).first()
                if user:
                    user.total_points += points

            match.is_evaluated = True

        db.commit()
