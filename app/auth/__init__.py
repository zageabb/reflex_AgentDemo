from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/status")
def status() -> tuple[dict[str, str], int]:
    """Simple endpoint to verify the auth blueprint is registered."""
    return jsonify({"status": "auth-ready"}), 200


__all__ = ["bp"]
