from __future__ import annotations

from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")

# Import routes to register blueprint handlers.
from . import routes  # noqa: E402,F401


__all__ = ["bp"]
