#!/usr/bin/env python3
"""
This script creates sample job description data for testing and development.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from jd_ingestion.database.connection import AsyncSessionLocal
from jd_ingestion.database.models import JobDescription, JobSection, JobMetadata
from jd_ingestion.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

SAMPLE_JOBS: List[Dict[str, Any]] = [
    {
        "job_number": "JD12345",
        "title": "Director of Strategic Planning",
        "classification": "EX-02",
        "language": "en",
        "file_path": "/sample/data/JD_EX-02_12345_Director_Strategic_Planning.txt",
        "raw_content": """POSITION TITLE: Director of Strategic Planning
JOB NUMBER: JD12345
CLASSIFICATION: EX-02
DEPARTMENT: Treasury Board Secretariat

GENERAL ACCOUNTABILITY:
The Director of Strategic Planning is responsible for leading the development and implementation of strategic planning initiatives across the organization. This position provides executive leadership in strategic analysis, policy development, and long-term organizational planning.

ORGANIZATION STRUCTURE:
Reports to: Assistant Deputy Minister, Corporate Services
Direct Reports: 3 Senior Analysts, 2 Policy Advisors
Budget Authority: $2.5M annually

NATURE AND SCOPE:
This position operates at the executive level, providing strategic direction and oversight for complex planning initiatives. The role involves collaboration with senior officials across government departments and external stakeholders.

SPECIFIC ACCOUNTABILITIES:
• Lead the development of comprehensive strategic plans and frameworks
• Oversee policy analysis and recommendations for senior management
• Manage strategic planning processes and methodologies
• Coordinate with other departments on cross-government initiatives
• Provide expert advice on strategic matters to executive leadership

DIMENSIONS:
• Annual budget responsibility: $2.5 million
• Staff supervised: 5 direct reports
• Geographic scope: National
• Stakeholder reach: 15+ government departments""",
        "sections": [
            {
                "section_type": "general_accountability",
                "section_content": "The Director of Strategic Planning is responsible for leading the development and implementation of strategic planning initiatives across the organization. This position provides executive leadership in strategic analysis, policy development, and long-term organizational planning.",
                "section_order": 1,
            },
            {
                "section_type": "organization_structure",
                "section_content": "Reports to: Assistant Deputy Minister, Corporate Services\nDirect Reports: 3 Senior Analysts, 2 Policy Advisors\nBudget Authority: $2.5M annually",
                "section_order": 2,
            },
            {
                "section_type": "specific_accountabilities",
                "section_content": "• Lead the development of comprehensive strategic plans and frameworks\n• Oversee policy analysis and recommendations for senior management\n• Manage strategic planning processes and methodologies\n• Coordinate with other departments on cross-government initiatives\n• Provide expert advice on strategic matters to executive leadership",
                "section_order": 3,
            },
        ],
        "metadata": {
            "reports_to": "Assistant Deputy Minister, Corporate Services",
            "department": "Treasury Board Secretariat",
            "location": "Ottawa, ON",
            "fte_count": 5,
            "salary_budget": 450000.00,
        },
    },
    # ... (rest of the sample data)
]


async def create_sample_data() -> None:
    """
    Creates sample job description data in the database.
    """
    logger.info("Creating sample job description data...")
    async with AsyncSessionLocal() as session:
        try:
            if (
                await session.execute(select(func.count(JobDescription.id)))
            ).scalar_one() > 0:
                logger.info("Sample data already exists.")
                return

            for job_data in SAMPLE_JOBS:
                job = JobDescription(
                    job_number=job_data["job_number"],
                    title=job_data["title"],
                    classification=job_data["classification"],
                    language=job_data["language"],
                    file_path=job_data["file_path"],
                    raw_content=job_data["raw_content"],
                    file_hash=f"sample_{job_data['job_number']}",
                )
                session.add(job)
                await session.flush()

                for section_data in job_data["sections"]:
                    session.add(JobSection(job_id=job.id, **section_data))

                if "metadata" in job_data:
                    session.add(JobMetadata(job_id=job.id, **job_data["metadata"]))

                logger.info(f"Created sample job: {job.job_number} - {job.title}")

            await session.commit()
            logger.info(
                f"Sample data creation completed. Total jobs: {len(SAMPLE_JOBS)}"
            )

        except SQLAlchemyError as e:
            logger.error(f"Failed to create sample data: {e}")
            await session.rollback()
            raise


async def main() -> None:
    """
    Main function to create sample data.
    """
    try:
        await create_sample_data()
        logger.info("Sample data script completed successfully!")
    except Exception as e:
        logger.critical(f"Sample data creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
