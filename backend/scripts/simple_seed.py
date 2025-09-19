#!/usr/bin/env python3
"""
Simple Phase 2 database seeding script.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from jd_ingestion.database.connection import get_async_session


async def main():
    """Simple seeding function."""
    print("Starting simple Phase 2 database seeding...")

    try:
        async for db in get_async_session():
            # Create a simple user
            result = await db.execute(text("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
                VALUES ('test_user', 'test@example.com', 'hash123', 'Test', 'User', 'editor', true)
                ON CONFLICT (username) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """))

            user_id = result.fetchone()[0]
            print(f"Created user with ID: {user_id}")

            await db.commit()
            print("SUCCESS: Basic seeding completed!")
            break

    except Exception as e:
        print(f"ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())