"""Authentication routes for the auth blueprint."""

from __future__ import annotations

import secrets
import time
from flask import flash, redirect, render_template, request, url_for, jsonify
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from sqlalchemy import func
from urllib.parse import urlsplit
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from werkzeug.security import check_password_hash, generate_password_hash

from ..models import User
from . import bp


_DUMMY_PASSWORD_HASH = generate_password_hash("dummy-password")


class LoginForm(FlaskForm):
    """Login form that authenticates via email or username and password."""

    identifier = StringField(
        "Email or Username",
        validators=[DataRequired(), Length(max=255)],
        render_kw={"autocomplete": "username"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=255)],
        render_kw={"autocomplete": "current-password"},
    )
    submit = SubmitField("Sign In")


def _verify_password(stored_hash: str, candidate: str) -> bool:
    """Verify a plaintext password against a stored hash safely."""

    if not stored_hash:
        return False
    return check_password_hash(stored_hash, candidate)


@bp.route("/status")
def status() -> tuple[dict[str, str], int]:
    """Simple endpoint to verify the auth blueprint is registered."""

    return jsonify({"status": "auth-ready"}), 200


@bp.route("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    """Render and process the authentication form."""

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier_raw = form.identifier.data.strip()
        identifier_input = identifier_raw.lower()

        match_attr = None
        user = User.query.filter(func.lower(User.email) == identifier_input).first()
        if user:
            match_attr = "email"
        if not user:
            user = User.query.filter(func.lower(User.username) == identifier_input).first()
            if user:
                match_attr = "username"

        password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
        password_matches = _verify_password(password_hash, form.password.data)

        if match_attr == "email":
            stored_identifier = (user.email or "").lower()
        elif match_attr == "username":
            stored_identifier = (user.username or "").lower()
        else:
            stored_identifier = ""

        identifier_matches = user is not None and secrets.compare_digest(
            stored_identifier, identifier_input
        )

        if user and identifier_matches and password_matches:
            login_user(user)
            flash("Successfully signed in.", "success")
            next_page = request.args.get("next")
            if not next_page or urlsplit(next_page).netloc:
                next_page = url_for("main.index")
            return redirect(next_page)

        time.sleep(0.5)
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout() -> ResponseReturnValue:
    """Log the current user out of their session."""

    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


__all__ = ["login", "logout", "status"]
