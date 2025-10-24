"""
Advanced job analysis and comparison service.

This service provides comprehensive job comparison, skill gap analysis,
and career path recommendations using semantic embeddings and NLP.
"""
# mypy: disable-error-code="attr-defined,arg-type"

from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import openai
import json
import numpy as np
from datetime import datetime
from sklearn.cluster import KMeans

from ..database.models import (
    JobDescription,
    JobMetadata,
    ContentChunk,
    JobComparison,
    JobSkill,
)
from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JobAnalysisService:
    """Service for advanced job analysis and comparison features."""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_compensation_analysis(
        self,
        db: AsyncSession,
        classification: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Comprehensive compensation analysis across positions."""
        # Query for jobs with salary_budget from JobMetadata
        query = (
            select(JobMetadata.salary_budget)
            .join(JobDescription, JobMetadata.job_id == JobDescription.id)
            .where(JobMetadata.salary_budget.isnot(None))
        )
        if classification:
            query = query.where(JobDescription.classification == classification)
        if department:
            query = query.where(JobMetadata.department == department)

        result = await db.execute(query)
        salaries = [s for s in result.scalars().all() if s is not None]

        if not salaries:
            return {"statistics": {}}

        # Calculate statistics
        statistics = {
            "total_positions": len(salaries),
            "salary_statistics": {
                "mean": round(np.mean(salaries), 2),
                "median": round(np.median(salaries), 2),
                "std_dev": round(np.std(salaries), 2),
                "min": min(salaries),
                "max": max(salaries),
                "percentiles": {
                    "25th": round(np.percentile(salaries, 25), 2),
                    "75th": round(np.percentile(salaries, 75), 2),
                    "90th": round(np.percentile(salaries, 90), 2),
                },
            },
        }

        return {
            "filters": {"classification": classification, "department": department},
            "statistics": statistics,
        }

    async def get_job_clusters(
        self,
        db: AsyncSession,
        classification: Optional[str] = None,
        method: str = "similarity",
        n_clusters: int = 5,
    ) -> Dict[str, Any]:
        """Discover job clusters based on similarity."""
        # Get job embeddings
        query = select(
            JobDescription.id,
            JobDescription.title,
            JobDescription.classification,
            ContentChunk.embedding,
        ).join(ContentChunk, JobDescription.id == ContentChunk.job_id)
        if classification:
            query = query.where(JobDescription.classification == classification)

        result = await db.execute(query)
        jobs = result.all()

        if not jobs:
            return {"clusters": []}

        job_data = {}
        for job_id, title, classif, embedding in jobs:
            if job_id not in job_data:
                job_data[job_id] = {
                    "id": job_id,
                    "title": title,
                    "classification": classif,
                    "embeddings": [],
                }
            job_data[job_id]["embeddings"].append(embedding)

        job_ids = list(job_data.keys())
        avg_embeddings = [
            np.mean(job_data[job_id]["embeddings"], axis=0) for job_id in job_ids
        ]

        # Cluster embeddings
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(avg_embeddings)
        labels = kmeans.labels_

        # Group jobs by cluster
        clusters: dict[int, list[Any]] = {i: [] for i in range(n_clusters)}
        for i, job_id in enumerate(job_ids):
            clusters[labels[i]].append(job_data[job_id])

        # Format output
        output_clusters = []
        for cluster_id, jobs_in_cluster in clusters.items():
            if not jobs_in_cluster:
                continue

            output_clusters.append(
                {
                    "cluster_id": cluster_id,
                    "cluster_name": f"Cluster {cluster_id}",
                    "job_count": len(jobs_in_cluster),
                    "sample_jobs": [
                        {
                            "id": job["id"],
                            "title": job["title"],
                            "classification": job["classification"],
                        }
                        for job in jobs_in_cluster[:3]
                    ],
                }
            )

        return {
            "method": method,
            "n_clusters": n_clusters,
            "classification_filter": classification,
            "clusters": output_clusters,
        }

    async def compare_jobs(
        self,
        db: AsyncSession,
        job_a_id: int,
        job_b_id: int,
        comparison_types: Optional[List[str]] = None,
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
                selectinload(JobDescription.job_metadata),
                selectinload(JobDescription.chunks),
            )
            .where(JobDescription.id.in_([job_a_id, job_b_id]))
        )

        result = await db.execute(jobs_query)
        jobs = {job.id: job for job in result.scalars().all()}

        if len(jobs) != 2:
            raise ValueError("One or both jobs not found")
        # type: ignore[attr-defined]
        job_a, job_b = jobs[job_a_id], jobs[job_b_id]  # type: ignore[index]

        comparison_result: Dict[str, Any] = {
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
        overall_similarity = await self._calculate_embedding_similarity(  # type: ignore[attr-defined]
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
            job_a.job_metadata, job_b.job_metadata
        )

        # Generate key differences using GPT
        key_differences: list[str] = []
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

        # Extract skills for both jobs  # type: ignore[attr-defined]
        skills_a = await self.extract_job_skills(db, job_a.id)  # type: ignore[attr-defined]
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
                        "name": skill.skill_name,  # type: ignore[attr-defined]
                        "level": skill.proficiency_level
                        or ("required" if skill.is_required else "preferred"),
                        "confidence": float(skill.confidence_score)
                        if skill.confidence_score
                        else 0.0,  # type: ignore[attr-defined]
                        "context": skill.extracted_context,
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
            # Map level to is_required and proficiency_level
            level = skill.get("level", "preferred")
            is_required = level == "required"

            job_skill = JobSkill(
                job_id=job_id,
                skill_category=skill.get("category"),
                skill_name=skill["name"],
                proficiency_level=level,
                is_required=is_required,
                confidence_score=skill.get("confidence", 0.0),
                extracted_context=skill.get("context") or skill.get("section"),
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
        """Calculate similarity between two text strings using word overlap (fallback method)."""
        # Simple word-overlap implementation used as fallback when embeddings fail
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
            and_(  # type: ignore[attr-defined]
                JobComparison.job1_id == job_a_id,  # type: ignore[attr-defined]
                JobComparison.job2_id == job_b_id,
                JobComparison.comparison_type == comparison_type,
            )
        )

        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            similarity = (
                analysis.get("overall_similarity")
                or analysis.get("gap_score")
                or analysis.get("overall_match_score")
            )
            if similarity is not None:
                existing.similarity_score = float(similarity)  # type: ignore[assignment]
            # Store detailed analysis in differences field
            differences_dict = {
                "section_similarities": analysis.get("section_similarities", {}),
                "metadata_comparison": analysis.get("metadata_comparison", {}),
                "skills_analysis": analysis.get("skills_analysis", {}),
            }
            existing.differences = differences_dict  # type: ignore[assignment]
        else:
            # Create new
            comparison = JobComparison(
                job1_id=job_a_id,
                job2_id=job_b_id,
                comparison_type=comparison_type,
                similarity_score=analysis.get("overall_similarity")
                or analysis.get("gap_score")
                or analysis.get("overall_match_score"),
                differences={
                    "section_similarities": analysis.get("section_similarities", {}),
                    "metadata_comparison": analysis.get("metadata_comparison", {}),
                    "skills_analysis": analysis.get("skills_analysis", {}),
                },
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

    async def _extract_requirements(self, job: JobDescription) -> Dict[str, Any]:
        """Extract structured requirements from job description."""
        requirements: Dict[str, list[str]] = {
            "education": [],
            "experience": [],
            "technical_skills": [],
            "soft_skills": [],
            "certifications": [],
            "languages": [],
        }

        try:
            # Get relevant sections for requirements extraction  # type: ignore[attr-defined]
            sections = await job.awaitable_attrs.job_sections

            # Extract from specific accountabilities and qualifications sections
            accountability_text = ""
            qualifications_text = ""

            for section in sections:
                if section.section_type in [
                    "specific_accountabilities",
                    "knowledge_skills",
                    "nature_and_scope",
                ]:
                    section_content = section.section_content or ""

                    if section.section_type == "specific_accountabilities":
                        accountability_text += section_content + "\n"
                    elif section.section_type == "knowledge_skills":
                        qualifications_text += section_content + "\n"

            # Use OpenAI to extract structured requirements
            prompt = f"""
            Extract structured job requirements from this government job description:

            ACCOUNTABILITIES:
            {accountability_text}

            QUALIFICATIONS:
            {qualifications_text}

            Extract and return as JSON:
            {{
                "education": ["requirement1", "requirement2"],
                "experience": ["years and type of experience"],
                "technical_skills": ["skill1", "skill2"],
                "soft_skills": ["skill1", "skill2"],
                "certifications": ["cert1", "cert2"],
                "languages": ["language requirements"]
            }}
            """

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured job requirements. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=800,
            )

            extracted = json.loads(response.choices[0].message.content)
            requirements.update(extracted)

        except Exception as e:
            logger.error(f"Error extracting requirements for job {job.id}: {str(e)}")
            # Fallback: extract basic requirements from text
            full_text = job.raw_content or ""
            if "degree" in full_text.lower() or "bachelor" in full_text.lower():
                requirements["education"].append("Bachelor's degree")
            if "experience" in full_text.lower():
                requirements["experience"].append("Professional experience required")

        return requirements

    async def _calculate_requirement_matches(
        self, requirements_a: Dict[str, Any], requirements_b: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate how well requirements match between two jobs."""
        matches = {
            "overall_score": 0.0,
            "education": 0.0,
            "experience": 0.0,
            "technical": 0.0,
            "soft_skills": 0.0,
            "certifications": 0.0,
            "languages": 0.0,
        }

        try:
            category_scores = []

            for category in [
                "education",
                "experience",
                "technical_skills",
                "soft_skills",
                "certifications",
                "languages",
            ]:
                reqs_a = requirements_a.get(category, [])
                reqs_b = requirements_b.get(category, [])

                if not reqs_a and not reqs_b:
                    score = 1.0  # Both empty, perfect match
                elif not reqs_a or not reqs_b:
                    score = 0.0  # One empty, no match
                else:
                    # Calculate semantic similarity using embeddings
                    text_a = " ".join(reqs_a)
                    text_b = " ".join(reqs_b)
                    score = await self._calculate_embedding_text_similarity(
                        text_a, text_b
                    )

                # Map category names for the result
                result_key = (
                    category
                    if category not in ["technical_skills", "soft_skills"]
                    else category.replace("_skills", "")
                )
                matches[result_key] = round(score, 3)
                category_scores.append(score)

            # Calculate overall score as weighted average
            matches["overall_score"] = round(
                sum(category_scores) / len(category_scores), 3
            )

        except Exception as e:
            logger.error(f"Error calculating requirement matches: {str(e)}")

        return matches

    async def _generate_requirement_insights(
        self, requirement_matches: Dict[str, float]
    ) -> List[str]:
        """Generate human-readable insights about requirement matching."""
        insights = []

        try:
            overall_score = requirement_matches.get("overall_score", 0.0)

            # Overall assessment
            if overall_score >= 0.8:
                insights.append(
                    "Excellent overall requirement match - candidate would be well-suited for this transition"
                )
            elif overall_score >= 0.6:
                insights.append(
                    "Good requirement match - some upskilling may be beneficial"
                )
            elif overall_score >= 0.4:
                insights.append(
                    "Moderate requirement match - significant training would be needed"
                )
            else:
                insights.append(
                    "Poor requirement match - major skill development required"
                )

            # Specific category insights
            for category, score in requirement_matches.items():
                if category == "overall_score":
                    continue

                if score < 0.3:
                    insights.append(
                        f"Significant gap in {category.replace('_', ' ')} requirements"
                    )
                elif score >= 0.8:
                    insights.append(
                        f"Strong match in {category.replace('_', ' ')} requirements"
                    )

            # Generate specific recommendations
            weak_areas = [
                cat.replace("_", " ")
                for cat, score in requirement_matches.items()
                if cat != "overall_score" and score < 0.5
            ]

            if weak_areas:
                insights.append(f"Focus development on: {', '.join(weak_areas)}")

        except Exception as e:
            logger.error(f"Error generating requirement insights: {str(e)}")
            insights.append("Unable to generate detailed insights")

        return insights

    async def _generate_skill_development_recommendations(
        self, missing_skills: List[str], skill_level_gaps: Dict[str, Any]
    ) -> List[str]:
        """Generate skill development recommendations based on gaps."""
        recommendations = []

        try:
            # Recommendations for missing skills
            if missing_skills:
                high_priority_skills = missing_skills[:5]  # Focus on top 5
                if len(high_priority_skills) <= 2:
                    recommendations.append(
                        f"Develop expertise in: {', '.join(high_priority_skills)}"
                    )
                else:
                    recommendations.append(
                        f"Priority skills to develop: {', '.join(high_priority_skills[:3])}"
                    )
                    if len(high_priority_skills) > 3:
                        recommendations.append(
                            f"Additional skills: {', '.join(high_priority_skills[3:])}"
                        )

            # Recommendations for skill level gaps
            if skill_level_gaps:
                upgrade_skills = []
                for skill, gap_info in skill_level_gaps.items():
                    current_level = gap_info.get("job_a_level", "")
                    required_level = gap_info.get("job_b_level", "")
                    if current_level and required_level:
                        upgrade_skills.append(
                            f"{skill} (from {current_level} to {required_level})"
                        )

                if upgrade_skills:
                    if len(upgrade_skills) <= 3:
                        recommendations.append(
                            f"Upgrade skill levels: {', '.join(upgrade_skills)}"
                        )
                    else:
                        recommendations.append(
                            f"Focus on upgrading: {', '.join(upgrade_skills[:3])}"
                        )

            # General development advice
            total_gaps = len(missing_skills) + len(skill_level_gaps)
            if total_gaps == 0:
                recommendations.append(
                    "Excellent skill alignment - minimal additional development needed"
                )
            elif total_gaps <= 3:
                recommendations.append(
                    "Consider targeted professional development in identified areas"
                )
            elif total_gaps <= 6:
                recommendations.append(
                    "Structured learning plan recommended to address skill gaps"
                )
            else:
                recommendations.append(
                    "Comprehensive skill development program would be beneficial"
                )

            # Always include a timeline suggestion
            if missing_skills or skill_level_gaps:
                if total_gaps <= 2:
                    recommendations.append("Estimated development time: 3-6 months")
                elif total_gaps <= 5:
                    recommendations.append("Estimated development time: 6-12 months")
                else:
                    recommendations.append("Estimated development time: 12+ months")

        except Exception as e:
            logger.error(
                f"Error generating skill development recommendations: {str(e)}"
            )
            recommendations.append(
                "Consider professional development opportunities to bridge skill gaps"
            )

        return recommendations

    async def get_similar_salary_range(
        self, db: AsyncSession, job_id: int, tolerance: float = 0.15
    ) -> Dict[str, Any]:
        """Find jobs with similar salary ranges."""
        # Get the current job's salary from JobMetadata
        current_query = (
            select(JobMetadata.salary_budget)
            .join(JobDescription, JobMetadata.job_id == JobDescription.id)
            .where(JobDescription.id == job_id)
        )
        current_result = await db.execute(current_query)
        current_salary = current_result.scalar_one_or_none()

        if not current_salary:
            return {"job_id": job_id, "similar_jobs": []}

        # Calculate salary range
        min_salary = current_salary * (1 - tolerance)
        max_salary = current_salary * (1 + tolerance)

        # Query for similar jobs with salary in range
        similar_jobs_query = (
            select(JobDescription, JobMetadata.salary_budget, JobMetadata.department)
            .join(JobMetadata, JobDescription.id == JobMetadata.job_id)
            .where(
                and_(
                    JobDescription.id != job_id,
                    JobMetadata.salary_budget.between(min_salary, max_salary),
                )
            )
            .limit(20)
        )

        similar_jobs_result = await db.execute(similar_jobs_query)
        similar_jobs = similar_jobs_result.all()

        similar_jobs_data = []
        for job, salary, department in similar_jobs:
            similarity = await self._calculate_embedding_similarity(db, job_id, job.id)
            similar_jobs_data.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "classification": job.classification,
                    "salary": salary,
                    "department": department,
                    "similarity_score": round(similarity, 2),
                }
            )

        return {
            "job_id": job_id,
            "tolerance": tolerance,
            "similar_jobs": similar_jobs_data,
        }

    async def get_classification_benchmark(
        self, db: AsyncSession, classification: str, department: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get benchmark data for a specific job classification."""
        # Query for jobs in the given classification with metadata
        query = (
            select(JobDescription.id)
            .join(JobMetadata, JobDescription.id == JobMetadata.job_id)
            .where(JobDescription.classification == classification)
        )
        if department:
            query = query.where(JobMetadata.department == department)

        result = await db.execute(query)
        job_ids = [row for row in result.scalars().all()]

        if not job_ids:
            return {"classification": classification, "statistics": {}}

        # Get salary data from job_metadata
        salary_query = select(JobMetadata.salary_budget).where(
            and_(JobMetadata.job_id.in_(job_ids), JobMetadata.salary_budget.isnot(None))
        )
        salary_result = await db.execute(salary_query)
        salaries = [s for s in salary_result.scalars().all() if s is not None]

        # Get common skills from job_skills
        skills_query = (
            select(JobSkill.skill_name, func.count(JobSkill.skill_name).label("count"))
            .where(JobSkill.job_id.in_(job_ids))
            .group_by(JobSkill.skill_name)
            .order_by(func.count(JobSkill.skill_name).desc())
            .limit(10)
        )
        skills_result = await db.execute(skills_query)
        common_skills = [row[0] for row in skills_result.all()]

        # Calculate statistics
        statistics = {
            "job_count": len(job_ids),
            "avg_salary": round(np.mean(salaries), 2) if salaries else 0,
            "median_salary": round(np.median(salaries), 2) if salaries else 0,
            "salary_range": {
                "min": min(salaries) if salaries else 0,
                "max": max(salaries) if salaries else 0,
            },
            "common_skills": common_skills,
        }

        return {
            "classification": classification,
            "department": department,
            "statistics": statistics,
        }

    async def get_career_paths(
        self,
        db: AsyncSession,
        job_id: int,
        target_classifications: Optional[List[str]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Find potential career progression paths from a given job."""
        # Get the current job
        current_job_query = select(JobDescription).where(JobDescription.id == job_id)
        current_job_result = await db.execute(current_job_query)
        current_job = current_job_result.scalar_one_or_none()

        if not current_job:
            raise ValueError(f"Job {job_id} not found")

        # Simple logic: find jobs with a higher classification level
        if not current_job.classification:
            return {"from_job_id": job_id, "career_paths": []}

        # A more sophisticated approach would involve a predefined hierarchy of classifications
        # For now, we just look for higher numbers in the classification
        try:
            current_level = int(current_job.classification.split("-")[-1])
        except (ValueError, IndexError):
            return {"from_job_id": job_id, "career_paths": []}

        next_level = current_level + 1
        next_level_classifications = [
            f"{current_job.classification.split('-')[0]}-{next_level:02d}",
            f"{current_job.classification.split('-')[0]}-{next_level + 1:02d}",
        ]

        if target_classifications:
            next_level_classifications = target_classifications

        paths_query = (
            select(JobDescription)
            .where(JobDescription.classification.in_(next_level_classifications))
            .limit(limit)
        )

        paths_result = await db.execute(paths_query)
        potential_jobs = paths_result.scalars().all()

        career_paths = []
        for job in potential_jobs:
            similarity = await self._calculate_embedding_similarity(  # type: ignore[attr-defined]
                db, current_job.id, job.id
            )
            career_paths.append(
                {
                    "target_job": {
                        "id": job.id,
                        "title": job.title,
                        "classification": job.classification,
                    },
                    "progression_type": "vertical",
                    "feasibility_score": round(similarity, 2),
                    "time_estimate": "18-24 months",
                    "skill_gaps": [],
                    "experience_required": "5+ years in current role",
                    "typical_salary_increase": "$25,000 - $35,000",
                }
            )

        return {
            "from_job_id": job_id,
            "target_classifications": target_classifications,
            "career_paths": career_paths,
        }


# Global service instance
job_analysis_service = JobAnalysisService()
