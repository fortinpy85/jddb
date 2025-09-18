"""
Job analysis and comparison API endpoints.

Provides advanced job comparison, skill gap analysis, and career path recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ...database.connection import get_async_session
from ...services.job_analysis_service import job_analysis_service
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["analysis"])


class JobComparisonRequest(BaseModel):
    job_a_id: int = Field(..., description="ID of the first job")
    job_b_id: int = Field(..., description="ID of the second job")
    comparison_types: List[str] = Field(
        default=["similarity", "skill_gap", "requirements"],
        description="Types of analysis to perform",
    )
    include_details: bool = Field(
        default=True, description="Whether to include detailed breakdowns"
    )


class BatchComparisonRequest(BaseModel):
    base_job_id: int = Field(..., description="Base job to compare against")
    comparison_job_ids: List[int] = Field(
        ..., description="List of job IDs to compare with"
    )
    comparison_type: str = Field(default="similarity", description="Type of comparison")
    limit: int = Field(default=20, le=50, description="Maximum number of comparisons")


class SkillGapRequest(BaseModel):
    job_a_id: int = Field(..., description="Current job ID")
    job_b_id: int = Field(..., description="Target job ID")
    include_suggestions: bool = Field(
        default=True, description="Include development suggestions"
    )


@router.post("/compare")
async def compare_jobs(
    request: JobComparisonRequest, db: AsyncSession = Depends(get_async_session)
):
    """
    Perform comprehensive comparison between two jobs.

    This endpoint provides multi-dimensional job analysis including:
    - Semantic similarity analysis
    - Skill gap identification
    - Requirements matching
    - Career transition feasibility
    """
    try:
        if request.job_a_id == request.job_b_id:
            raise HTTPException(
                status_code=400, detail="Cannot compare job with itself"
            )

        result = await job_analysis_service.compare_jobs(
            db=db,
            job_a_id=request.job_a_id,
            job_b_id=request.job_b_id,
            comparison_types=request.comparison_types,
            include_details=request.include_details,
        )

        logger.info(
            "Job comparison completed",
            job_a=request.job_a_id,
            job_b=request.job_b_id,
            types=request.comparison_types,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Job comparison failed", error=str(e))
        raise HTTPException(status_code=500, detail="Comparison analysis failed")


@router.post("/batch-compare")
async def batch_compare_jobs(
    request: BatchComparisonRequest, db: AsyncSession = Depends(get_async_session)
):
    """
    Compare one job against multiple other jobs.

    Useful for finding similar positions or identifying career path options
    from a single starting position.
    """
    try:
        if request.base_job_id in request.comparison_job_ids:
            raise HTTPException(
                status_code=400, detail="Base job cannot be in comparison list"
            )

        # Limit the number of comparisons
        comparison_ids = request.comparison_job_ids[: request.limit]

        results = []
        for job_id in comparison_ids:
            try:
                comparison = await job_analysis_service.compare_jobs(
                    db=db,
                    job_a_id=request.base_job_id,
                    job_b_id=job_id,
                    comparison_types=[request.comparison_type],
                    include_details=False,  # Keep batch results lightweight
                )

                # Extract the main score for sorting
                analysis = comparison["analyses"][request.comparison_type]
                score = (
                    analysis.get("overall_similarity")
                    or analysis.get("gap_score")
                    or analysis.get("overall_match_score")
                    or 0
                )

                results.append(
                    {
                        "job_id": job_id,
                        "job_title": comparison["job_b"]["title"],
                        "classification": comparison["job_b"]["classification"],
                        "score": score,
                        "analysis": analysis,
                    }
                )

            except Exception as e:
                logger.warning(f"Failed to compare with job {job_id}: {str(e)}")
                continue

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        logger.info(
            "Batch comparison completed",
            base_job=request.base_job_id,
            comparisons=len(results),
        )

        return {
            "base_job_id": request.base_job_id,
            "comparison_type": request.comparison_type,
            "total_comparisons": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error("Batch comparison failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch comparison failed")


@router.get("/career-paths/{job_id}")
async def get_career_paths(
    job_id: int,
    target_classifications: Optional[str] = Query(
        None, description="Comma-separated classifications"
    ),
    limit: int = Query(10, le=50, description="Maximum number of paths"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Find potential career progression paths from a given job.

    Analyzes possible next steps based on classification levels,
    skill requirements, and typical career progressions.
    """
    try:
        # Parse target classifications
        target_classes = None
        if target_classifications:
            target_classes = [cls.strip() for cls in target_classifications.split(",")]

        # For now, return a placeholder structure
        # This would be implemented with career path analysis logic

        return {
            "from_job_id": job_id,
            "target_classifications": target_classes,
            "career_paths": [
                {
                    "target_job": {
                        "id": 789,
                        "title": "Senior Director",
                        "classification": "EX-03",
                    },
                    "progression_type": "vertical",
                    "feasibility_score": 0.82,
                    "time_estimate": "18-24 months",
                    "skill_gaps": ["Advanced Finance", "Executive Leadership"],
                    "experience_required": "5+ years in current role",
                    "typical_salary_increase": "$25,000 - $35,000",
                }
            ],
        }

    except Exception as e:
        logger.error("Career path analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail="Career path analysis failed")


@router.post("/skill-gap")
async def analyze_skill_gap(
    request: SkillGapRequest, db: AsyncSession = Depends(get_async_session)
):
    """
    Detailed skill gap analysis between two positions.

    Identifies missing skills, skill level differences, and provides
    development recommendations for career transition.
    """
    try:
        comparison = await job_analysis_service.compare_jobs(
            db=db,
            job_a_id=request.job_a_id,
            job_b_id=request.job_b_id,
            comparison_types=["skill_gap"],
            include_details=request.include_suggestions,
        )

        return comparison["analyses"]["skill_gap"]

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Skill gap analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail="Skill gap analysis failed")


@router.get("/classification-benchmark/{classification}")
async def get_classification_benchmark(
    classification: str,
    department: Optional[str] = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get benchmark data for a specific job classification.

    Provides salary ranges, typical skills, and other metrics
    for positions within the classification level.
    """
    try:
        # For now, return placeholder data
        # This would query the classification_benchmarks table

        return {
            "classification": classification,
            "department": department,
            "statistics": {
                "job_count": 45,
                "avg_salary": 89500,
                "median_salary": 87000,
                "salary_range": {"min": 72000, "max": 108000},
                "avg_fte_supervised": 3.2,
                "common_skills": [
                    "Strategic Planning",
                    "Project Management",
                    "Team Leadership",
                    "Budget Management",
                ],
                "typical_reports_to": "Director General",
                "typical_departments": [
                    "Policy Development",
                    "Operations",
                    "Strategic Planning",
                ],
            },
        }

    except Exception as e:
        logger.error("Classification benchmark failed", error=str(e))
        raise HTTPException(status_code=500, detail="Benchmark analysis failed")


@router.post("/extract-skills/{job_id}")
async def extract_job_skills(
    job_id: int,
    refresh: bool = Query(False, description="Force re-extraction of skills"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Extract and return skills from a job description.

    Uses NLP to identify required skills, qualifications, and competencies
    from job description text. Results are cached for performance.
    """
    try:
        skills = await job_analysis_service.extract_job_skills(
            db=db, job_id=job_id, refresh=refresh
        )

        # Group skills by category
        skills_by_category = {}
        for skill in skills:
            category = skill["category"]
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)

        return {
            "job_id": job_id,
            "total_skills": len(skills),
            "skills_by_category": skills_by_category,
            "all_skills": skills,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Skill extraction failed", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Skill extraction failed")


@router.get("/similar-salary-range/{job_id}")
async def get_similar_salary_range(
    job_id: int,
    tolerance: float = Query(
        0.15, ge=0.05, le=0.5, description="Salary range tolerance"
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Find jobs with similar salary ranges.

    Identifies positions with comparable compensation to help with
    career planning and market analysis.
    """
    try:
        # For now, return placeholder data
        # This would query jobs with similar salary_budget values

        return {
            "job_id": job_id,
            "tolerance": tolerance,
            "similar_jobs": [
                {
                    "id": 123,
                    "title": "Senior Policy Advisor",
                    "classification": "EX-01",
                    "salary": 85000,
                    "department": "Treasury Board",
                    "similarity_score": 0.89,
                },
                {
                    "id": 456,
                    "title": "Program Manager",
                    "classification": "EX-01",
                    "salary": 87500,
                    "department": "Finance",
                    "similarity_score": 0.82,
                },
            ],
        }

    except Exception as e:
        logger.error("Salary range analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail="Salary analysis failed")


@router.get("/job-clusters")
async def get_job_clusters(
    classification: Optional[str] = Query(None, description="Filter by classification"),
    method: str = Query("similarity", description="Clustering method"),
    n_clusters: int = Query(5, ge=2, le=20, description="Number of clusters"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Discover job clusters based on similarity.

    Groups similar jobs together to identify career families,
    skill groups, and organizational patterns.
    """
    try:
        # For now, return placeholder data
        # This would implement clustering using job embeddings

        return {
            "method": method,
            "n_clusters": n_clusters,
            "classification_filter": classification,
            "clusters": [
                {
                    "cluster_id": 1,
                    "cluster_name": "Strategic Leadership",
                    "job_count": 12,
                    "avg_similarity": 0.78,
                    "common_skills": ["Strategic Planning", "Team Leadership"],
                    "sample_jobs": [
                        {
                            "id": 123,
                            "title": "Director, Policy",
                            "classification": "EX-02",
                        },
                        {
                            "id": 456,
                            "title": "Senior Manager",
                            "classification": "EX-01",
                        },
                    ],
                },
                {
                    "cluster_id": 2,
                    "cluster_name": "Technical Analysis",
                    "job_count": 8,
                    "avg_similarity": 0.82,
                    "common_skills": ["Data Analysis", "Research"],
                    "sample_jobs": [
                        {
                            "id": 789,
                            "title": "Senior Analyst",
                            "classification": "AS-05",
                        },
                        {
                            "id": 101,
                            "title": "Research Officer",
                            "classification": "AS-04",
                        },
                    ],
                },
            ],
        }

    except Exception as e:
        logger.error("Job clustering failed", error=str(e))
        raise HTTPException(status_code=500, detail="Clustering analysis failed")


@router.get("/compensation-analysis")
async def get_compensation_analysis(
    classification: Optional[str] = Query(None, description="Filter by classification"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Comprehensive compensation analysis across positions.

    Provides salary statistics, benefit comparisons, and compensation
    trends for similar positions.
    """
    try:
        # For now, return placeholder data
        # This would analyze salary_budget data from job_metadata

        return {
            "filters": {"classification": classification, "department": department},
            "statistics": {
                "total_positions": 156,
                "salary_statistics": {
                    "mean": 89750,
                    "median": 87500,
                    "std_dev": 12300,
                    "min": 65000,
                    "max": 125000,
                    "percentiles": {"25th": 78000, "75th": 98000, "90th": 110000},
                },
                "fte_statistics": {
                    "avg_supervised": 2.8,
                    "median_supervised": 2,
                    "max_supervised": 15,
                },
            },
            "trends": {
                "salary_growth": "3.2% annually",
                "market_position": "competitive",
                "comparison_to_private": "-8% to -12%",
            },
        }

    except Exception as e:
        logger.error("Compensation analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail="Compensation analysis failed")
