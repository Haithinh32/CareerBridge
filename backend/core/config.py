import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes"}


def _get_list(key: str) -> list[str]:
    return [item.strip() for item in os.getenv(key, "").split(",") if item.strip()]


DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./careerbridge.db")
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI: str = os.getenv(
    "LINKEDIN_REDIRECT_URI", "http://localhost:8000/api/auth/linkedin/callback"
)

ENABLE_SCHEDULER: bool = _get_bool("ENABLE_SCHEDULER", False)
SCHEDULER_INTERVAL_MINUTES: int = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))
PARTNER_FEED_URLS: list[str] = _get_list("PARTNER_FEED_URLS")
CRAWL_SEED_URLS: list[str] = _get_list("CRAWL_SEED_URLS")
