"""add_audit_log_table

Revision ID: 6375fbf9a927
Revises: 352152d04764
Create Date: 2025-09-19 07:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6375fbf9a927'
down_revision = '352152d04764'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add audit log table for comprehensive activity tracking."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            user_id INTEGER,
            username VARCHAR(100),
            timestamp TIMESTAMP NOT NULL DEFAULT now(),
            resource_type VARCHAR(50),
            resource_id INTEGER,
            action VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            ip_address INET,
            user_agent TEXT,
            session_id VARCHAR(128),
            details JSONB,
            before_state JSONB,
            after_state JSONB,
            success BOOLEAN DEFAULT true,
            error_message TEXT,
            event_hash VARCHAR(64),
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    # Create indexes for efficient querying
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_severity ON audit_log(severity);
        CREATE INDEX IF NOT EXISTS idx_audit_log_session_id ON audit_log(session_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_success ON audit_log(success);
    """)

    # Create a partial index for failed events (security monitoring)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_failures
        ON audit_log(timestamp, event_type, user_id)
        WHERE success = false;
    """)


def downgrade() -> None:
    """Remove audit log table."""

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_audit_log_failures;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_success;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_session_id;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_severity;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_resource;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_timestamp;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_event_type;")

    # Drop table
    op.drop_table('audit_log')