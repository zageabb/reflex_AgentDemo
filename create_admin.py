"""CLI helper for creating or updating an admin user."""

from __future__ import annotations

import argparse
import getpass
import sys

from app import create_app, db
from app.models import User


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("username", nargs="?", help="Admin username")
    parser.add_argument("password", nargs="?", help="Admin password")
    parser.add_argument("--email", dest="email", help="Optional email address")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update the password if the user already exists",
    )
    return parser


def _resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    username = args.username or input("Username: ")
    password = args.password or getpass.getpass("Password: ")

    if not username:
        raise ValueError("Username cannot be empty")
    if not password:
        raise ValueError("Password cannot be empty")
    return username, password


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        username, password = _resolve_credentials(args)
    except ValueError as exc:  # pragma: no cover - user input branch
        parser.error(str(exc))
    except KeyboardInterrupt:  # pragma: no cover - interactive use
        parser.exit(1, "\nAborted by user.\n")

    app = create_app()

    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            if not args.update:
                parser.error(
                    f"User '{username}' already exists. Use --update to reset the password."
                )
            user.set_password(password)
            user.is_admin = True
            if args.email:
                user.email = args.email
            action = "Updated"
        else:
            user = User(username=username, is_admin=True, email=args.email)
            user.set_password(password)
            db.session.add(user)
            action = "Created"

        db.session.commit()

    print(f"{action} admin user '{username}'.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
