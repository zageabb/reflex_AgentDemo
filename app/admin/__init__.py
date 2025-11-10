from __future__ import annotations

from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
def dashboard() -> str:
    """Minimal placeholder for the admin dashboard."""
    return "Admin dashboard"


__all__ = ["bp"]
