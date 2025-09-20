#!/usr/bin/env python3
"""
Development database seeding script for Phase 2 features.

This script creates sample data for testing collaborative editing,
translation memory, user management, and other Phase 2 features.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
import hashlib
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from jd_ingestion.database.connection import get_async_session


async def create_sample_users(db: AsyncSession) -> List[int]:
    """Create sample users for testing collaborative features."""

    users_data = [
        {
            "username": "admin_user",
            "email": "admin@jddb.gov.ca",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "department": "IT",
            "security_clearance": "SECRET",
            "preferred_language": "en"
        },
        {
            "username": "editor_john",
            "email": "john.smith@jddb.gov.ca",
            "password_hash": hashlib.sha256("editor123".encode()).hexdigest(),
            "first_name": "John",
            "last_name": "Smith",
            "role": "editor",
            "department": "HR",
            "security_clearance": "PROTECTED_B",
            "preferred_language": "en"
        },
        {
            "username": "editor_marie",
            "email": "marie.tremblay@jddb.gov.ca",
            "password_hash": hashlib.sha256("editor123".encode()).hexdigest(),
            "first_name": "Marie",
            "last_name": "Tremblay",
            "role": "editor",
            "department": "HR",
            "security_clearance": "PROTECTED_B",
            "preferred_language": "fr"
        },
        {
            "username": "translator_bob",
            "email": "bob.wilson@jddb.gov.ca",
            "password_hash": hashlib.sha256("translator123".encode()).hexdigest(),
            "first_name": "Bob",
            "last_name": "Wilson",
            "role": "translator",
            "department": "Translation Services",
            "security_clearance": "PROTECTED_A",
            "preferred_language": "en"
        },
        {
            "username": "reviewer_sarah",
            "email": "sarah.johnson@jddb.gov.ca",
            "password_hash": hashlib.sha256("reviewer123".encode()).hexdigest(),
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": "reviewer",
            "department": "Quality Assurance",
            "security_clearance": "PROTECTED_B",
            "preferred_language": "en"
        }
    ]

    user_ids = []
    for user_data in users_data:
        result = await db.execute(text("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, role,
                             department, security_clearance, preferred_language, is_active)
            VALUES (:username, :email, :password_hash, :first_name, :last_name, :role,
                    :department, :security_clearance, :preferred_language, true)
            ON CONFLICT (username) DO UPDATE SET
                email = EXCLUDED.email,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
            RETURNING id
        """), user_data)

        user_id = result.fetchone()[0]
        user_ids.append(user_id)
        print(f"Created user: {user_data['username']} (ID: {user_id})")

    await db.commit()
    return user_ids


async def create_user_preferences(db: AsyncSession, user_ids: List[int]):
    """Create sample user preferences."""

    preferences_data = [
        # Admin preferences - converted to work with existing table structure
        {"user_id": str(user_ids[0]), "preference_type": "ui", "preference_key": "theme", "preference_value": {"mode": "dark", "color": "blue"}},
        {"user_id": str(user_ids[0]), "preference_type": "ui", "preference_key": "editor_settings", "preference_value": {"font_size": 14, "line_numbers": True}},
        {"user_id": str(user_ids[0]), "preference_type": "ui", "preference_key": "notifications", "preference_value": {"email": True, "browser": True}},

        # Editor preferences
        {"user_id": str(user_ids[1]), "preference_type": "ui", "preference_key": "theme", "preference_value": {"mode": "light", "color": "green"}},
        {"user_id": str(user_ids[1]), "preference_type": "ui", "preference_key": "editor_settings", "preference_value": {"font_size": 12, "line_numbers": False}},

        # French editor preferences
        {"user_id": str(user_ids[2]), "preference_type": "ui", "preference_key": "theme", "preference_value": {"mode": "light", "color": "red"}},
        {"user_id": str(user_ids[2]), "preference_type": "ui", "preference_key": "language_settings", "preference_value": {"spell_check": "fr", "dictionary": "canadian_french"}},

        # Translator preferences
        {"user_id": str(user_ids[3]), "preference_type": "ui", "preference_key": "translation_settings", "preference_value": {"auto_save": True, "memory_threshold": 0.8}},
        {"user_id": str(user_ids[3]), "preference_type": "ui", "preference_key": "editor_settings", "preference_value": {"split_view": True, "sync_scroll": True}},
    ]

    for pref in preferences_data:
        # Use string user_id and include preference_type to match existing table structure
        await db.execute(text("""
            INSERT INTO user_preferences (user_id, session_id, preference_type, preference_key, preference_value)
            VALUES (:user_id, NULL, :preference_type, :preference_key, CAST(:preference_value AS jsonb))
            ON CONFLICT (user_id, session_id, preference_type, preference_key) DO UPDATE SET
                preference_value = EXCLUDED.preference_value
        """), {
            "user_id": pref["user_id"],  # Already converted to string above
            "preference_type": pref["preference_type"],
            "preference_key": pref["preference_key"],
            "preference_value": json.dumps(pref["preference_value"])  # Convert dict to JSON string
        })

    await db.commit()
    print(f"Created {len(preferences_data)} user preferences")


async def create_ai_providers(db: AsyncSession) -> List[int]:
    """Create sample AI providers configuration."""

    providers_data = [
        {
            "name": "OpenAI GPT-4",
            "api_endpoint": "https://api.openai.com/v1",
            "model_name": "gpt-4",
            "capabilities": {"text_generation": True, "translation": True, "summarization": True},
            "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 40000},
            "cost_per_token": 0.00003,
            "is_active": True
        },
        {
            "name": "Anthropic Claude",
            "api_endpoint": "https://api.anthropic.com/v1",
            "model_name": "claude-3-sonnet",
            "capabilities": {"text_generation": True, "translation": True, "analysis": True},
            "rate_limits": {"requests_per_minute": 50, "tokens_per_minute": 30000},
            "cost_per_token": 0.00002,
            "is_active": True
        },
        {
            "name": "Google Gemini",
            "api_endpoint": "https://generativelanguage.googleapis.com/v1",
            "model_name": "gemini-pro",
            "capabilities": {"text_generation": True, "translation": True, "multimodal": True},
            "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 32000},
            "cost_per_token": 0.000025,
            "is_active": False
        }
    ]

    provider_ids = []
    for provider in providers_data:
        result = await db.execute(text("""
            INSERT INTO ai_providers (name, api_endpoint, model_name, capabilities, rate_limits, cost_per_token, is_active)
            VALUES (:name, :api_endpoint, :model_name, :capabilities, :rate_limits, :cost_per_token, :is_active)
            ON CONFLICT (name) DO UPDATE SET
                api_endpoint = EXCLUDED.api_endpoint,
                model_name = EXCLUDED.model_name,
                is_active = EXCLUDED.is_active
            RETURNING id
        """), {
            **provider,
            "capabilities": json.dumps(provider["capabilities"]),
            "rate_limits": json.dumps(provider["rate_limits"])
        })

        provider_id = result.fetchone()[0]
        provider_ids.append(provider_id)
        print(f"Created AI provider: {provider['name']} (ID: {provider_id})")

    await db.commit()
    return provider_ids


async def create_translation_projects(db: AsyncSession, user_ids: List[int]) -> List[int]:
    """Create sample translation projects."""

    projects_data = [
        {
            "name": "Government Job Descriptions EN-FR",
            "description": "Translation project for government job descriptions from English to French",
            "source_language": "en",
            "target_language": "fr",
            "status": "active",
            "created_by": user_ids[3]  # translator_bob
        },
        {
            "name": "Technical Documentation FR-EN",
            "description": "Translation of technical documentation from French to English",
            "source_language": "fr",
            "target_language": "en",
            "status": "active",
            "created_by": user_ids[3]  # translator_bob
        },
        {
            "name": "Policy Documents Bilingual Review",
            "description": "Bilingual review and improvement of policy documents",
            "source_language": "en",
            "target_language": "fr",
            "status": "completed",
            "created_by": user_ids[2]  # editor_marie
        }
    ]

    project_ids = []
    for project in projects_data:
        result = await db.execute(text("""
            INSERT INTO translation_projects (name, description, source_language, target_language, status, created_by)
            VALUES (:name, :description, :source_language, :target_language, :status, :created_by)
            RETURNING id
        """), project)

        project_id = result.fetchone()[0]
        project_ids.append(project_id)
        print(f"Created translation project: {project['name']} (ID: {project_id})")

    await db.commit()
    return project_ids


async def create_translation_memory(db: AsyncSession, project_ids: List[int], user_ids: List[int]):
    """Create sample translation memory entries."""

    memory_data = [
        {
            "project_id": project_ids[0],
            "source_text": "The candidate must have strong analytical skills and experience with data analysis.",
            "target_text": "Le candidat doit posséder de solides compétences analytiques et une expérience en analyse de données.",
            "source_language": "en",
            "target_language": "fr",
            "context_info": {"domain": "job_requirements", "section": "qualifications"},
            "quality_score": 0.95,
            "created_by": user_ids[3]
        },
        {
            "project_id": project_ids[0],
            "source_text": "Excellent communication skills, both written and oral, are required.",
            "target_text": "D'excellentes compétences en communication, tant écrites qu'orales, sont requises.",
            "source_language": "en",
            "target_language": "fr",
            "context_info": {"domain": "job_requirements", "section": "skills"},
            "quality_score": 0.92,
            "created_by": user_ids[3]
        },
        {
            "project_id": project_ids[0],
            "source_text": "This position requires a Bachelor's degree in Computer Science or related field.",
            "target_text": "Ce poste exige un baccalauréat en informatique ou dans un domaine connexe.",
            "source_language": "en",
            "target_language": "fr",
            "context_info": {"domain": "education_requirements", "section": "qualifications"},
            "quality_score": 0.98,
            "created_by": user_ids[2]
        },
        {
            "project_id": project_ids[1],
            "source_text": "Assurer la maintenance et le support technique des systèmes informatiques.",
            "target_text": "Provide maintenance and technical support for computer systems.",
            "source_language": "fr",
            "target_language": "en",
            "context_info": {"domain": "job_duties", "section": "responsibilities"},
            "quality_score": 0.89,
            "created_by": user_ids[3]
        }
    ]

    for memory in memory_data:
        await db.execute(text("""
            INSERT INTO translation_memory (project_id, source_text, target_text, source_language,
                                          target_language, context_info, quality_score, created_by)
            VALUES (:project_id, :source_text, :target_text, :source_language,
                    :target_language, :context_info, :quality_score, :created_by)
        """), {
            **memory,
            "context_info": json.dumps(memory["context_info"])
        })

    await db.commit()
    print(f"Created {len(memory_data)} translation memory entries")


async def create_editing_sessions(db: AsyncSession, user_ids: List[int]):
    """Create sample editing sessions for testing collaborative features."""

    # Get a sample job ID from existing data
    result = await db.execute(text("SELECT id FROM job_descriptions LIMIT 1"))
    job_row = result.fetchone()

    if not job_row:
        print("No job descriptions found. Creating a sample job first...")
        await db.execute(text("""
            INSERT INTO job_descriptions (job_number, title, classification, language, file_path, raw_content)
            VALUES ('SAMPLE-001', 'Sample Job for Testing', 'EX-01', 'en', '/sample/test.txt',
                    'This is a sample job description for testing collaborative editing features.')
        """))
        await db.commit()

        result = await db.execute(text("SELECT id FROM job_descriptions WHERE job_number = 'SAMPLE-001'"))
        job_row = result.fetchone()

    job_id = job_row[0]

    sessions_data = [
        {
            "session_id": str(uuid.uuid4()),
            "job_id": job_id,
            "created_by": user_ids[1],  # editor_john
            "session_type": "editing",
            "status": "active",
            "metadata": {"version": "1.0", "last_save": datetime.utcnow().isoformat()},
            "expires_at": datetime.utcnow() + timedelta(hours=8)
        },
        {
            "session_id": str(uuid.uuid4()),
            "job_id": job_id,
            "created_by": user_ids[2],  # editor_marie
            "session_type": "review",
            "status": "paused",
            "metadata": {"version": "1.1", "review_stage": "content"},
            "expires_at": datetime.utcnow() + timedelta(hours=4)
        }
    ]

    session_ids = []
    for session in sessions_data:
        result = await db.execute(text("""
            INSERT INTO editing_sessions (session_id, job_id, created_by, session_type, status, metadata, expires_at)
            VALUES (:session_id, :job_id, :created_by, :session_type, :status, :metadata, :expires_at)
            RETURNING id
        """), {
            **session,
            "metadata": json.dumps(session["metadata"])
        })

        session_id = result.fetchone()[0]
        session_ids.append(session_id)
        print(f"Created editing session: {session['session_type']} (ID: {session_id})")

    await db.commit()
    return session_ids


async def create_sample_analytics(db: AsyncSession, user_ids: List[int]):
    """Create sample analytics data for testing dashboards."""

    # Create system metrics
    metrics_data = [
        {"metric_name": "active_users", "metric_value": 25, "metric_unit": "count", "metadata": {"daily": True}},
        {"metric_name": "documents_processed", "metric_value": 150, "metric_unit": "count", "metadata": {"weekly": True}},
        {"metric_name": "translation_requests", "metric_value": 45, "metric_unit": "count", "metadata": {"daily": True}},
        {"metric_name": "system_uptime", "metric_value": 99.8, "metric_unit": "percent", "metadata": {"weekly": True}},
        {"metric_name": "avg_response_time", "metric_value": 120.5, "metric_unit": "milliseconds", "metadata": {"hourly": True}}
    ]

    for metric in metrics_data:
        await db.execute(text("""
            INSERT INTO system_metrics (metric_name, metric_value, metric_unit, metadata)
            VALUES (:metric_name, :metric_value, :metric_unit, :metadata)
        """), {
            **metric,
            "metadata": json.dumps(metric["metadata"])
        })

    # Create user analytics events
    events_data = [
        {"user_id": user_ids[1], "event_type": "document_edit", "event_data": {"document_id": 1, "changes": 15}},
        {"user_id": user_ids[2], "event_type": "translation_request", "event_data": {"source": "en", "target": "fr"}},
        {"user_id": user_ids[3], "event_type": "search_performed", "event_data": {"query": "data analyst", "results": 23}},
        {"user_id": user_ids[0], "event_type": "user_login", "event_data": {"ip": "10.0.0.1", "browser": "Chrome"}},
    ]

    for event in events_data:
        await db.execute(text("""
            INSERT INTO user_analytics (user_id, event_type, event_data, page_url, ip_address)
            VALUES (:user_id, :event_type, :event_data, '/dashboard', '10.0.0.1')
        """), {
            **event,
            "event_data": json.dumps(event["event_data"])
        })

    await db.commit()
    print(f"Created {len(metrics_data)} system metrics and {len(events_data)} user events")


async def main():
    """Main seeding function."""
    print("Starting Phase 2 database seeding...")
    print("=" * 50)

    try:
        async for db in get_async_session():
            # Create sample users
            print("\n[USERS] Creating sample users...")
            user_ids = await create_sample_users(db)

            # Create user preferences
            print("\n[PREFS] Creating user preferences...")
            await create_user_preferences(db, user_ids)

            # Create AI providers
            print("\n[AI] Creating AI providers...")
            provider_ids = await create_ai_providers(db)

            # Create translation projects
            print("\n[TRANS] Creating translation projects...")
            project_ids = await create_translation_projects(db, user_ids)

            # Create translation memory
            print("\n[MEMORY] Creating translation memory...")
            await create_translation_memory(db, project_ids, user_ids)

            # Create editing sessions
            print("\n[SESSIONS] Creating editing sessions...")
            session_ids = await create_editing_sessions(db, user_ids)

            # Create sample analytics
            print("\n[ANALYTICS] Creating sample analytics...")
            await create_sample_analytics(db, user_ids)

            print("\n" + "=" * 50)
            print("SUCCESS: Phase 2 database seeding completed successfully!")
            print(f"   Created {len(user_ids)} users")
            print(f"   Created {len(provider_ids)} AI providers")
            print(f"   Created {len(project_ids)} translation projects")
            print(f"   Created {len(session_ids)} editing sessions")
            print("\nYour development environment is ready for Phase 2 testing!")

            break  # Exit the async generator

    except Exception as e:
        print(f"\nERROR: Error during seeding: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())