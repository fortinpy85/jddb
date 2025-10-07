"""
Service for extracting and managing skills from job descriptions using Lightcast API.
"""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from jd_ingestion.database.models import Skill, JobDescription, job_description_skills
from jd_ingestion.services.lightcast_client import get_lightcast_client, ExtractedSkill
from jd_ingestion.utils.logging import get_logger

logger = get_logger(__name__)


class SkillExtractionService:
    """Service for extracting skills from job descriptions and storing them."""

    async def extract_and_save_skills(
        self,
        job_id: int,
        job_text: str,
        db: AsyncSession,
        confidence_threshold: float = 0.5,
    ) -> List[Skill]:
        """
        Extract skills from job description text and save to database.

        Args:
            job_id: ID of the job description
            job_text: The job description text to extract skills from
            db: Database session
            confidence_threshold: Minimum confidence score for skills (0.0-1.0)

        Returns:
            List[Skill]: List of skills associated with the job

        Raises:
            Exception: If skill extraction or database operations fail
        """
        try:
            logger.info(
                f"Starting skill extraction for job {job_id}",
                job_id=job_id,
                text_length=len(job_text),
                confidence_threshold=confidence_threshold,
            )

            # Get Lightcast client
            client = await get_lightcast_client()

            # Extract skills from text
            extracted_skills = await client.extract_skills(
                text=job_text,
                confidence_threshold=confidence_threshold,
            )

            if not extracted_skills:
                logger.warning(f"No skills extracted for job {job_id}", job_id=job_id)
                return []

            logger.info(
                f"Extracted {len(extracted_skills)} skills for job {job_id}",
                job_id=job_id,
                skill_count=len(extracted_skills),
            )

            # Save skills and create associations
            saved_skills = []
            for extracted_skill in extracted_skills:
                try:
                    # Check if skill already exists in database
                    skill = await self._get_or_create_skill(
                        extracted_skill=extracted_skill,
                        db=db,
                    )
                    saved_skills.append(skill)

                    # Create job-skill association
                    await self._create_job_skill_association(
                        job_id=job_id,
                        skill_id=skill.id,
                        confidence=extracted_skill.confidence,
                        db=db,
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to save skill {extracted_skill.name}",
                        skill_name=extracted_skill.name,
                        error=str(e),
                    )
                    # Continue with other skills even if one fails

            # Commit all changes
            await db.commit()

            logger.info(
                f"Successfully saved {len(saved_skills)} skills for job {job_id}",
                job_id=job_id,
                saved_count=len(saved_skills),
            )

            return saved_skills

        except Exception as e:
            logger.error(
                f"Skill extraction failed for job {job_id}",
                job_id=job_id,
                error=str(e),
            )
            await db.rollback()
            raise

    async def _get_or_create_skill(
        self,
        extracted_skill: ExtractedSkill,
        db: AsyncSession,
    ) -> Skill:
        """
        Get existing skill or create new one if it doesn't exist.

        Args:
            extracted_skill: Extracted skill data from Lightcast
            db: Database session

        Returns:
            Skill: The skill object
        """
        # Check if skill exists
        result = await db.execute(
            select(Skill).where(Skill.lightcast_id == extracted_skill.id)
        )
        skill = result.scalars().first()

        if skill:
            logger.debug(
                f"Found existing skill: {skill.name}",
                lightcast_id=extracted_skill.id,
            )
            return skill

        # Create new skill
        skill = Skill(
            lightcast_id=extracted_skill.id,
            name=extracted_skill.name,
            skill_type=extracted_skill.type,
            # Additional metadata can be added here when available
        )

        db.add(skill)
        await db.flush()  # Flush to get the skill ID without committing

        logger.info(
            f"Created new skill: {skill.name}",
            skill_id=skill.id,
            lightcast_id=extracted_skill.id,
        )

        return skill

    async def _create_job_skill_association(
        self,
        job_id: int,
        skill_id: int,
        confidence: float,
        db: AsyncSession,
    ) -> None:
        """
        Create association between job and skill.

        Args:
            job_id: Job description ID
            skill_id: Skill ID
            confidence: Confidence score from Lightcast
            db: Database session
        """
        try:
            # Check if association already exists
            result = await db.execute(
                select(job_description_skills).where(
                    job_description_skills.c.job_id == job_id,
                    job_description_skills.c.skill_id == skill_id,
                )
            )
            existing = result.first()

            if existing:
                logger.debug(
                    "Job-skill association already exists",
                    job_id=job_id,
                    skill_id=skill_id,
                )
                return

            # Create new association
            await db.execute(
                job_description_skills.insert().values(
                    job_id=job_id,
                    skill_id=skill_id,
                    confidence=confidence,
                )
            )

            logger.debug(
                "Created job-skill association",
                job_id=job_id,
                skill_id=skill_id,
                confidence=confidence,
            )

        except IntegrityError:
            # Handle race condition where another process created the association
            logger.warning(
                "Job-skill association already exists (race condition)",
                job_id=job_id,
                skill_id=skill_id,
            )
            await db.rollback()

    async def get_job_skills(
        self,
        job_id: int,
        db: AsyncSession,
    ) -> List[Skill]:
        """
        Get all skills associated with a job description.

        Args:
            job_id: Job description ID
            db: Database session

        Returns:
            List[Skill]: List of skills associated with the job
        """
        try:
            # Get job with skills loaded
            result = await db.execute(
                select(JobDescription).where(JobDescription.id == job_id)
            )
            job = result.scalars().first()

            if not job:
                logger.warning(f"Job not found: {job_id}", job_id=job_id)
                return []

            # Skills are loaded via the relationship
            return job.skills if job.skills else []

        except Exception as e:
            logger.error(
                f"Failed to get skills for job {job_id}",
                job_id=job_id,
                error=str(e),
            )
            raise


# Singleton instance
skill_extraction_service = SkillExtractionService()
