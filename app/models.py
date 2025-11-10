"""Database models for the Reflex demo application."""

from __future__ import annotations

from passlib.hash import bcrypt
from flask_login import UserMixin

from . import db, login_manager


class User(UserMixin, db.Model):
    """Represents an application user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    audit_logs = db.relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""

        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""

        if not self.password_hash:
            return False
        return bcrypt.verify(password, self.password_hash)

    def __repr__(self) -> str:  # pragma: no cover - repr for debugging
        return f"<User {self.username!r}>"


class AuditLog(db.Model):
    """Records user actions for auditing purposes."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:  # pragma: no cover - repr for debugging
        return f"<AuditLog user={self.user_id} action={self.action!r}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Retrieve a user for Flask-Login sessions."""

    if user_id is None:
        return None
    return User.query.get(int(user_id))


__all__ = ["User", "AuditLog", "load_user"]
