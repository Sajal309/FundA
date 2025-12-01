"""Add options features to sector_features

Revision ID: 004_options_features
Revises: 003_options
Create Date: 2025-11-28 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_options_features'
down_revision = '003_options'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add options-based feature columns to sector_features
    op.add_column('sector_features', sa.Column('pcr_oi', sa.Float(), nullable=True))
    op.add_column('sector_features', sa.Column('oi_change_1d', sa.Float(), nullable=True))
    op.add_column('sector_features', sa.Column('oi_change_3d', sa.Float(), nullable=True))
    op.add_column('sector_features', sa.Column('iv_index', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('sector_features', 'iv_index')
    op.drop_column('sector_features', 'oi_change_3d')
    op.drop_column('sector_features', 'oi_change_1d')
    op.drop_column('sector_features', 'pcr_oi')

