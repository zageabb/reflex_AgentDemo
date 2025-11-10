from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Type

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import CONFIG_MAPPING, Config
from data.snippets import sync_snippet_tree


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

    from . import models  # noqa: F401  # Ensure models are registered

    _register_blueprints(app)
    _initialize_database(app)

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

    sync_snippet_tree(source_dir, upload_dir)


def _register_blueprints(app: Flask) -> None:
    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)


def _initialize_database(app: Flask) -> None:
    """Create database tables and seed initial data."""

    from .models import User

    with app.app_context():
        db.create_all()
        _seed_admin_user(User)


if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from .models import User


def _seed_admin_user(user_model: Type["User"]) -> None:
    """Create an initial admin user from environment variables."""

    username = os.getenv("ADMIN_USER")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        return

    existing_user = user_model.query.filter_by(username=username).first()
    if existing_user:
        return

    admin_user = user_model(username=username, is_admin=True)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()


__all__ = ["create_app", "db", "login_manager", "csrf"]
