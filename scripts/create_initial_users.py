#!/usr/bin/env python3
"""Bootstrap script for initial Superadmin and Admin users in HealthTech Dashboard.

Security guarantees:
1. Passwords are never stored in plaintext - hashed with bcrypt.
2. Passwords and password hashes are never printed to terminal or logs.
3. Loads DATABASE_URL securely from .env.development / environment config.
4. Uses atomic SQLAlchemy transaction with automatic rollback on error.
5. Idempotent: safe to run multiple times without duplicating accounts.

Usage:
    python scripts/create_initial_users.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 1. Resolve project root and load environment variables from .env.development
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

env_development = PROJECT_ROOT / ".env.development"
if env_development.exists():
    load_dotenv(dotenv_path=env_development, override=True)
else:
    load_dotenv(override=True)

# 2. Reuse existing project configuration, database engine, and password hashing utility
from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402

# Credentials definition (kept strictly in memory, never logged)
INITIAL_USERS = [
    {
        "role_name": "superadmin",
        "email": "superadmin@3401.com",
        "name": "Super Administrator",
        "password": "Superadmin3401",
        "label": "Superadmin",
    },
    {
        "role_name": "admin",
        "email": "admin@3401.com",
        "name": "System Administrator",
        "password": "Admin3401",
        "label": "Admin",
    },
]


def bootstrap_users() -> None:
    """Connects to database, validates roles, and creates initial users safely."""
    # Ensure database is accessible
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(
            f"Error: Could not connect to PostgreSQL database. Check DATABASE_URL configuration: {exc}"
        )
        sys.exit(1)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    # Verify required tables exist
    if "roles" not in table_names:
        print(
            "Error: 'roles' table does not exist in the database. Ensure database migrations or seed scripts have run."
        )
        sys.exit(1)

    if "users" not in table_names:
        print(
            "Error: 'users' table does not exist in the database. Ensure database migrations or seed scripts have run."
        )
        sys.exit(1)

    role_cols = {c["name"] for c in inspector.get_columns("roles")}
    name_col = "name" if "name" in role_cols else "slug" if "slug" in role_cols else None
    if not name_col:
        print("Error: Could not find role name column in 'roles' table.")
        sys.exit(1)

    user_cols = {c["name"] for c in inspector.get_columns("users")}

    session = SessionLocal()
    try:
        # Step 3 & 4: Find roles 'superadmin' and 'admin'
        roles_map: dict[str, Any] = {}
        for user_spec in INITIAL_USERS:
            target_role = user_spec["role_name"]
            role_record = (
                session.execute(
                    text(f"SELECT id, {name_col} FROM roles WHERE {name_col} = :role_name"),
                    {"role_name": target_role},
                )
                .mappings()
                .first()
            )

            # Step 5: Stop execution if either role does not exist
            if not role_record:
                print(f"Error: Role '{target_role}' does not exist in the database.")
                sys.exit(1)

            roles_map[target_role] = role_record["id"]

        # Step 6 & 7: Check if users already exist
        users_to_create = []
        for user_spec in INITIAL_USERS:
            email = user_spec["email"]
            label = user_spec["label"]
            existing_user = (
                session.execute(
                    text("SELECT id, email FROM users WHERE email = :email"),
                    {"email": email},
                )
                .mappings()
                .first()
            )

            # Step 8: Safe message if user already exists
            if existing_user:
                print(f"{label} user already exists.")
            else:
                users_to_create.append(user_spec)

        # If all users already exist, exit cleanly
        if not users_to_create:
            return

        # Step 9 & 10: Insert within safe SQLAlchemy transaction
        with session.begin():
            for user_spec in users_to_create:
                role_id = roles_map[user_spec["role_name"]]
                password_hash = hash_password(user_spec["password"])

                record: dict[str, Any] = {
                    "email": user_spec["email"],
                }

                # Set hashed password column
                if "password_hash" in user_cols:
                    record["password_hash"] = password_hash
                elif "hashed_password" in user_cols:
                    record["hashed_password"] = password_hash
                else:
                    record["password_hash"] = password_hash

                # Set name column
                if "name" in user_cols:
                    record["name"] = user_spec["name"]
                elif "full_name" in user_cols:
                    record["full_name"] = user_spec["name"]

                # Set role_id foreign key
                if "role_id" in user_cols:
                    record["role_id"] = role_id

                # Set role string/enum if column exists
                if "role" in user_cols:
                    record["role"] = user_spec["role_name"]

                # Set active status
                if "is_active" in user_cols:
                    record["is_active"] = True

                # Timestamps
                now = datetime.now(timezone.utc)
                if "created_at" in user_cols:
                    record["created_at"] = now
                if "updated_at" in user_cols:
                    record["updated_at"] = now

                # Construct parameterized INSERT statement
                cols = ", ".join(record.keys())
                placeholders = ", ".join(f":{k}" for k in record.keys())
                insert_query = text(f"INSERT INTO users ({cols}) VALUES ({placeholders})")

                session.execute(insert_query, record)
                print(f"{user_spec['label']} user created successfully.")

    except SQLAlchemyError as db_err:
        # Step 11: Rollback on error
        session.rollback()
        print(f"Database error during user bootstrap: {db_err}")
        sys.exit(1)
    except Exception as exc:
        session.rollback()
        print(f"Unexpected error during user bootstrap: {exc}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    bootstrap_users()
