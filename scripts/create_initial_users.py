#!/usr/bin/env python3
"""Bootstrap script for initial Superadmin and Admin users in HealthTech Dashboard.

Security guarantees:
1. Passwords are never hardcoded in plaintext.
2. Credentials can be passed via CLI arguments or environment variables:
   - SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD
   - ADMIN_EMAIL / ADMIN_PASSWORD
   If not provided, a cryptographically secure random password is generated and displayed once.
3. Loads DATABASE_URL securely from .env / environment config.
4. Uses atomic SQLAlchemy transaction with automatic rollback on error.
5. Idempotent: safe to run multiple times without duplicating accounts.

Usage:
    python scripts/create_initial_users.py
    python scripts/create_initial_users.py --role superadmin --email admin@example.com --password SecurePass123!
    python scripts/create_initial_users.py --force-update
"""

import argparse
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

# 1. Resolve project root and load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

env_development = PROJECT_ROOT / ".env.development"
env_local = PROJECT_ROOT / ".env"
if env_development.exists():
    load_dotenv(dotenv_path=env_development, override=False)
if env_local.exists():
    load_dotenv(dotenv_path=env_local, override=True)
else:
    load_dotenv(override=True)

# 2. Project configuration, database engine, models, and password hashing
from sqlalchemy import inspect  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from app.core.constants import UserRole  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402
from app.models.user import User  # noqa: E402


def get_default_users() -> List[dict[str, Any]]:
    """Resolve initial users from environment variables or generate secure passwords."""
    superadmin_email = os.getenv("SUPERADMIN_EMAIL", "superadmin@healthtech.local").strip()
    superadmin_password = os.getenv("SUPERADMIN_PASSWORD")
    if not superadmin_password:
        superadmin_password = secrets.token_urlsafe(16)
        print(f"[SECURITY] Generated initial password for {superadmin_email}: {superadmin_password}")

    admin_email = os.getenv("ADMIN_EMAIL", "admin@healthtech.local").strip()
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        admin_password = secrets.token_urlsafe(16)
        print(f"[SECURITY] Generated initial password for {admin_email}: {admin_password}")

    return [
        {
            "role": UserRole.SUPERADMIN,
            "email": superadmin_email,
            "name": "Super Administrator",
            "password": superadmin_password,
            "label": "Superadmin",
        },
        {
            "role": UserRole.ADMIN,
            "email": admin_email,
            "name": "System Administrator",
            "password": admin_password,
            "label": "Admin",
        },
    ]


def bootstrap_users(users_spec: List[dict[str, Any]], force_update: bool = False) -> None:
    """Connects to database, validates tables, and creates initial users safely."""
    try:
        with engine.connect() as conn:
            from sqlalchemy import text

            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print("Error: Could not connect to PostgreSQL database.")
        print(f"Details: {exc}")
        print("\nPlease verify DATABASE_URL in your .env / .env.development configuration.")
        sys.exit(1)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "users" not in table_names:
        print(
            "Error: 'users' table does not exist in the database. "
            "Please run database migrations first:\n"
            "    alembic upgrade head"
        )
        sys.exit(1)

    session = SessionLocal()
    try:
        with session.begin():
            for spec in users_spec:
                email = spec["email"].strip().lower()
                label = spec.get("label", spec["role"].value.capitalize())
                password = spec["password"]
                role = spec["role"]
                name = spec.get("name", label)

                existing = session.query(User).filter(User.email == email).first()

                if existing:
                    if force_update:
                        existing.name = name
                        existing.role = role
                        existing.password_hash = hash_password(password)
                        existing.is_active = True
                        existing.updated_at = datetime.now(timezone.utc)
                        print(f"Updated {label} user ({email}) with new credentials.")
                    else:
                        print(
                            f"{label} user already exists ({email}). (Use --force-update to reset password)"
                        )
                else:
                    new_user = User(
                        email=email,
                        name=name,
                        password_hash=hash_password(password),
                        role=role,
                        is_active=True,
                    )
                    session.add(new_user)
                    print(f"Created {label} user successfully ({email}).")

        print("\nAll initial users processed successfully.")

    except SQLAlchemyError as db_err:
        session.rollback()
        print(f"Database error during user bootstrap: {db_err}")
        sys.exit(1)
    except Exception as exc:
        session.rollback()
        print(f"Unexpected error during user bootstrap: {exc}")
        sys.exit(1)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Bootstrap Superadmin and Admin users.")
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Update existing accounts with new password and name if they already exist",
    )
    parser.add_argument("--email", type=str, help="Custom user email")
    parser.add_argument("--password", type=str, help="Custom user password")
    parser.add_argument("--name", type=str, help="Custom user display name")
    parser.add_argument(
        "--role",
        type=str,
        choices=["superadmin", "admin", "clinician", "nurse"],
        help="Custom user role",
    )

    args = parser.parse_args()

    if args.email and args.password and args.role:
        users = [
            {
                "role": UserRole(args.role),
                "email": args.email,
                "name": args.name or args.email.split("@")[0].capitalize(),
                "password": args.password,
                "label": args.role.capitalize(),
            }
        ]
    else:
        users = get_default_users()

    bootstrap_users(users, force_update=args.force_update)


if __name__ == "__main__":
    main()
