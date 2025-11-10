from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATA_DIR = BASE_DIR / "data"


def _parse_extensions(raw: str | None, default: Iterable[str]) -> set[str]:
    if not raw:
        return {ext if ext.startswith(".") else f".{ext}" for ext in default}
    extensions = set()
    for value in raw.split(","):
        cleaned = value.strip()
        if not cleaned:
            continue
        extensions.add(cleaned if cleaned.startswith(".") else f".{cleaned}")
    return extensions


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SCENARIO_DIR = DATA_DIR / "scenarios"
    UPLOAD_DIR = INSTANCE_DIR / "uploads"

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'app.db'}"
    )
    UPLOAD_EXTENSIONS = _parse_extensions(
        os.getenv("UPLOAD_EXTENSIONS"),
        {".txt", ".md", ".json", ".pdf"},
    )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


CONFIG_MAPPING = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
