import logging
from database.connection import get_db
from database.models import Match, Prediction, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# قواعد احتساب النقاط
EXACT_SCORE_POINTS = 3      # نقاط التوقع الدقيق للنتيجة
CORRECT_OUTCOME_POINTS = 1  # نقاط توقع الفائز أو التعادل
WRONG_PREDICTION_POINTS = 0 # نقاط التوقع الخاطئ


def calculate_prediction_points(pred_home: int, pred_away: int, actual_home: int, actual_away: int) -> tuple[int, bool]:
    """
    حساب النقاط المستحقة للتوقع بناءً على النتيجة الفعلية:
    - نتيجة دقيقة (Exact Score): 3 نقاط + علامة توقع دقيق.
    - توقع الفائز/التعادل صحيح (Correct Outcome): 1 نقطة.
    - توقع خاطئ: 0 نقاط.
    """
    # 1. التوقع الدقيق للنتيجة
    if pred_home == actual_home and pred_away == actual_away:
        return EXACT_SCORE_POINTS, True

    # 2. تحديد اتجاه التوقع والنتيجة الفعلية (فوز/تعادل/خسارة)
    pred_diff = pred_home - pred_away
    actual_diff = actual_home - actual_away

    # هل تتطابق هوية الفائز أو حالة التعادل؟
    if (pred_diff > 0 and actual_diff > 0) or \
       (pred_diff < 0 and actual_diff < 0) or \
       (pred_diff == 0 and actual_diff == 0):
        return CORRECT_OUTCOME_POINTS, False

    # 3. توقع خاطئ
    return WRONG_PREDICTION_POINTS, False


def evaluate_match_predictions(match_id: int):
    """
    معالجة وتقييم جميع توقعات مباراة معينة بعد انتهائها،
    إضافة النقاط لرصيد المستخدمين، وتحديث إحصائياتهم.
    """
    with get_db() as db:
        match = db.query(Match).filter(Match.id == match_id).first()

        if not match:
            logger.error(f"المباراة برقم {match_id} غير موجودة.")
            return

        # التأكد من أن المباراة انتهت بالفعل
        if match.status not in ["FT", "AET", "PEN"]:
            logger.warning(f"المباراة {match_id} لم تنتهِ بعد (الحالة الحالية: {match.status}).")
            return

        if match.home_score is None or match.away_score is None:
            logger.warning(f"نتائج المباراة {match_id} غير مكتملة بعد.")
            return

        # جلب التوقعات التي لم يتم تقييمها بعد لتجنب تكرار احتساب النقاط
        unprocessed_predictions = db.query(Prediction).filter(
            Prediction.match_id == match.id,
            Prediction.is_processed == False
        ).all()

        if not unprocessed_predictions:
            logger.info(f"لا توجد توقعات جديدة معلقة للمباراة {match_id}.")
            match.is_evaluated = True
            return

        evaluated_count = 0
        for pred in unprocessed_predictions:
            user = db.query(User).filter(User.id == pred.user_id).first()
            if not user:
                continue

            points, is_exact = calculate_prediction_points(
                pred.predicted_home_score,
                pred.predicted_away_score,
                match.home_score,
                match.away_score
            )

            # تحديث بيانات التوقع
            pred.points_earned = points
            pred.is_processed = True

            # تحديث رصيد وإحصائيات المستخدم
            user.points += points
            user.total_predictions += 1
            if is_exact:
                user.correct_predictions += 1

            evaluated_count += 1

        # علم على المباراة بأنها عولجت بالكامل
        match.is_evaluated = True
        logger.info(f"تمت معالجة {evaluated_count} توقعاً لمباراة ({match.home_team} vs {match.away_team}).")


def evaluate_all_finished_matches():
    """
    فحص ومعالجة كافة المباريات المنتهية التي لم تُقيّم توقعاتها بعد.
    تُستدعى هذه الدالة تلقائياً بواسطة المجدول الدوري.
    """
    with get_db() as db:
        finished_matches = db.query(Match).filter(
            Match.status.in_(["FT", "AET", "PEN"]),
            Match.is_evaluated == False
        ).all()

        match_ids = [m.id for m in finished_matches]

    # تقييم كل مباراة داخل جلسة مستقلة للحفاظ على الاستقرار
    for m_id in match_ids:
        evaluate_match_predictions(m_id)
