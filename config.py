import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


def _get_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = _get_int("PORT", 10000)
    environment: str = os.getenv("ENVIRONMENT", "development").lower()
    secret_key: str | None = os.getenv("SECRET_KEY")
    fernet_key: str | None = os.getenv("FERNET_KEY") or os.getenv("MESSAGE_ENCRYPTION_KEY")
    allowed_origins: list[str] = field(default_factory=_get_origins)
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_upload_size: int = _get_int("MAX_UPLOAD_SIZE", 5 * 1024 * 1024)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
