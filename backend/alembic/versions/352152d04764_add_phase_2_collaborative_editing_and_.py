"""Add Phase 2 collaborative editing and translation schema

Revision ID: 352152d04764
Revises: 014_optimize_vector_indexes
Create Date: 2025-09-18 22:05:19.844128

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import VECTOR


# revision identifiers, used by Alembic.
revision = '352152d04764'
down_revision = '014_optimize_vector_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Phase 2 database schema for collaborative editing and translation features."""

    # Create extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. User Management System
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            role VARCHAR(50) DEFAULT 'user',
            department VARCHAR(100),
            security_clearance VARCHAR(20),
            preferred_language VARCHAR(5) DEFAULT 'en',
            is_active BOOLEAN DEFAULT true,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            ip_address INET,
            user_agent TEXT,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            last_activity TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            preference_key VARCHAR(100) NOT NULL,
            preference_value JSONB,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now(),
            UNIQUE(user_id, preference_key)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS user_permissions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            resource_type VARCHAR(50) NOT NULL,
            resource_id INTEGER,
            permission_type VARCHAR(20) NOT NULL,
            granted_by INTEGER REFERENCES users(id),
            granted_at TIMESTAMP DEFAULT now(),
            expires_at TIMESTAMP,
            UNIQUE(user_id, resource_type, resource_id, permission_type)
        );
    """)

    # 2. Collaborative Editing System
    op.execute("""
        CREATE TABLE IF NOT EXISTS editing_sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(128) UNIQUE NOT NULL,
            job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
            created_by INTEGER REFERENCES users(id),
            session_type VARCHAR(20) DEFAULT 'editing',
            status VARCHAR(20) DEFAULT 'active',
            metadata JSONB,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now(),
            expires_at TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS editing_participants (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES editing_sessions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(20) DEFAULT 'editor',
            joined_at TIMESTAMP DEFAULT now(),
            last_activity TIMESTAMP DEFAULT now(),
            is_active BOOLEAN DEFAULT true,
            cursor_position JSONB,
            UNIQUE(session_id, user_id)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS document_changes (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES editing_sessions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id),
            change_type VARCHAR(20) NOT NULL,
            content_before TEXT,
            content_after TEXT,
            position_start INTEGER,
            position_end INTEGER,
            operation_data JSONB,
            applied_at TIMESTAMP DEFAULT now(),
            operation_id VARCHAR(128),
            parent_operation_id VARCHAR(128)
        );
    """)

    # 3. Translation Memory System
    op.execute("""
        CREATE TABLE IF NOT EXISTS translation_projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            source_language VARCHAR(5) NOT NULL,
            target_language VARCHAR(5) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS translation_memory (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES translation_projects(id) ON DELETE CASCADE,
            source_text TEXT NOT NULL,
            target_text TEXT NOT NULL,
            source_language VARCHAR(5) NOT NULL,
            target_language VARCHAR(5) NOT NULL,
            context_info JSONB,
            quality_score DECIMAL(3,2),
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS translation_embeddings (
            id SERIAL PRIMARY KEY,
            memory_id INTEGER REFERENCES translation_memory(id) ON DELETE CASCADE,
            embedding vector(1536),
            text_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    # 4. AI Integration & Content Enhancement
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_providers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            api_endpoint VARCHAR(500),
            model_name VARCHAR(100),
            capabilities JSONB,
            rate_limits JSONB,
            cost_per_token DECIMAL(10,8),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_content_enhancements (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id),
            enhancement_type VARCHAR(50) NOT NULL,
            original_content TEXT,
            enhanced_content TEXT,
            ai_provider_id INTEGER REFERENCES ai_providers(id),
            confidence_score DECIMAL(3,2),
            review_status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT now(),
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER REFERENCES users(id)
        );
    """)

    # 5. Advanced Analytics & Reporting
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_analytics (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            session_id INTEGER REFERENCES user_sessions(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            event_data JSONB,
            page_url VARCHAR(500),
            user_agent TEXT,
            ip_address INET,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            metric_value DECIMAL(15,4),
            metric_unit VARCHAR(20),
            metadata JSONB,
            recorded_at TIMESTAMP DEFAULT now()
        );
    """)

    # 6. Content Workflow & Approval
    op.execute("""
        CREATE TABLE IF NOT EXISTS content_workflows (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
            workflow_type VARCHAR(50) NOT NULL,
            current_stage VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            created_by INTEGER REFERENCES users(id),
            assigned_to INTEGER REFERENCES users(id),
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS content_approvals (
            id SERIAL PRIMARY KEY,
            workflow_id INTEGER REFERENCES content_workflows(id) ON DELETE CASCADE,
            approver_id INTEGER REFERENCES users(id),
            approval_stage VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            comments TEXT,
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    # 7. Performance Monitoring Tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS websocket_connections (
            id SERIAL PRIMARY KEY,
            connection_id VARCHAR(128) UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id),
            session_id INTEGER REFERENCES editing_sessions(id),
            ip_address INET,
            connected_at TIMESTAMP DEFAULT now(),
            last_ping TIMESTAMP DEFAULT now(),
            status VARCHAR(20) DEFAULT 'active'
        );
    """)

    # Create Performance Indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_editing_sessions_job_id ON editing_sessions(job_id);
        CREATE INDEX IF NOT EXISTS idx_editing_sessions_created_by ON editing_sessions(created_by);
        CREATE INDEX IF NOT EXISTS idx_document_changes_session_id ON document_changes(session_id);
        CREATE INDEX IF NOT EXISTS idx_document_changes_user_id ON document_changes(user_id);
        CREATE INDEX IF NOT EXISTS idx_translation_memory_project_id ON translation_memory(project_id);
        CREATE INDEX IF NOT EXISTS idx_translation_embeddings_memory_id ON translation_embeddings(memory_id);
        CREATE INDEX IF NOT EXISTS idx_ai_content_enhancements_job_id ON ai_content_enhancements(job_id);
        CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON user_analytics(user_id);
        CREATE INDEX IF NOT EXISTS idx_content_workflows_job_id ON content_workflows(job_id);
        CREATE INDEX IF NOT EXISTS idx_websocket_connections_user_id ON websocket_connections(user_id);
    """)

    # Create Vector Indexes for Translation Similarity Search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_translation_embeddings_vector_cosine
        ON translation_embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)


def downgrade() -> None:
    """Remove Phase 2 database schema."""

    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_translation_embeddings_vector_cosine;")
    op.execute("DROP INDEX IF EXISTS idx_websocket_connections_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_content_workflows_job_id;")
    op.execute("DROP INDEX IF EXISTS idx_user_analytics_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_ai_content_enhancements_job_id;")
    op.execute("DROP INDEX IF EXISTS idx_translation_embeddings_memory_id;")
    op.execute("DROP INDEX IF EXISTS idx_translation_memory_project_id;")
    op.execute("DROP INDEX IF EXISTS idx_document_changes_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_document_changes_session_id;")
    op.execute("DROP INDEX IF EXISTS idx_editing_sessions_created_by;")
    op.execute("DROP INDEX IF EXISTS idx_editing_sessions_job_id;")
    op.execute("DROP INDEX IF EXISTS idx_user_sessions_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_user_sessions_token;")
    op.execute("DROP INDEX IF EXISTS idx_users_username;")
    op.execute("DROP INDEX IF EXISTS idx_users_email;")

    # Drop tables in reverse dependency order
    op.drop_table('websocket_connections')
    op.drop_table('content_approvals')
    op.drop_table('content_workflows')
    op.drop_table('system_metrics')
    op.drop_table('user_analytics')
    op.drop_table('ai_content_enhancements')
    op.drop_table('ai_providers')
    op.drop_table('translation_embeddings')
    op.drop_table('translation_memory')
    op.drop_table('translation_projects')
    op.drop_table('document_changes')
    op.drop_table('editing_participants')
    op.drop_table('editing_sessions')
    op.drop_table('user_permissions')
    op.drop_table('user_preferences')
    op.drop_table('user_sessions')
    op.drop_table('users')