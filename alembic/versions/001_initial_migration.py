"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-06-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create initial tables."""
    # Create company_profiles table
    op.create_table(
        'company_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_url', sa.String(2048), nullable=False, index=True),
        sa.Column('source_url_hash', sa.String(64), unique=True, index=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('company_description', sa.Text, nullable=True),
        sa.Column('industry', sa.String(255), nullable=True),
        sa.Column('website', sa.String(2048), nullable=True),
        sa.Column('employee_count', sa.Integer, nullable=True),
        sa.Column('employee_count_range', sa.String(50), nullable=True),
        sa.Column('funding_stage', sa.String(100), nullable=True),
        sa.Column('total_funding', sa.Float, nullable=True),
        sa.Column('headquarters', sa.String(255), nullable=True),
        sa.Column('linkedin_url', sa.String(2048), nullable=True),
        sa.Column('twitter_url', sa.String(2048), nullable=True),
        sa.Column('logo_url', sa.String(2048), nullable=True),
        sa.Column('founded_year', sa.Integer, nullable=True),
        sa.Column('completeness_score', sa.Float, default=0.0),
        sa.Column('confidence_score', sa.Float, default=0.0),
        sa.Column('processing_time_ms', sa.Integer, default=0),
        sa.Column('analysis_timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('enrichment_enabled', sa.Boolean, default=False),
        sa.Column('enrichment_complete', sa.Boolean, default=False),
        sa.Column('locations', sa.JSON, nullable=True),
        sa.Column('tech_stack', sa.JSON, nullable=True),
        sa.Column('benefits', sa.JSON, nullable=True),
        sa.Column('culture_keywords', sa.JSON, nullable=True),
        sa.Column('enrichment_sources', sa.JSON, nullable=True),
        sa.Column('enrichment_errors', sa.JSON, nullable=True),
        sa.Column('markdown_report', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create crawl_logs table
    op.create_table(
        'crawl_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('profile_id', sa.String(36), nullable=False, index=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('status_code', sa.Integer, nullable=True),
        sa.Column('success', sa.Boolean, default=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('content_length', sa.Integer, nullable=True),
        sa.Column('robots_txt_allowed', sa.Boolean, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )

def downgrade() -> None:
    """Drop tables."""
    op.drop_table('crawl_logs')
    op.drop_table('company_profiles')