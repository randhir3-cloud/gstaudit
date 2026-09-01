"""Application configuration."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

DatabaseProvider = Literal["memory", "postgres"]


@dataclass(frozen=True)
class Settings:
    database_provider: DatabaseProvider
    database_url: str
    echo_sql: bool = False
    job_worker_embedded: bool = True
    job_worker_count: int = 2
    job_poll_interval_ms: int = 500
    auth_disabled: bool = False
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    cors_origins: str = "*"
    rate_limit_disabled: bool = False

    @property
    def is_postgres(self) -> bool:
        return self.database_provider == "postgres"

    @property
    def is_memory(self) -> bool:
        return self.database_provider == "memory"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def _normalize_provider(raw: str) -> DatabaseProvider:
    value = (raw or "memory").strip().lower()
    if value in ("postgres", "postgresql", "pg"):
        return "postgres"
    return "memory"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    provider = _normalize_provider(os.getenv("DATABASE_PROVIDER", "memory"))
    default_url = "postgresql+psycopg://gais:gais@127.0.0.1:5432/gais"
    url = os.getenv("DATABASE_URL", default_url)
    echo = _env_bool("DATABASE_ECHO", False)
    worker_embedded = _env_bool("JOB_WORKER_EMBEDDED", True)
    worker_count = int(os.getenv("JOB_WORKER_COUNT", "2"))
    poll_ms = int(os.getenv("JOB_POLL_INTERVAL_MS", "500"))
    auth_disabled = _env_bool("AUTH_DISABLED", False)
    jwt_secret = os.getenv("JWT_SECRET") or os.getenv("GAIS_JWT_SECRET") or secrets.token_hex(32)
    access_minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
    refresh_days = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    rate_limit_disabled = _env_bool("RATE_LIMIT_DISABLED", False)
    return Settings(
        database_provider=provider,
        database_url=url,
        echo_sql=echo,
        job_worker_embedded=worker_embedded,
        job_worker_count=max(1, worker_count),
        job_poll_interval_ms=max(100, poll_ms),
        auth_disabled=auth_disabled,
        jwt_secret=jwt_secret,
        access_token_minutes=max(5, access_minutes),
        refresh_token_days=max(1, refresh_days),
        cors_origins=cors_origins,
        rate_limit_disabled=rate_limit_disabled,
    )


settings = get_settings()
