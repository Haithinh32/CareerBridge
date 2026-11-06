from enums.quality import MatchFeature

# Trọng số mặc định của thuật toán khớp (tổng = 1), được thay bởi trọng số học từ phản hồi
DEFAULT_MATCH_WEIGHTS: dict[str, float] = {
    MatchFeature.SKILL.value: 0.45,
    MatchFeature.TEXT.value: 0.15,
    MatchFeature.EXPERIENCE.value: 0.15,
    MatchFeature.LOCATION.value: 0.10,
    MatchFeature.WORK_TYPE.value: 0.05,
    MatchFeature.TITLE.value: 0.10,
}
REQUIRED_SKILL_SHARE: float = 0.8
MIN_FEEDBACK_FOR_TRAINING: int = 20
WEIGHT_SMOOTHING: float = 0.5
MIN_FEATURE_WEIGHT: float = 0.02

RECOMMENDATION_LIMIT: int = 20
MAX_JOBS_FOR_MATCHING: int = 3000
CANDIDATE_RANKING_LIMIT: int = 50

# Kiểm tra chất lượng tin
DUPLICATE_SIMILARITY_THRESHOLD: float = 0.9
SCAM_SCORE_THRESHOLD: float = 0.5
FRESHER_MAX_YEARS: float = 1.0
MIN_DESCRIPTION_LENGTH: int = 80
UNREALISTIC_JUNIOR_SALARY_VND: int = 60_000_000

# Theo dõi chất lượng dữ liệu
FRESHNESS_WINDOW_DAYS: int = 30
QUALITY_HISTORY_WINDOW: int = 7
QUALITY_DROP_THRESHOLD: float = 0.10

USD_TO_VND: int = 25_000
UPLOAD_MAX_SIZE_MB: int = 10
TOP_SKILLS_LIMIT: int = 15
COURSES_PER_SKILL: int = 2
