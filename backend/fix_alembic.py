#!/usr/bin/env python3
"""Fix alembic version in database to match current head."""
import sys
sys.path.append("src")

from sqlalchemy import create_engine, text
from jd_ingestion.config.settings import settings

def fix_alembic_version():
    """Update alembic version to current head."""
    engine = create_engine(str(settings.database_url).replace('postgresql+asyncpg', 'postgresql'))

    with engine.connect() as conn:
        # Check current version
        result = conn.execute(text('SELECT version_num FROM alembic_version'))
        current = result.scalar()
        print(f'Current alembic version: {current}')

        # Update to head
        head_version = '9063ab14ed70'
        conn.execute(text(f"UPDATE alembic_version SET version_num = '{head_version}'"))
        conn.commit()
        print(f'Updated alembic version to: {head_version} (head)')

if __name__ == "__main__":
    fix_alembic_version()