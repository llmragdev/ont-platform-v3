"""Create lineage_chains table.

Revision ID: 002
Revises: 001
Create Date: 2026-08-05 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create lineage_chains table."""
    op.create_table(
        'lineage_chains',
        sa.Column('lineage_id', sa.UUID(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('source_entities', postgresql.JSON, nullable=True),
        sa.Column('transformation_chain', postgresql.JSON, nullable=True),
        sa.Column('data_quality_chain', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('lineage_id'),
        sa.Index('idx_lineage_entity_id', 'entity_id'),
        sa.Index('idx_lineage_created_at', 'created_at', postgresql.DESC()),
        sa.Index('idx_lineage_sources_gin', 'source_entities', postgresql_using='gin'),
        sa.Index('idx_lineage_transformations_gin', 'transformation_chain', postgresql_using='gin'),
    )


def downgrade() -> None:
    """Drop lineage_chains table."""
    op.drop_table('lineage_chains')
