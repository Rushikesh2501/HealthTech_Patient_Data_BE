"""CLI script to provision an initial administrator account.
Usage:
    python scripts/create_admin.py --email admin@healthtech.local --name "Admin User" --password "SecureAdmin123!"
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.constants import UserRole
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User


def create_admin(email: str, name: str, password: str, role: UserRole = UserRole.ADMIN) -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Error: User with email '{email}' already exists.")
            sys.exit(1)

        admin = User(
            email=email,
            name=name,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Successfully created {role.value.capitalize()} account: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create initial Admin or Superadmin user")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--name", default="System Administrator", help="Admin display name")
    parser.add_argument("--password", help="Admin initial password (generated if omitted)")
    parser.add_argument(
        "--role",
        default="admin",
        choices=["admin", "superadmin"],
        help="Account role (admin or superadmin)",
    )

    args = parser.parse_args()
    password = args.password
    if not password:
        import secrets

        password = secrets.token_urlsafe(16)
        print(f"[SECURITY] Generated initial password: {password}")

    create_admin(args.email, args.name, password, role=UserRole(args.role))
