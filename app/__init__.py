from __future__ import annotations

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import CONFIG_MAPPING, Config


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for the Reflex demo app."""

    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    resolved_config = (config_name or os.getenv("FLASK_CONFIG", "development")).lower()
    config_class = CONFIG_MAPPING.get(resolved_config, Config)
    app.config.from_object(config_class)
    app.config.from_pyfile("config.py", silent=True)

    _ensure_directories(app)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"

    _register_blueprints(app)

    return app


def _ensure_directories(app: Flask) -> None:
    upload_dir = Path(app.config["UPLOAD_DIR"])
    scenario_dir = Path(app.config["SCENARIO_DIR"])

    upload_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir.mkdir(parents=True, exist_ok=True)

    _seed_snippets(app, upload_dir)


def _seed_snippets(app: Flask, upload_dir: Path) -> None:
    source_dir = Path(app.root_path).parent / "data" / "snippets"
    if not source_dir.exists():
        return

    target_dir = upload_dir / "snippets"
    target_dir.mkdir(parents=True, exist_ok=True)

    for source_file in source_dir.iterdir():
        if not source_file.is_file():
            continue
        destination = target_dir / source_file.name
        if destination.exists():
            continue
        shutil.copy2(source_file, destination)


def _register_blueprints(app: Flask) -> None:
    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)


__all__ = ["create_app", "db", "login_manager", "csrf"]
