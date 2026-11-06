from enum import Enum


class JobStatus(str, Enum):
    OPEN = "open"
    QUARANTINED = "quarantined"
    CLOSED = "closed"
    EXPIRED = "expired"
    REJECTED = "rejected"


class JobSource(str, Enum):
    EMPLOYER = "employer"
    PARTNER_FEED = "partner_feed"
    CRAWLER = "crawler"


class WorkType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    REMOTE = "remote"
    HYBRID = "hybrid"


class JobLevel(str, Enum):
    INTERN = "intern"
    FRESHER = "fresher"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


class FlagType(str, Enum):
    DUPLICATE = "duplicate"
    EXPIRED = "expired"
    FRESHER_REQUIRES_EXPERIENCE = "fresher_requires_experience"
    SCAM = "scam"
    INCOMPLETE = "incomplete"


class ReviewAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
