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
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

from passlib.hash import bcrypt

from ..models import User
from . import bp


_DUMMY_PASSWORD_HASH = bcrypt.hash("dummy-password")


class LoginForm(FlaskForm):
    """Login form that authenticates via email and password."""

    email = EmailField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"autocomplete": "email"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=255)],
        render_kw={"autocomplete": "current-password"},
    )
    submit = SubmitField("Sign In")


def _verify_password(stored_hash: str, candidate: str) -> bool:
    """Verify a plaintext password against a stored hash safely."""

    try:
        return bcrypt.verify(candidate, stored_hash)
    except ValueError:
        return False


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
        email_input = form.email.data.strip().lower()
        user = User.query.filter(func.lower(User.email) == email_input).first()

        password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
        password_matches = _verify_password(password_hash, form.password.data)
        stored_email = (user.email or "").lower() if user else ""
        email_matches = user is not None and secrets.compare_digest(
            stored_email, email_input
        )

        if user and email_matches and password_matches:
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
