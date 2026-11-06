"""Học trọng số thuật toán khớp từ phản hồi 'gợi ý có phù hợp không' của ứng viên.

Mỗi phản hồi lưu lại vector đặc trưng tại thời điểm gợi ý. Hồi quy logistic dự đoán
P(phù hợp | đặc trưng); hệ số dương được chuẩn hóa thành trọng số mới, rồi trộn với
trọng số cũ để tránh dao động mạnh khi dữ liệu còn ít.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

from constants import MIN_FEATURE_WEIGHT, MIN_FEEDBACK_FOR_TRAINING, WEIGHT_SMOOTHING

MIN_SAMPLES_PER_CLASS_FOR_CV = 3
MAX_CV_FOLDS = 5


@dataclass
class LearnedWeights:
    weights: dict[str, float]
    metrics: dict[str, float]
    sample_size: int


def learn_weights(
    feature_rows: list[dict[str, float]],
    labels: list[bool],
    previous_weights: dict[str, float],
) -> LearnedWeights | None:
    """Trả về None nếu chưa đủ dữ liệu (ít mẫu hoặc chỉ có một lớp)."""
    if len(feature_rows) < MIN_FEEDBACK_FOR_TRAINING or len(set(labels)) < 2:
        return None

    names = list(previous_weights)
    x = np.array([[row.get(name, 0.0) for name in names] for row in feature_rows])
    y = np.array(labels, dtype=int)

    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(x, y)

    coefs = np.clip(model.coef_[0], 0, None) + MIN_FEATURE_WEIGHT
    learned = coefs / coefs.sum()
    blended = {
        name: WEIGHT_SMOOTHING * previous_weights[name] + (1 - WEIGHT_SMOOTHING) * learned[i]
        for i, name in enumerate(names)
    }
    total = sum(blended.values())
    weights = {name: round(value / total, 4) for name, value in blended.items()}

    metrics: dict[str, float] = {"positive_rate": round(float(y.mean()), 4)}
    min_class = int(min(y.sum(), len(y) - y.sum()))
    if min_class >= MIN_SAMPLES_PER_CLASS_FOR_CV:
        folds = StratifiedKFold(n_splits=min(MAX_CV_FOLDS, min_class), shuffle=True, random_state=42)
        auc = cross_val_score(
            LogisticRegression(class_weight="balanced", max_iter=1000), x, y,
            cv=folds, scoring="roc_auc",
        )
        metrics["cv_auc"] = round(float(auc.mean()), 4)
    return LearnedWeights(weights=weights, metrics=metrics, sample_size=len(y))
