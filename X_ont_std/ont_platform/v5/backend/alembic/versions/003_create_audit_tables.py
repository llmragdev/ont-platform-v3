"""Create entity_versions and audit_logs tables.

Revision ID: 003
Revises: 002
Create Date: 2026-08-05 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create entity_versions and audit_logs tables."""
    op.create_table(
        'entity_versions',
        sa.Column('version_id', sa.UUID(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSON, nullable=False),
        sa.Column('changed_fields', postgresql.JSON, nullable=True),
        sa.Column('changed_by', sa.VARCHAR(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('rollback_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.UniqueConstraint('entity_id', 'version_number', name='uq_entity_version'),
        sa.Index('idx_entity_versions_entity_id', 'entity_id'),
        sa.Index('idx_entity_versions_changed_at', 'changed_at', postgresql.DESC()),
    )

    op.create_table(
        'audit_logs',
        sa.Column('audit_id', sa.UUID(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.VARCHAR(), nullable=False),
        sa.Column('old_value', postgresql.JSON, nullable=True),
        sa.Column('new_value', postgresql.JSON, nullable=True),
        sa.Column('performed_by', sa.VARCHAR(), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('ip_address', sa.VARCHAR(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.VARCHAR(), nullable=False, server_default='success'),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default='365'),
        sa.PrimaryKeyConstraint('audit_id'),
        sa.Index('idx_audit_entity_id', 'entity_id'),
        sa.Index('idx_audit_performed_by', 'performed_by'),
        sa.Index('idx_audit_performed_at', 'performed_at', postgresql.DESC()),
        sa.Index('idx_audit_action', 'action'),
        sa.Index('idx_audit_entity_action_date', 'entity_id', 'action', 'performed_at', postgresql.DESC()),
        sa.Index('idx_audit_performed_by_date', 'performed_by', 'performed_at', postgresql.DESC()),
        sa.Index('idx_audit_action_status', 'action', 'status'),
    )


def downgrade() -> None:
    """Drop entity_versions and audit_logs tables."""
    op.drop_table('audit_logs')
    op.drop_table('entity_versions')
