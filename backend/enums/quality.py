from enum import Enum


class QualityMetric(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    FRESHNESS = "freshness"
    UNIQUENESS = "uniqueness"


class MatchFeature(str, Enum):
    SKILL = "skill"
    TEXT = "text"
    EXPERIENCE = "experience"
    LOCATION = "location"
    WORK_TYPE = "work_type"
    TITLE = "title"
