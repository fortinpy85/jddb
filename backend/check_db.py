#!/usr/bin/env python3

import sys

sys.path.append("src")

from sqlalchemy import text
from jd_ingestion.database.connection import get_sync_session
from jd_ingestion.database.models import JobDescription, JobSection


def check_database():
    with get_sync_session() as db:
        # Check recent jobs
        result = db.execute(
            text(
                "SELECT id, job_number, title, LENGTH(raw_content) as content_length "
                "FROM job_descriptions ORDER BY id DESC LIMIT 5"
            )
        )
        rows = result.fetchall()
        print("Recent jobs:")
        for row in rows:
            print(
                f"  ID: {row[0]}, Job#: {row[1]}, Title: {row[2]}, Content Length: {row[3]}"
            )

        # Check sections for recent jobs
        result = db.execute(
            text(
                "SELECT job_id, COUNT(*) as section_count "
                "FROM job_sections WHERE job_id IN (297, 298) GROUP BY job_id"
            )
        )
        rows = result.fetchall()
        print("\nSections count:")
        for row in rows:
            print(f"  Job ID {row[0]}: {row[1]} sections")


if __name__ == "__main__":
    check_database()
