"""Create entity_metadata and transformations tables.

Revision ID: 001
Revises:
Create Date: 2026-08-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create entity_metadata table."""
    op.create_table(
        'entity_metadata',
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('domain_id', sa.VARCHAR(), nullable=False),
        sa.Column('created_by', sa.VARCHAR(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', sa.VARCHAR(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('tags', postgresql.JSON, nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('last_validated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('entity_id'),
        sa.Index('idx_metadata_domain', 'domain_id'),
        sa.Index('idx_metadata_quality', 'data_quality_score', postgresql.DESC()),
        sa.Index('idx_metadata_tags_gin', 'tags', postgresql_using='gin'),
        sa.Index('idx_metadata_updated_at', 'updated_at', postgresql.DESC()),
    )

    op.create_table(
        'transformations',
        sa.Column('transformation_id', sa.UUID(), nullable=False),
        sa.Column('operation_type', sa.VARCHAR(), nullable=False),
        sa.Column('input_entity_ids', postgresql.JSON, nullable=False),
        sa.Column('output_entity_id', sa.UUID(), nullable=False),
        sa.Column('transformation_rule', postgresql.JSON, nullable=False),
        sa.Column('performed_by', sa.VARCHAR(), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.VARCHAR(), nullable=False, server_default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('transformation_id'),
        sa.Index('idx_transformation_output', 'output_entity_id'),
        sa.Index('idx_transformation_type_date', 'operation_type', 'performed_at', postgresql.DESC()),
    )


def downgrade() -> None:
    """Drop transformations and entity_metadata tables."""
    op.drop_table('transformations')
    op.drop_table('entity_metadata')
