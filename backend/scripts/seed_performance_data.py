#!/usr/bin/env python3
"""
Performance Test Data Seeding Script

Seeds the database with a large dataset to test performance under load.
Creates realistic job descriptions, search analytics, and translation memory data.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from jd_ingestion.config.settings import settings
from jd_ingestion.database.models import (
    JobDescription,
    JobMetadata,
    ContentChunk,
    SearchAnalytics,
    TranslationProject,
    TranslationMemory,
    AIUsageTracking,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data for generating realistic content
JOB_TITLES = [
    "Senior Software Engineer",
    "Product Manager",
    "Data Scientist",
    "DevOps Engineer",
    "UX Designer",
    "Business Analyst",
    "Technical Writer",
    "Project Manager",
    "Database Administrator",
    "Security Analyst",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Solutions Architect",
    "System Administrator",
    "Quality Assurance Engineer",
    "Marketing Manager",
    "Sales Representative",
    "HR Specialist",
    "Financial Analyst",
    "Operations Manager",
    "Customer Success Manager",
    "Content Manager",
    "Social Media Specialist",
]

DEPARTMENTS = [
    "Information Technology",
    "Engineering",
    "Product Development",
    "Marketing",
    "Sales",
    "Human Resources",
    "Finance",
    "Operations",
    "Customer Support",
    "Legal",
    "Research and Development",
    "Quality Assurance",
    "Security",
]

CLASSIFICATIONS = [
    "AS-01",
    "AS-02",
    "AS-03",
    "AS-04",
    "AS-05",
    "AS-06",
    "AS-07",
    "EX-01",
    "EX-02",
    "PM-01",
    "PM-02",
    "PM-03",
    "PM-04",
    "PM-05",
    "CS-01",
    "CS-02",
    "CS-03",
    "CS-04",
    "CS-05",
]

SAMPLE_CONTENT_TEMPLATES = [
    """The {title} position is responsible for {primary_responsibility}.
This role requires strong {skill_1} and {skill_2} skills, with experience in {technology}.
The successful candidate will work closely with {team} team to deliver high-quality solutions.

Key Responsibilities:
- {responsibility_1}
- {responsibility_2}
- {responsibility_3}
- {responsibility_4}

Qualifications:
- Bachelor's degree in {field} or related field
- {years} years of experience in {area}
- Experience with {tool_1}, {tool_2}, and {tool_3}
- Strong communication and problem-solving skills""",
    """We are seeking a {title} to join our dynamic {department} department.
This position offers an exciting opportunity to {opportunity} and contribute to {contribution}.

The ideal candidate will have:
- Proven experience in {experience_area}
- Strong technical skills in {tech_skills}
- Ability to {ability_1} and {ability_2}
- Experience working in {environment} environments

Responsibilities include:
- {duty_1}
- {duty_2}
- {duty_3}
- {duty_4}

This role reports to the {reports_to} and requires {requirement}.""",
]


def generate_realistic_content(title: str, department: str, classification: str) -> str:
    """Generate realistic job description content."""
    template = random.choice(SAMPLE_CONTENT_TEMPLATES)

    # Technology and skills pools
    technologies = [
        "Python",
        "JavaScript",
        "Java",
        "C++",
        "React",
        "Node.js",
        "PostgreSQL",
        "MongoDB",
        "AWS",
        "Docker",
        "Kubernetes",
    ]
    skills = [
        "communication",
        "leadership",
        "analytical",
        "project management",
        "teamwork",
        "problem-solving",
    ]
    tools = [
        "Git",
        "Jira",
        "Confluence",
        "Slack",
        "Microsoft Office",
        "Tableau",
        "Power BI",
        "Jenkins",
        "Terraform",
    ]

    content = template.format(
        title=title,
        department=department,
        classification=classification,
        primary_responsibility=f"leading {department.lower()} initiatives",
        skill_1=random.choice(skills),
        skill_2=random.choice(skills),
        technology=random.choice(technologies),
        team=department.lower(),
        responsibility_1=f"Develop and implement {department.lower()} strategies",
        responsibility_2="Collaborate with cross-functional teams",
        responsibility_3=f"Monitor and improve {department.lower()} processes",
        responsibility_4="Provide technical guidance and mentorship",
        field=department.replace(" ", " "),
        years=random.randint(3, 8),
        area=department.lower(),
        tool_1=random.choice(tools),
        tool_2=random.choice(tools),
        tool_3=random.choice(tools),
        opportunity=f"work on cutting-edge {department.lower()} projects",
        contribution=f"our organization's {department.lower()} excellence",
        experience_area=f"{department.lower()} and related fields",
        tech_skills=", ".join(random.sample(technologies, 3)),
        ability_1="work independently",
        ability_2="manage multiple priorities",
        environment="agile",
        duty_1=f"Design and implement {department.lower()} solutions",
        duty_2=f"Participate in {department.lower()} planning sessions",
        duty_3=f"Ensure compliance with {department.lower()} standards",
        duty_4=f"Document {department.lower()} processes and procedures",
        reports_to=f"Director of {department}",
        requirement="strong attention to detail",
    )

    return content


def create_sample_job_descriptions(session, count: int = 1000) -> List[JobDescription]:
    """Create sample job descriptions for performance testing."""
    logger.info(f"Creating {count} job descriptions...")

    jobs = []
    for i in range(count):
        title = random.choice(JOB_TITLES)
        department = random.choice(DEPARTMENTS)
        classification = random.choice(CLASSIFICATIONS)

        # Generate realistic content
        content = generate_realistic_content(title, department, classification)

        job = JobDescription(
            title=f"{title} - {i + 1:04d}",
            content=content,
            filename=f"job_{i + 1:04d}_{title.lower().replace(' ', '_')}.txt",
            language="en",
            status="completed",
            processing_time=random.uniform(1.0, 5.0),
            word_count=len(content.split()),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
        )

        session.add(job)
        jobs.append(job)

        if i % 100 == 0:
            session.commit()
            logger.info(f"Created {i + 1} job descriptions...")

    session.commit()
    logger.info(f"Successfully created {count} job descriptions")
    return jobs


def create_sample_metadata(session, jobs: List[JobDescription]):
    """Create sample metadata for job descriptions."""
    logger.info("Creating job metadata...")

    for i, job in enumerate(jobs):
        metadata = JobMetadata(
            job_id=job.id,
            classification=random.choice(CLASSIFICATIONS),
            department=random.choice(DEPARTMENTS),
            location="Ottawa, ON",
            employment_type="Full-time",
            salary_min=random.randint(50000, 80000),
            salary_max=random.randint(80000, 150000),
            reports_to=f"Director of {random.choice(DEPARTMENTS)}",
            team_size=random.randint(3, 15),
            travel_required=random.choice([True, False]),
            security_clearance=random.choice(
                ["None", "Reliability", "Secret", "Top Secret"]
            ),
            bilingual_required=random.choice([True, False]),
            metadata={
                "posting_date": (
                    datetime.utcnow() - timedelta(days=random.randint(0, 90))
                ).isoformat(),
                "application_deadline": (
                    datetime.utcnow() + timedelta(days=random.randint(1, 30))
                ).isoformat(),
                "budget_responsibility": random.randint(100000, 5000000),
                "performance_indicators": [
                    "Project delivery on time",
                    "Team satisfaction scores",
                    "Quality metrics achievement",
                ],
            },
        )
        session.add(metadata)

        if i % 100 == 0:
            session.commit()

    session.commit()
    logger.info("Successfully created job metadata")


def create_sample_content_chunks(session, jobs: List[JobDescription]):
    """Create sample content chunks for vector search testing."""
    logger.info("Creating content chunks...")

    for i, job in enumerate(jobs):
        # Split content into chunks
        words = job.content.split()
        chunk_size = 150

        for j in range(0, len(words), chunk_size):
            chunk_words = words[j : j + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunk = ContentChunk(
                job_id=job.id,
                chunk_index=j // chunk_size,
                chunk_text=chunk_text,
                chunk_type="body",
                word_count=len(chunk_words),
                embedding=[
                    random.uniform(-1, 1) for _ in range(1536)
                ],  # Mock embedding
            )
            session.add(chunk)

        if i % 50 == 0:
            session.commit()

    session.commit()
    logger.info("Successfully created content chunks")


def create_sample_search_analytics(session, count: int = 5000):
    """Create sample search analytics data."""
    logger.info(f"Creating {count} search analytics records...")

    search_queries = [
        "software engineer",
        "project manager",
        "data scientist",
        "developer",
        "analyst",
        "manager",
        "coordinator",
        "specialist",
        "director",
        "senior",
        "python",
        "javascript",
        "aws",
        "agile",
        "leadership",
        "communication",
    ]

    for i in range(count):
        query = random.choice(search_queries)

        analytics = SearchAnalytics(
            search_id=f"search_{i + 1:06d}",
            user_id=f"user_{random.randint(1, 100):03d}",
            session_id=f"session_{random.randint(1, 1000):04d}",
            ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            query_text=query,
            query_hash=f"hash_{hash(query) % 1000000:06d}",
            search_type=random.choice(["semantic", "fulltext", "hybrid"]),
            filters_applied={
                "department": (
                    random.choice(DEPARTMENTS) if random.random() > 0.7 else None
                ),
                "classification": (
                    random.choice(CLASSIFICATIONS) if random.random() > 0.8 else None
                ),
            },
            execution_time_ms=random.randint(50, 500),
            total_response_time_ms=random.randint(100, 800),
            embedding_time_ms=random.randint(20, 200),
            total_results=random.randint(0, 200),
            returned_results=min(20, random.randint(0, 50)),
            has_results="yes" if random.random() > 0.1 else "no",
            timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            api_version="1.0.0",
            client_type=random.choice(["web", "api", "mobile"]),
        )
        session.add(analytics)

        if i % 500 == 0:
            session.commit()
            logger.info(f"Created {i + 1} search analytics records...")

    session.commit()
    logger.info(f"Successfully created {count} search analytics records")


def create_sample_translation_data(session):
    """Create sample translation memory data."""
    logger.info("Creating translation memory data...")

    # Create translation project
    project = TranslationProject(
        name="Government Job Descriptions EN-FR",
        description="Translation project for government job descriptions",
        source_language="en",
        target_language="fr",
        project_type="job_descriptions",
    )
    session.add(project)
    session.commit()

    # Sample translation pairs
    translation_pairs = [
        (
            "Responsible for strategic planning",
            "Responsable de la planification stratégique",
        ),
        ("Manage team of professionals", "Gérer une équipe de professionnels"),
        (
            "Develop and implement policies",
            "Élaborer et mettre en œuvre des politiques",
        ),
        ("Coordinate with stakeholders", "Coordonner avec les parties prenantes"),
        ("Analyze business requirements", "Analyser les exigences commerciales"),
        ("Provide technical guidance", "Fournir des conseils techniques"),
        ("Ensure quality standards", "Assurer les normes de qualité"),
        ("Monitor project progress", "Surveiller les progrès du projet"),
        ("Facilitate team meetings", "Faciliter les réunions d'équipe"),
        ("Prepare detailed reports", "Préparer des rapports détaillés"),
    ]

    for i, (source, target) in enumerate(translation_pairs * 20):  # Create 200 entries
        tm_entry = TranslationMemory(
            project_id=project.id,
            source_text=f"{source} - Context {i // 10 + 1}",
            target_text=f"{target} - Contexte {i // 10 + 1}",
            source_language="en",
            target_language="fr",
            domain="government",
            subdomain="job_descriptions",
            quality_score=random.uniform(0.8, 1.0),
            confidence_score=random.uniform(0.85, 0.98),
            usage_count=random.randint(1, 50),
            context_hash=f"hash_{hash(source + target + str(i)) % 1000000:06d}",
            tm_metadata={
                "translator": f"translator_{random.randint(1, 5)}",
                "reviewed": random.choice([True, False]),
                "domain_specific": True,
            },
        )
        session.add(tm_entry)

    session.commit()
    logger.info("Successfully created translation memory data")


def create_sample_ai_usage_tracking(session, count: int = 1000):
    """Create sample AI usage tracking data."""
    logger.info(f"Creating {count} AI usage tracking records...")

    for i in range(count):
        tracking = AIUsageTracking(
            request_id=f"req_{i + 1:06d}",
            user_id=f"user_{random.randint(1, 100):03d}",
            endpoint=random.choice(["/search", "/translate", "/analyze", "/enhance"]),
            model_used=random.choice(
                ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002"]
            ),
            tokens_used=random.randint(100, 2000),
            cost_usd=random.uniform(0.001, 0.1),
            response_time_ms=random.randint(500, 3000),
            success=random.choice([True, False]) if random.random() > 0.95 else True,
            timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 60)),
        )
        session.add(tracking)

        if i % 100 == 0:
            session.commit()

    session.commit()
    logger.info(f"Successfully created {count} AI usage tracking records")


def main():
    """Main seeding function."""
    logger.info("Starting performance data seeding...")

    # Create database engine and session - use sync URL
    db_url = (
        settings.database_sync_url
        if hasattr(settings, "database_sync_url")
        else settings.database_url
    )
    # Convert async URL to sync if needed
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Create sample data
        jobs = create_sample_job_descriptions(session, count=1000)
        create_sample_metadata(session, jobs)
        create_sample_content_chunks(session, jobs)
        create_sample_search_analytics(session, count=5000)
        create_sample_translation_data(session)
        create_sample_ai_usage_tracking(session, count=1000)

        logger.info("Performance data seeding completed successfully!")

    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
