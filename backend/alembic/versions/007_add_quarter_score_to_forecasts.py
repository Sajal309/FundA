"""Add quarter_score and drivers to sector_forecasts

Revision ID: 007_quarter_score_forecasts
Revises: 006_quarter_outlook
Create Date: 2025-12-05 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_quarter_score_forecasts'
down_revision = '006_quarter_outlook'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add quarter_score and drivers to sector_forecasts
    op.add_column('sector_forecasts', sa.Column('quarter_score', sa.Float(), nullable=True))
    op.add_column('sector_forecasts', sa.Column('drivers', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('sector_forecasts', 'drivers')
    op.drop_column('sector_forecasts', 'quarter_score')

