"""v3 initial schema

Revision ID: 0001_v3
Revises:
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_v3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ca_company",
        sa.Column("tenant_id", sa.String(length=64), primary_key=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "ca_org_mgnt",
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=8), nullable=False),
        sa.Column("org_name", sa.String(length=255), nullable=False),
        sa.Column("dept_code", sa.String(length=2), nullable=False),
        sa.Column("org_level", sa.Integer(), nullable=False),
        sa.Column("parent_org_id", sa.String(length=8), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["ca_company.tenant_id"]),
        sa.PrimaryKeyConstraint("tenant_id", "org_id"),
    )
    op.create_table(
        "ca_user",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=8), nullable=True),
        sa.Column("user_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["ca_company.tenant_id"]),
    )
    op.create_table(
        "wc_project",
        sa.Column("project_code", sa.String(length=6), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("vector_db_id", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["ca_company.tenant_id"]),
    )
    op.create_table(
        "wc_category",
        sa.Column("category_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category_mid", sa.String(length=128), nullable=False),
        sa.Column("category_low", sa.String(length=128), nullable=True),
        sa.Column("vector_db_id", sa.String(length=128), nullable=False),
    )
    op.create_table(
        "wc_intent",
        sa.Column("intent_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("intent_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_table(
        "wc_project_rag_doc",
        sa.Column("doc_id", sa.String(length=64), primary_key=True),
        sa.Column("project_code", sa.String(length=6), nullable=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=8), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("pipeline_status", sa.String(length=32), nullable=False),
        sa.Column("assigned_vector_db", sa.String(length=128), nullable=False),
        sa.Column("category_mid", sa.String(length=128), nullable=False),
        sa.Column("category_low", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["ca_company.tenant_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "org_id"], ["ca_org_mgnt.tenant_id", "ca_org_mgnt.org_id"]),
    )
    op.create_table(
        "wc_dialog_history",
        sa.Column("dialog_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=8), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("used_chunks", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["ca_company.tenant_id"]),
    )


def downgrade() -> None:
    op.drop_table("wc_dialog_history")
    op.drop_table("wc_project_rag_doc")
    op.drop_table("wc_intent")
    op.drop_table("wc_category")
    op.drop_table("wc_project")
    op.drop_table("ca_user")
    op.drop_table("ca_org_mgnt")
    op.drop_table("ca_company")

