from __future__ import annotations

from flask import Blueprint

bp = Blueprint("main", __name__)


@bp.route("/")
def index() -> str:
    """Root landing page placeholder."""
    return "Welcome to the Reflex Agent Demo"


__all__ = ["bp"]
