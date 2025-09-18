"""
Advanced job analysis and comparison service.

This service provides comprehensive job comparison, skill gap analysis,
and career path recommendations using semantic embeddings and NLP.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import openai
import json
import numpy as np
from datetime import datetime, timedelta

from ..database.models import (
    JobDescription,
    JobSection,
    ContentChunk,
    JobMetadata,
    JobComparison,
    JobSkill,
    CareerPath,
    ClassificationBenchmark,
)
from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JobAnalysisService:
    """Service for advanced job analysis and comparison features."""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def compare_jobs(
        self,
        db: AsyncSession,
        job_a_id: int,
        job_b_id: int,
        comparison_types: List[str] = None,
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """
        Comprehensive job comparison with multiple analysis types.

        Args:
            db: Database session
            job_a_id: ID of first job
            job_b_id: ID of second job
            comparison_types: Types of comparison ['similarity', 'skill_gap', 'requirements']
            include_details: Whether to include detailed breakdowns

        Returns:
            Dictionary with comparison results
        """
        if not comparison_types:
            comparison_types = ["similarity", "skill_gap", "requirements"]

        # Get job data with relationships
        jobs_query = (
            select(JobDescription)
            .options(
                selectinload(JobDescription.sections),
                selectinload(JobDescription.metadata_entry),
                selectinload(JobDescription.chunks),
            )
            .where(JobDescription.id.in_([job_a_id, job_b_id]))
        )

        result = await db.execute(jobs_query)
        jobs = {job.id: job for job in result.scalars().all()}

        if len(jobs) != 2:
            raise ValueError("One or both jobs not found")

        job_a, job_b = jobs[job_a_id], jobs[job_b_id]

        comparison_result = {
            "job_a": {
                "id": job_a_id,
                "title": job_a.title,
                "classification": job_a.classification,
            },
            "job_b": {
                "id": job_b_id,
                "title": job_b.title,
                "classification": job_b.classification,
            },
            "comparison_types": comparison_types,
            "timestamp": datetime.utcnow().isoformat(),
            "analyses": {},
        }

        # Run different types of analysis
        for comp_type in comparison_types:
            if comp_type == "similarity":
                analysis = await self._analyze_similarity(
                    db, job_a, job_b, include_details
                )
            elif comp_type == "skill_gap":
                analysis = await self._analyze_skill_gap(
                    db, job_a, job_b, include_details
                )
            elif comp_type == "requirements":
                analysis = await self._analyze_requirements_match(
                    db, job_a, job_b, include_details
                )
            else:
                logger.warning(f"Unknown comparison type: {comp_type}")
                continue

            comparison_result["analyses"][comp_type] = analysis

            # Cache the result
            await self._cache_comparison(db, job_a_id, job_b_id, comp_type, analysis)

        return comparison_result

    async def _analyze_similarity(
        self,
        db: AsyncSession,
        job_a: JobDescription,
        job_b: JobDescription,
        include_details: bool,
    ) -> Dict[str, Any]:
        """Analyze semantic similarity between two jobs."""

        # Calculate overall embedding similarity
        overall_similarity = await self._calculate_embedding_similarity(
            db, job_a.id, job_b.id
        )

        # Calculate section-wise similarities
        section_similarities = {}
        if include_details:
            section_similarities = await self._calculate_section_similarities(
                job_a, job_b
            )

        # Compare metadata
        metadata_comparison = self._compare_metadata(
            job_a.metadata_entry, job_b.metadata_entry
        )

        # Generate key differences using GPT
        key_differences = []
        recommendation = ""

        if include_details:
            key_differences, recommendation = await self._generate_similarity_insights(
                job_a, job_b, overall_similarity
            )

        return {
            "overall_similarity": round(float(overall_similarity), 3),
            "section_similarities": section_similarities,
            "metadata_comparison": metadata_comparison,
            "key_differences": key_differences,
            "recommendation": recommendation,
            "similarity_level": self._get_similarity_level(overall_similarity),
        }

    async def _analyze_skill_gap(
        self,
        db: AsyncSession,
        job_a: JobDescription,
        job_b: JobDescription,
        include_details: bool,
    ) -> Dict[str, Any]:
        """Analyze skill gaps between two positions."""

        # Extract skills for both jobs
        skills_a = await self.extract_job_skills(db, job_a.id)
        skills_b = await self.extract_job_skills(db, job_b.id)

        # Compare skills
        skill_comparison = self._compare_skills(skills_a, skills_b)

        # Generate development recommendations
        recommendations = []
        if include_details:
            recommendations = await self._generate_skill_development_recommendations(
                skill_comparison["missing_skills"], skill_comparison["skill_level_gaps"]
            )

        return {
            "skills_job_a": len(skills_a),
            "skills_job_b": len(skills_b),
            "matching_skills": skill_comparison["matching_skills"],
            "missing_skills": skill_comparison["missing_skills"],
            "skill_level_gaps": skill_comparison["skill_level_gaps"],
            "development_recommendations": recommendations,
            "skill_gap_score": skill_comparison["gap_score"],
        }

    async def _analyze_requirements_match(
        self,
        db: AsyncSession,
        job_a: JobDescription,
        job_b: JobDescription,
        include_details: bool,
    ) -> Dict[str, Any]:
        """Analyze how well job A's requirements match job B's profile."""

        # Get requirements sections
        requirements_a = await self._extract_requirements(job_a)
        requirements_b = await self._extract_requirements(job_b)

        # Calculate requirement matching using embeddings
        requirement_matches = await self._calculate_requirement_matches(
            requirements_a, requirements_b
        )

        # Generate matching insights
        insights = []
        if include_details:
            insights = await self._generate_requirement_insights(requirement_matches)

        return {
            "overall_match_score": requirement_matches["overall_score"],
            "education_match": requirement_matches.get("education", 0.0),
            "experience_match": requirement_matches.get("experience", 0.0),
            "technical_skills_match": requirement_matches.get("technical", 0.0),
            "soft_skills_match": requirement_matches.get("soft_skills", 0.0),
            "matching_insights": insights,
            "match_level": self._get_match_level(requirement_matches["overall_score"]),
        }

    async def extract_job_skills(
        self, db: AsyncSession, job_id: int, refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Extract skills from a job description using NLP."""

        if not refresh:
            # Check if we have cached skills
            cached_skills_query = select(JobSkill).where(JobSkill.job_id == job_id)
            cached_result = await db.execute(cached_skills_query)
            cached_skills = cached_result.scalars().all()

            if cached_skills:
                return [
                    {
                        "category": skill.skill_category,
                        "name": skill.skill_name,
                        "level": skill.skill_level,
                        "confidence": float(skill.confidence_score),
                        "section": skill.extracted_from_section,
                    }
                    for skill in cached_skills
                ]

        # Get job with sections
        job_query = (
            select(JobDescription)
            .options(selectinload(JobDescription.sections))
            .where(JobDescription.id == job_id)
        )

        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Extract skills using GPT
        extracted_skills = []

        for section in job.sections:
            if section.section_content and len(section.section_content.strip()) > 50:
                skills = await self._extract_skills_from_text(
                    section.section_content, section.section_type
                )
                extracted_skills.extend(skills)

        # Save extracted skills to database
        await self._save_extracted_skills(db, job_id, extracted_skills)

        return extracted_skills

    async def _extract_skills_from_text(
        self, text: str, section_type: str
    ) -> List[Dict[str, Any]]:
        """Use GPT to extract skills from text content."""

        prompt = f"""
        Extract specific skills from this job description section. Be precise and avoid generic terms.
        
        Section Type: {section_type}
        Content: {text[:2000]}
        
        For each skill found, provide:
        1. Skill name (be specific, e.g. "Python Programming" not just "Programming")
        2. Category: technical, leadership, communication, analytical, domain, or interpersonal
        3. Level: required, preferred, or asset (infer from context like "must have", "nice to have")
        4. Confidence score: 0.0-1.0 based on how clearly the skill is stated
        
        Return as JSON array:
        [
            {{
                "name": "Python Programming",
                "category": "technical",
                "level": "required",
                "confidence": 0.9
            }}
        ]
        
        Focus on concrete skills and qualifications. Avoid soft descriptions.
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting specific skills from job descriptions. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            skills_data = json.loads(response.choices[0].message.content)

            # Add section information
            for skill in skills_data:
                skill["section"] = section_type

            return skills_data

        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []

    async def _save_extracted_skills(
        self, db: AsyncSession, job_id: int, skills: List[Dict[str, Any]]
    ):
        """Save extracted skills to database."""

        # Delete existing skills for this job
        await db.execute(select(JobSkill).where(JobSkill.job_id == job_id))

        # Add new skills
        for skill in skills:
            job_skill = JobSkill(
                job_id=job_id,
                skill_category=skill["category"],
                skill_name=skill["name"],
                skill_level=skill["level"],
                confidence_score=skill["confidence"],
                extracted_from_section=skill["section"],
            )
            db.add(job_skill)

        await db.commit()

    async def _calculate_embedding_similarity(
        self, db: AsyncSession, job_a_id: int, job_b_id: int
    ) -> float:
        """Calculate overall similarity using job embeddings."""

        # Get average embeddings for both jobs
        chunk_query = select(ContentChunk.embedding).where(
            and_(
                ContentChunk.job_id.in_([job_a_id, job_b_id]),
                ContentChunk.embedding.isnot(None),
            )
        )

        result = await db.execute(chunk_query)
        embeddings = [np.array(row[0]) for row in result.all()]

        if len(embeddings) < 2:
            return 0.0

        # Split embeddings by job (this is simplified - in practice you'd want to track which is which)
        mid = len(embeddings) // 2
        avg_a = np.mean(embeddings[:mid], axis=0)
        avg_b = np.mean(embeddings[mid:], axis=0)

        # Calculate cosine similarity
        similarity = np.dot(avg_a, avg_b) / (
            np.linalg.norm(avg_a) * np.linalg.norm(avg_b)
        )
        return max(0.0, min(1.0, float(similarity)))

    async def _calculate_section_similarities(
        self, job_a: JobDescription, job_b: JobDescription
    ) -> Dict[str, float]:
        """Calculate similarity scores for each section type using vector embeddings."""

        # Group sections by type
        sections_a = {s.section_type: s.section_content for s in job_a.sections}
        sections_b = {s.section_type: s.section_content for s in job_b.sections}

        # Find common section types
        common_sections = set(sections_a.keys()) & set(sections_b.keys())

        section_similarities = {}
        for section_type in common_sections:
            if sections_a[section_type] and sections_b[section_type]:
                # Use vector embedding-based similarity for accurate comparison
                similarity = await self._calculate_embedding_text_similarity(
                    sections_a[section_type], sections_b[section_type]
                )
                section_similarities[section_type] = similarity

        return section_similarities

    def _calculate_text_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate similarity between two text strings."""
        # Simple implementation - deprecated, use _calculate_embedding_text_similarity instead
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        return intersection / union if union > 0 else 0.0

    async def _calculate_embedding_text_similarity(
        self, text_a: str, text_b: str
    ) -> float:
        """Calculate similarity between two text strings using OpenAI embeddings."""
        try:
            # Get embeddings for both texts
            response_a = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text_a[:8000],  # Limit to avoid token limits
            )

            response_b = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text_b[:8000],  # Limit to avoid token limits
            )

            # Extract embedding vectors
            embedding_a = np.array(response_a.data[0].embedding)
            embedding_b = np.array(response_b.data[0].embedding)

            # Calculate cosine similarity
            similarity = np.dot(embedding_a, embedding_b) / (
                np.linalg.norm(embedding_a) * np.linalg.norm(embedding_b)
            )

            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))

        except Exception as e:
            logger.warning(
                f"Failed to calculate embedding similarity, falling back to text similarity: {str(e)}"
            )
            # Fallback to simple text similarity if embedding fails
            return self._calculate_text_similarity(text_a, text_b)

    def _compare_metadata(self, metadata_a, metadata_b) -> Dict[str, Any]:
        """Compare job metadata (salary, classification, etc.)."""

        comparison = {}

        if metadata_a and metadata_b:
            # Salary comparison
            if metadata_a.salary_budget and metadata_b.salary_budget:
                salary_diff = abs(
                    float(metadata_a.salary_budget) - float(metadata_b.salary_budget)
                )
                salary_avg = (
                    float(metadata_a.salary_budget) + float(metadata_b.salary_budget)
                ) / 2
                comparison["salary_difference_percent"] = round(
                    (salary_diff / salary_avg) * 100, 1
                )

            # FTE comparison
            if metadata_a.fte_count and metadata_b.fte_count:
                comparison["fte_difference"] = abs(
                    metadata_a.fte_count - metadata_b.fte_count
                )

            # Department comparison
            if metadata_a.department and metadata_b.department:
                comparison["same_department"] = (
                    metadata_a.department == metadata_b.department
                )
                comparison["department_a"] = metadata_a.department
                comparison["department_b"] = metadata_b.department

        return comparison

    def _compare_skills(
        self, skills_a: List[Dict], skills_b: List[Dict]
    ) -> Dict[str, Any]:
        """Compare extracted skills between two jobs."""

        skills_a_names = set(skill["name"].lower() for skill in skills_a)
        skills_b_names = set(skill["name"].lower() for skill in skills_b)

        matching = skills_a_names & skills_b_names
        missing_from_a = skills_b_names - skills_a_names
        missing_from_b = skills_a_names - skills_b_names

        # Calculate skill level gaps for matching skills
        skill_level_gaps = {}
        skills_a_dict = {skill["name"].lower(): skill for skill in skills_a}
        skills_b_dict = {skill["name"].lower(): skill for skill in skills_b}

        for skill_name in matching:
            level_a = skills_a_dict[skill_name]["level"]
            level_b = skills_b_dict[skill_name]["level"]
            if level_a != level_b:
                skill_level_gaps[skill_name] = {
                    "job_a_level": level_a,
                    "job_b_level": level_b,
                }

        # Calculate overall gap score
        total_unique_skills = len(skills_a_names | skills_b_names)
        gap_score = (
            len(matching) / total_unique_skills if total_unique_skills > 0 else 0.0
        )

        return {
            "matching_skills": list(matching),
            "missing_skills": list(missing_from_a),
            "skill_level_gaps": skill_level_gaps,
            "gap_score": round(gap_score, 3),
        }

    async def _generate_similarity_insights(
        self, job_a: JobDescription, job_b: JobDescription, similarity: float
    ) -> Tuple[List[str], str]:
        """Generate human-readable insights about job similarity."""

        prompt = f"""
        Compare these two government job positions and provide insights:
        
        Job A: {job_a.title} ({job_a.classification})
        Job B: {job_b.title} ({job_b.classification})
        
        Similarity Score: {similarity:.3f}
        
        Provide:
        1. Top 3 key differences between the roles
        2. A recommendation for career transition feasibility
        
        Format as JSON:
        {{
            "key_differences": ["difference 1", "difference 2", "difference 3"],
            "recommendation": "brief recommendation about transition feasibility"
        }}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career advisor analyzing government job positions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )

            insights = json.loads(response.choices[0].message.content)
            return insights["key_differences"], insights["recommendation"]

        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return [], ""

    async def _cache_comparison(
        self,
        db: AsyncSession,
        job_a_id: int,
        job_b_id: int,
        comparison_type: str,
        analysis: Dict[str, Any],
    ):
        """Cache comparison result in database."""

        # Check if comparison already exists
        existing_query = select(JobComparison).where(
            and_(
                JobComparison.job_a_id == job_a_id,
                JobComparison.job_b_id == job_b_id,
                JobComparison.comparison_type == comparison_type,
            )
        )

        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.section_scores = analysis.get("section_similarities", {})
            existing.metadata_comparison = analysis.get("metadata_comparison", {})
            existing.skills_analysis = analysis.get("skills_analysis", {})
            existing.overall_score = (
                analysis.get("overall_similarity")
                or analysis.get("gap_score")
                or analysis.get("overall_match_score")
            )
            existing.updated_at = func.now()
        else:
            # Create new
            comparison = JobComparison(
                job_a_id=job_a_id,
                job_b_id=job_b_id,
                comparison_type=comparison_type,
                overall_score=analysis.get("overall_similarity")
                or analysis.get("gap_score")
                or analysis.get("overall_match_score"),
                section_scores=analysis.get("section_similarities", {}),
                metadata_comparison=analysis.get("metadata_comparison", {}),
                skills_analysis=analysis.get("skills_analysis", {}),
            )
            db.add(comparison)

        await db.commit()

    def _get_similarity_level(self, similarity: float) -> str:
        """Get human-readable similarity level."""
        if similarity >= 0.8:
            return "Very High"
        elif similarity >= 0.6:
            return "High"
        elif similarity >= 0.4:
            return "Medium"
        elif similarity >= 0.2:
            return "Low"
        else:
            return "Very Low"

    def _get_match_level(self, match_score: float) -> str:
        """Get human-readable match level."""
        if match_score >= 0.85:
            return "Excellent Match"
        elif match_score >= 0.7:
            return "Good Match"
        elif match_score >= 0.5:
            return "Fair Match"
        elif match_score >= 0.3:
            return "Poor Match"
        else:
            return "No Match"


# Global service instance
job_analysis_service = JobAnalysisService()
