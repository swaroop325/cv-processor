"""Initial tables

Revision ID: 001_initial_tables
Revises:
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create CV table
    op.create_table(
        'cv',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('skills', postgresql.JSON(), nullable=True),
        sa.Column('experience', postgresql.JSON(), nullable=True),
        sa.Column('education', postgresql.JSON(), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('embedding_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embedding_generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_cv_email', 'cv', ['email'])
    op.execute('CREATE INDEX idx_cv_embedding ON cv USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')

    # Create JD table
    op.create_table(
        'jd',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=False),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('required_skills', postgresql.JSON(), nullable=True),
        sa.Column('preferred_skills', postgresql.JSON(), nullable=True),
        sa.Column('benefits', postgresql.JSON(), nullable=True),
        sa.Column('employment_type', sa.String(50), nullable=True),
        sa.Column('experience_level', sa.String(50), nullable=True),
        sa.Column('salary_range', postgresql.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('embedding_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embedding_generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_jd_is_active', 'jd', ['is_active'])
    op.execute('CREATE INDEX idx_jd_embedding ON jd USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    op.drop_index('idx_jd_embedding')
    op.drop_index('ix_jd_is_active')
    op.drop_table('jd')

    op.drop_index('idx_cv_embedding')
    op.drop_index('ix_cv_email')
    op.drop_table('cv')
