# Phase 2 Database Schema Extensions
*Collaborative Editing, Translation, and User Management*

## Overview

This document defines the database schema extensions required for JDDB Phase 2, supporting real-time collaborative editing, translation concordance, and enhanced user management.

## Current Schema Foundation

### Existing Tables (Phase 1)
- `job_descriptions` - Core job description data
- `job_sections` - Parsed content sections
- `content_chunks` - AI-ready text chunks
- `job_metadata` - Structured metadata fields
- `ai_usage_tracking` - OpenAI API usage monitoring

## New Schema Extensions for Phase 2

### 1. User Management System

```sql
-- Users table for authentication and authorization
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user', -- 'admin', 'editor', 'translator', 'reviewer', 'user'
    department VARCHAR(100),
    security_clearance VARCHAR(20), -- 'public', 'confidential', 'secret', 'top_secret'
    preferred_language VARCHAR(5) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User sessions for authentication tracking
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW()
);

-- User preferences and settings
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- User permissions for fine-grained access control
CREATE TABLE user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- 'job_description', 'editing_session', 'translation'
    resource_id INTEGER,
    permission_type VARCHAR(20) NOT NULL, -- 'read', 'write', 'delete', 'share', 'approve'
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(user_id, resource_type, resource_id, permission_type)
);
```

### 2. Collaborative Editing System

```sql
-- Editing sessions for real-time collaboration
CREATE TABLE editing_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) UNIQUE NOT NULL,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    created_by INTEGER REFERENCES users(id),
    session_type VARCHAR(20) DEFAULT 'editing', -- 'editing', 'translation', 'review', 'approval'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'completed', 'cancelled'
    collaborators INTEGER[] DEFAULT '{}',
    document_state JSONB DEFAULT '{}',
    editor_config JSONB DEFAULT '{}', -- Editor settings, layout preferences
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Real-time document changes with operational transform support
CREATE TABLE document_changes (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    change_sequence INTEGER NOT NULL, -- For ordering changes
    change_type VARCHAR(20) NOT NULL, -- 'insert', 'delete', 'retain', 'format', 'replace'
    operation_data JSONB NOT NULL, -- Operational transform data
    position INTEGER NOT NULL,
    length INTEGER DEFAULT 0,
    content_before TEXT,
    content_after TEXT,
    section_type VARCHAR(50), -- Which section was modified
    timestamp TIMESTAMP DEFAULT NOW(),
    transformed_from INTEGER REFERENCES document_changes(id),
    conflict_resolved BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,
    reverted_at TIMESTAMP
);

-- WebSocket connection tracking for real-time features
CREATE TABLE websocket_connections (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    connection_id VARCHAR(128) UNIQUE NOT NULL,
    server_instance VARCHAR(100), -- For load balancing across multiple servers
    connected_at TIMESTAMP DEFAULT NOW(),
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    disconnected_at TIMESTAMP,
    user_agent TEXT,
    ip_address INET,
    connection_status VARCHAR(20) DEFAULT 'active' -- 'active', 'idle', 'disconnected'
);

-- Collaborative editing locks (prevent conflicts on specific sections)
CREATE TABLE editing_locks (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    resource_type VARCHAR(50) NOT NULL, -- 'section', 'paragraph', 'sentence'
    resource_identifier VARCHAR(255) NOT NULL, -- Section name, paragraph ID, etc.
    lock_type VARCHAR(20) DEFAULT 'exclusive', -- 'exclusive', 'shared'
    acquired_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    released_at TIMESTAMP,
    auto_release BOOLEAN DEFAULT TRUE
);

-- Comments and annotations on documents
CREATE TABLE document_comments (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    user_id INTEGER REFERENCES users(id),
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(20) DEFAULT 'general', -- 'general', 'suggestion', 'correction', 'approval'
    position_start INTEGER,
    position_end INTEGER,
    section_type VARCHAR(50),
    referenced_text TEXT,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'resolved', 'dismissed'
    parent_comment_id INTEGER REFERENCES document_comments(id),
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Translation Concordance System

```sql
-- Translation document pairs for bilingual management
CREATE TABLE translation_pairs (
    id SERIAL PRIMARY KEY,
    source_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    target_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    source_language VARCHAR(5) NOT NULL,
    target_language VARCHAR(5) NOT NULL,
    pair_type VARCHAR(20) DEFAULT 'manual', -- 'manual', 'automatic', 'hybrid'
    alignment_method VARCHAR(20), -- 'sentence', 'paragraph', 'section'
    alignment_quality DECIMAL(3,2),
    alignment_confidence DECIMAL(3,2),
    translator_id INTEGER REFERENCES users(id),
    reviewer_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'review', 'approved', 'rejected'
    translation_memory_hits INTEGER DEFAULT 0,
    ai_assistance_used BOOLEAN DEFAULT FALSE,
    human_post_editing BOOLEAN DEFAULT FALSE,
    quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    approved_at TIMESTAMP
);

-- Sentence-level alignments for translation concordance
CREATE TABLE sentence_alignments (
    id SERIAL PRIMARY KEY,
    translation_pair_id INTEGER REFERENCES translation_pairs(id) ON DELETE CASCADE,
    source_sentence TEXT NOT NULL,
    target_sentence TEXT NOT NULL,
    source_position_start INTEGER,
    source_position_end INTEGER,
    target_position_start INTEGER,
    target_position_end INTEGER,
    confidence_score DECIMAL(3,2),
    alignment_type VARCHAR(20), -- 'automatic', 'manual', 'validated', 'corrected'
    alignment_method VARCHAR(50), -- 'embedding_similarity', 'statistical', 'manual'
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Translation memory corpus for reusable translations
CREATE TABLE translation_memory (
    id SERIAL PRIMARY KEY,
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL,
    source_language VARCHAR(5) NOT NULL,
    target_language VARCHAR(5) NOT NULL,
    domain VARCHAR(50), -- 'government', 'hr', 'technical', 'legal'
    subdomain VARCHAR(50), -- 'job_descriptions', 'policies', 'procedures'
    quality_score DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    context_hash VARCHAR(64), -- For similar context matching
    metadata JSONB DEFAULT '{}',
    source_embedding VECTOR(1536), -- OpenAI embedding for similarity search
    target_embedding VECTOR(1536),
    created_by INTEGER REFERENCES users(id),
    validated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Terminology management for consistent translations
CREATE TABLE terminology_glossary (
    id SERIAL PRIMARY KEY,
    term_source VARCHAR(255) NOT NULL,
    term_target VARCHAR(255) NOT NULL,
    source_language VARCHAR(5) NOT NULL,
    target_language VARCHAR(5) NOT NULL,
    domain VARCHAR(50),
    category VARCHAR(50), -- 'job_title', 'department', 'skill', 'qualification'
    definition_source TEXT,
    definition_target TEXT,
    usage_notes TEXT,
    context_examples JSONB, -- Example usage in context
    frequency_score INTEGER DEFAULT 0,
    approval_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    created_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    reviewed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Translation sessions for workflow tracking
CREATE TABLE translation_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id) ON DELETE CASCADE,
    translation_pair_id INTEGER REFERENCES translation_pairs(id),
    translator_id INTEGER REFERENCES users(id),
    session_type VARCHAR(20) DEFAULT 'translation', -- 'translation', 'review', 'post_editing'
    source_document_state JSONB DEFAULT '{}',
    target_document_state JSONB DEFAULT '{}',
    alignment_data JSONB DEFAULT '{}',
    translation_memory_hits INTEGER DEFAULT 0,
    ai_suggestions_used INTEGER DEFAULT 0,
    human_overrides INTEGER DEFAULT 0,
    terminology_hits INTEGER DEFAULT 0,
    productivity_metrics JSONB DEFAULT '{}', -- Words per hour, etc.
    quality_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### 4. AI Assistance and Enhancement System

```sql
-- AI suggestions and enhancements for content improvement
CREATE TABLE ai_suggestions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    user_id INTEGER REFERENCES users(id),
    suggestion_type VARCHAR(50) NOT NULL, -- 'grammar', 'style', 'compliance', 'content', 'translation'
    ai_provider VARCHAR(50), -- 'openai', 'claude', 'copilot', 'gemini'
    ai_model VARCHAR(100),
    original_text TEXT NOT NULL,
    suggested_text TEXT NOT NULL,
    context_before TEXT,
    context_after TEXT,
    section_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    explanation TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'modified'
    user_action VARCHAR(20), -- 'accepted', 'rejected', 'modified', 'ignored'
    applied_text TEXT, -- Final text if user modified the suggestion
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP
);

-- AI usage tracking for cost management and analytics
CREATE TABLE ai_usage_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    user_id INTEGER REFERENCES users(id),
    ai_provider VARCHAR(50) NOT NULL,
    feature_type VARCHAR(50), -- 'content_generation', 'translation', 'grammar_check', 'enhancement'
    tokens_used INTEGER,
    api_calls INTEGER DEFAULT 1,
    estimated_cost DECIMAL(10,4),
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Content compliance validation
CREATE TABLE compliance_checks (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    check_type VARCHAR(50) NOT NULL, -- 'policy', 'accessibility', 'language', 'format'
    rule_name VARCHAR(100),
    rule_description TEXT,
    compliance_status VARCHAR(20), -- 'compliant', 'warning', 'violation'
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    location_start INTEGER,
    location_end INTEGER,
    section_type VARCHAR(50),
    flagged_text TEXT,
    recommendation TEXT,
    auto_fixable BOOLEAN DEFAULT FALSE,
    fix_applied BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5. Workflow and Approval System

```sql
-- Document approval workflows
CREATE TABLE approval_workflows (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(100) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(50), -- 'job_description', 'translation', 'policy_change'
    steps JSONB NOT NULL, -- Array of workflow steps with requirements
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document approval instances
CREATE TABLE document_approvals (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    workflow_id INTEGER REFERENCES approval_workflows(id),
    current_step INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'approved', 'rejected', 'cancelled'
    submitted_by INTEGER REFERENCES users(id),
    submitted_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Individual approval steps
CREATE TABLE approval_steps (
    id SERIAL PRIMARY KEY,
    approval_id INTEGER REFERENCES document_approvals(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100),
    assigned_to INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'delegated'
    comments TEXT,
    decision_date TIMESTAMP,
    deadline TIMESTAMP,
    delegated_to INTEGER REFERENCES users(id),
    delegated_at TIMESTAMP
);

-- Version control for documents
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    version_type VARCHAR(20) DEFAULT 'minor', -- 'major', 'minor', 'patch', 'draft'
    content_snapshot JSONB NOT NULL, -- Full document content
    changes_summary TEXT,
    created_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'published', 'archived'
    created_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    archived_at TIMESTAMP,
    UNIQUE(job_id, version_number)
);
```

### 6. Analytics and Reporting

```sql
-- Enhanced usage analytics for Phase 2 features
CREATE TABLE usage_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(128),
    action_type VARCHAR(50) NOT NULL, -- 'document_edit', 'translation', 'ai_suggestion', 'collaboration'
    feature_used VARCHAR(50),
    duration_seconds INTEGER,
    success BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance metrics tracking
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL, -- 'response_time', 'websocket_latency', 'ai_response_time'
    metric_value DECIMAL(10,3),
    measurement_unit VARCHAR(20), -- 'milliseconds', 'seconds', 'requests_per_second'
    context JSONB DEFAULT '{}',
    measured_at TIMESTAMP DEFAULT NOW()
);

-- User activity logs for audit trails
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW()
);

-- System health monitoring
CREATE TABLE system_health (
    id SERIAL PRIMARY KEY,
    component VARCHAR(50) NOT NULL, -- 'database', 'websocket', 'ai_service', 'redis'
    status VARCHAR(20) NOT NULL, -- 'healthy', 'warning', 'error', 'critical'
    metrics JSONB DEFAULT '{}',
    error_message TEXT,
    checked_at TIMESTAMP DEFAULT NOW()
);
```

## Database Indexes for Performance

```sql
-- Editing Sessions Indexes
CREATE INDEX idx_editing_sessions_job_id ON editing_sessions(job_id);
CREATE INDEX idx_editing_sessions_created_by ON editing_sessions(created_by);
CREATE INDEX idx_editing_sessions_status ON editing_sessions(status);
CREATE INDEX idx_editing_sessions_last_activity ON editing_sessions(last_activity);

-- Document Changes Indexes
CREATE INDEX idx_document_changes_session_id ON document_changes(session_id);
CREATE INDEX idx_document_changes_user_id ON document_changes(user_id);
CREATE INDEX idx_document_changes_timestamp ON document_changes(timestamp);
CREATE INDEX idx_document_changes_sequence ON document_changes(session_id, change_sequence);

-- WebSocket Connections Indexes
CREATE INDEX idx_websocket_connections_session_id ON websocket_connections(session_id);
CREATE INDEX idx_websocket_connections_user_id ON websocket_connections(user_id);
CREATE INDEX idx_websocket_connections_status ON websocket_connections(connection_status);

-- Translation Memory Indexes
CREATE INDEX idx_translation_memory_languages ON translation_memory(source_language, target_language);
CREATE INDEX idx_translation_memory_domain ON translation_memory(domain, subdomain);
CREATE INDEX idx_translation_memory_quality ON translation_memory(quality_score);
CREATE INDEX idx_translation_memory_usage ON translation_memory(usage_count);

-- Vector similarity indexes for translation memory
CREATE INDEX idx_translation_memory_source_embedding ON translation_memory
USING ivfflat (source_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_translation_memory_target_embedding ON translation_memory
USING ivfflat (target_embedding vector_cosine_ops) WITH (lists = 100);

-- AI Suggestions Indexes
CREATE INDEX idx_ai_suggestions_job_id ON ai_suggestions(job_id);
CREATE INDEX idx_ai_suggestions_session_id ON ai_suggestions(session_id);
CREATE INDEX idx_ai_suggestions_type_status ON ai_suggestions(suggestion_type, status);
CREATE INDEX idx_ai_suggestions_created_at ON ai_suggestions(created_at);

-- User Activity Indexes
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);
CREATE INDEX idx_activity_logs_resource ON activity_logs(resource_type, resource_id);

-- Performance optimization indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
```

## Database Triggers and Functions

```sql
-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_translation_memory_updated_at BEFORE UPDATE ON translation_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-cleanup expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    -- Close expired editing sessions
    UPDATE editing_sessions
    SET status = 'expired'
    WHERE expires_at < NOW() AND status = 'active';

    -- Remove expired user sessions
    DELETE FROM user_sessions WHERE expires_at < NOW();

    -- Remove old websocket connections
    DELETE FROM websocket_connections
    WHERE disconnected_at < NOW() - INTERVAL '24 hours';

    -- Release expired locks
    UPDATE editing_locks
    SET released_at = NOW()
    WHERE expires_at < NOW() AND released_at IS NULL;
END;
$$ language 'plpgsql';

-- Schedule cleanup function (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired-sessions', '*/15 * * * *', 'SELECT cleanup_expired_sessions()');
```

## Data Migration Plan

```sql
-- Migration script for Phase 2 schema deployment
-- This should be run as part of Alembic migration

-- 1. Create new tables in dependency order
-- 2. Populate initial data
INSERT INTO approval_workflows (workflow_name, description, workflow_type, steps, created_by) VALUES
('Standard Job Description Review', 'Standard 3-step review process for job descriptions', 'job_description',
 '[{"step": 1, "name": "Manager Review", "role": "manager"},
   {"step": 2, "name": "HR Review", "role": "hr"},
   {"step": 3, "name": "Final Approval", "role": "director"}]', 1);

-- 3. Update existing data to maintain compatibility
-- Add default version for existing job descriptions
INSERT INTO document_versions (job_id, version_number, version_type, content_snapshot, created_by, status, published_at)
SELECT id, '1.0.0', 'major',
       jsonb_build_object('title', title, 'content', raw_content, 'sections',
         (SELECT jsonb_agg(jsonb_build_object('type', section_type, 'content', section_content))
          FROM job_sections WHERE job_id = job_descriptions.id)),
       1, 'published', created_at
FROM job_descriptions;
```

## Schema Validation Rules

```sql
-- Add constraints for data integrity
ALTER TABLE editing_sessions ADD CONSTRAINT check_session_type
    CHECK (session_type IN ('editing', 'translation', 'review', 'approval'));

ALTER TABLE document_changes ADD CONSTRAINT check_change_type
    CHECK (change_type IN ('insert', 'delete', 'retain', 'format', 'replace'));

ALTER TABLE translation_pairs ADD CONSTRAINT check_languages
    CHECK (source_language != target_language);

ALTER TABLE ai_suggestions ADD CONSTRAINT check_confidence_score
    CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0);

ALTER TABLE translation_memory ADD CONSTRAINT check_quality_score
    CHECK (quality_score >= 0.0 AND quality_score <= 1.0);

-- Ensure proper language codes
ALTER TABLE translation_memory ADD CONSTRAINT check_language_codes
    CHECK (source_language ~ '^[a-z]{2}(-[A-Z]{2})?$' AND target_language ~ '^[a-z]{2}(-[A-Z]{2})?$');
```

## Security Considerations

### Row-Level Security (RLS)

```sql
-- Enable RLS for sensitive tables
ALTER TABLE editing_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE translation_pairs ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY editing_sessions_access ON editing_sessions
    FOR ALL TO authenticated_users
    USING (created_by = current_user_id() OR current_user_id() = ANY(collaborators));

CREATE POLICY document_changes_access ON document_changes
    FOR ALL TO authenticated_users
    USING (session_id IN (
        SELECT session_id FROM editing_sessions
        WHERE created_by = current_user_id() OR current_user_id() = ANY(collaborators)
    ));

-- Function to get current user ID (to be implemented based on auth system)
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS INTEGER AS $$
BEGIN
    -- Implementation depends on authentication system
    -- Could use session variables, JWT claims, etc.
    RETURN COALESCE(current_setting('app.user_id', true)::INTEGER, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Performance Monitoring Queries

```sql
-- Monitor active editing sessions
SELECT
    COUNT(*) as active_sessions,
    AVG(array_length(collaborators, 1)) as avg_collaborators,
    MAX(last_activity) as most_recent_activity
FROM editing_sessions
WHERE status = 'active';

-- Check WebSocket connection health
SELECT
    connection_status,
    COUNT(*) as connection_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - last_heartbeat))) as avg_seconds_since_heartbeat
FROM websocket_connections
GROUP BY connection_status;

-- Translation memory utilization
SELECT
    domain,
    COUNT(*) as total_entries,
    AVG(usage_count) as avg_usage,
    MAX(last_used) as most_recent_use
FROM translation_memory
GROUP BY domain;

-- AI suggestion acceptance rates
SELECT
    suggestion_type,
    COUNT(*) as total_suggestions,
    COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted,
    ROUND(COUNT(CASE WHEN status = 'accepted' THEN 1 END) * 100.0 / COUNT(*), 2) as acceptance_rate
FROM ai_suggestions
GROUP BY suggestion_type;
```

This comprehensive database schema provides the foundation for all Phase 2 features while maintaining scalability, security, and performance requirements for government-level usage.
