#!/usr/bin/env python3
"""
Create initial admin user. Run after migrations.
Usage (from services/admin-service): python -m admin_service.scripts.create_admin <email> <password> <name>
"""
import asyncio
import sys
from pathlib import Path

# Ensure admin_service package is importable
# Run from admin-service dir: python scripts/create_admin.py ...
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config.settings import settings
from domain.user.models import AdminUser
from domain.user.repository import hash_password


async def main():
    if len(sys.argv) < 4:
        print("Usage: python -m admin_service.scripts.create_admin <email> <password> <name>")
        sys.exit(1)
    email, password, name = sys.argv[1], sys.argv[2], sys.argv[3]
    if len(password) < 8:
        print("Password must be at least 8 characters")
        sys.exit(1)

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    reset = "--reset" in sys.argv
    super_admin = "--super-admin" in sys.argv
    async with async_session() as session:
        r = await session.execute(select(AdminUser).where(AdminUser.email == email))
        user = r.scalar_one_or_none()
        if user:
            if reset:
                user.password_hash = hash_password(password)
                user.is_active = True
                if super_admin:
                    user.role = "super_admin"
                    print(f"Password updated and promoted to super_admin: {email}")
                else:
                    print(f"Password updated for {email}")
                await session.commit()
            else:
                print(f"User {email} already exists. Use --reset to update password.")
                sys.exit(0)
            await engine.dispose()
            return
        user = AdminUser(
            email=email,
            name=name,
            role="super_admin" if super_admin else "admin",
            password_hash=hash_password(password),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin user: {email}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
