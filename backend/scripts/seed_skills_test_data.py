#!/usr/bin/env python3
"""
Seed script for Skills Intelligence E2E test data.

Creates sample jobs with skills matching the expectations in tests/skills.spec.ts:
- Job 1: "Senior Python Developer" (123456, IT-03) with Python and Project Management
- Job 2: "Data Analyst" (789012, EC-05) with Data Analysis and Python
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select, func, text
from sqlalchemy.exc import SQLAlchemyError
from jd_ingestion.database.connection import AsyncSessionLocal
from jd_ingestion.database.models import JobDescription, Skill
from jd_ingestion.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


# Skills data matching Lightcast format
SKILLS_DATA: List[Dict[str, Any]] = [
    {
        "lightcast_id": "KS123456",
        "name": "Python",
        "skill_type": "Hard Skill",
        "description": "Python programming language",
        "category": "IT and Programming",
        "subcategory": "Programming Languages",
    },
    {
        "lightcast_id": "KS789012",
        "name": "Project Management",
        "skill_type": "Soft Skill",
        "description": "Planning, organizing, and managing projects",
        "category": "Business and Management",
        "subcategory": "Management Skills",
    },
    {
        "lightcast_id": "KS345678",
        "name": "Data Analysis",
        "skill_type": "Hard Skill",
        "description": "Analyzing and interpreting data",
        "category": "Analytics and Data",
        "subcategory": "Data Science",
    },
]


# Jobs data matching test expectations
JOBS_DATA: List[Dict[str, Any]] = [
    {
        "job_number": "123456",
        "title": "Senior Python Developer",
        "classification": "IT-03",
        "language": "en",
        "file_path": "/test/data/IT-03_Senior_Python_Developer_123456.txt",
        "raw_content": """POSITION TITLE: Senior Python Developer
JOB NUMBER: 123456
CLASSIFICATION: IT-03
DEPARTMENT: Information Technology

GENERAL ACCOUNTABILITY:
The Senior Python Developer is responsible for designing, developing, and maintaining Python-based applications. This position requires strong analytical skills and project management capabilities.

SPECIFIC ACCOUNTABILITIES:
• Design and implement Python applications and services
• Lead development projects and coordinate with team members
• Apply data analysis techniques to improve application performance
• Ensure code quality through testing and code reviews
• Mentor junior developers in Python best practices

REQUIRED SKILLS:
• Expert knowledge of Python programming
• Strong project management experience
• Experience with data analysis and visualization
• Excellent problem-solving abilities""",
        "skills": [
            {"lightcast_id": "KS123456", "confidence": 0.95},  # Python
            {"lightcast_id": "KS789012", "confidence": 0.87},  # Project Management
        ],
    },
    {
        "job_number": "789012",
        "title": "Data Analyst",
        "classification": "EC-05",
        "language": "en",
        "file_path": "/test/data/EC-05_Data_Analyst_789012.txt",
        "raw_content": """POSITION TITLE: Data Analyst
JOB NUMBER: 789012
CLASSIFICATION: EC-05
DEPARTMENT: Economics and Statistics

GENERAL ACCOUNTABILITY:
The Data Analyst is responsible for collecting, processing, and analyzing data to support business decisions. This position requires strong analytical and programming skills.

SPECIFIC ACCOUNTABILITIES:
• Analyze large datasets to identify trends and patterns
• Create reports and visualizations using Python
• Develop data processing pipelines
• Collaborate with stakeholders to understand data needs
• Ensure data quality and accuracy

REQUIRED SKILLS:
• Strong data analysis capabilities
• Proficiency in Python programming
• Experience with statistical analysis
• Database query skills""",
        "skills": [
            {"lightcast_id": "KS345678", "confidence": 0.92},  # Data Analysis
            {"lightcast_id": "KS123456", "confidence": 0.88},  # Python
        ],
    },
]


async def get_or_create_skill(session, skill_data: Dict[str, Any]) -> Skill:
    """Get existing skill or create new one."""
    result = await session.execute(
        select(Skill).where(Skill.lightcast_id == skill_data["lightcast_id"])
    )
    skill = result.scalar_one_or_none()

    if skill:
        logger.info(f"Found existing skill: {skill.name} ({skill.lightcast_id})")
        return skill

    skill = Skill(**skill_data)
    session.add(skill)
    await session.flush()
    logger.info(f"Created skill: {skill.name} ({skill.lightcast_id})")
    return skill


async def create_skills_test_data() -> None:
    """
    Creates sample jobs with skills for E2E testing.
    """
    logger.info("Creating skills test data...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if test jobs already exist
            result = await session.execute(
                select(func.count(JobDescription.id)).where(
                    JobDescription.job_number.in_(["123456", "789012"])
                )
            )
            existing_count = result.scalar_one()

            if existing_count > 0:
                logger.info(f"Skills test data already exists ({existing_count} jobs found).")
                logger.info("To recreate, delete jobs 123456 and 789012 first.")
                return

            # Create skills first
            logger.info("\n[SKILLS] Creating skills...")
            skills_map = {}
            for skill_data in SKILLS_DATA:
                skill = await get_or_create_skill(session, skill_data)
                skills_map[skill.lightcast_id] = skill

            # Create jobs with skills
            logger.info("\n[JOBS] Creating jobs with skills...")
            for job_data in JOBS_DATA:
                # Extract skills associations before creating job
                skills_associations = job_data.pop("skills", [])

                # Create job
                job = JobDescription(
                    job_number=job_data["job_number"],
                    title=job_data["title"],
                    classification=job_data["classification"],
                    language=job_data["language"],
                    file_path=job_data["file_path"],
                    raw_content=job_data["raw_content"],
                    file_hash=f"test_{job_data['job_number']}",
                )
                session.add(job)
                await session.flush()

                # Link skills to job using raw SQL for association table with confidence
                for skill_assoc in skills_associations:
                    skill = skills_map[skill_assoc["lightcast_id"]]
                    await session.execute(
                        text(
                            """
                            INSERT INTO job_description_skills (job_id, skill_id, confidence, created_at)
                            VALUES (:job_id, :skill_id, :confidence, CURRENT_TIMESTAMP)
                            """
                        ),
                        {
                            "job_id": job.id,
                            "skill_id": skill.id,
                            "confidence": skill_assoc["confidence"],
                        },
                    )
                    logger.info(
                        f"  Linked skill: {skill.name} "
                        f"(confidence: {skill_assoc['confidence']:.2%})"
                    )

                logger.info(f"Created job: {job.job_number} - {job.title}")

            await session.commit()
            logger.info("\n" + "=" * 50)
            logger.info("SUCCESS: Skills test data creation completed!")
            logger.info(f"   Created {len(SKILLS_DATA)} skills")
            logger.info(f"   Created {len(JOBS_DATA)} jobs")
            logger.info("\nYour E2E tests are ready to run!")

        except SQLAlchemyError as e:
            logger.error(f"Failed to create skills test data: {e}")
            await session.rollback()
            raise


async def main() -> None:
    """
    Main function to create skills test data.
    """
    try:
        await create_skills_test_data()
        logger.info("Skills test data script completed successfully!")
    except Exception as e:
        logger.critical(f"Skills test data creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
