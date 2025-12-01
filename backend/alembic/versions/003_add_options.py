"""Add options daily table

Revision ID: 003_options
Revises: 002_flows_macro
Create Date: 2025-11-28 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_options'
down_revision = '002_flows_macro'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create options_daily table
    op.create_table(
        'options_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('underlying', sa.String(), nullable=False),
        sa.Column('expiry', sa.Date(), nullable=True),
        sa.Column('total_call_oi', sa.BigInteger(), nullable=True),
        sa.Column('total_put_oi', sa.BigInteger(), nullable=True),
        sa.Column('pcr_oi', sa.Float(), nullable=True),
        sa.Column('pcr_volume', sa.Float(), nullable=True),
        sa.Column('total_call_volume', sa.BigInteger(), nullable=True),
        sa.Column('total_put_volume', sa.BigInteger(), nullable=True),
        sa.Column('oi_change_1d', sa.Float(), nullable=True),
        sa.Column('oi_change_3d', sa.Float(), nullable=True),
        sa.Column('iv_index', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('underlying', 'date', name='uq_options_daily')
    )
    op.create_index('ix_options_daily_date', 'options_daily', ['date'], unique=False)
    op.create_index('ix_options_daily_underlying', 'options_daily', ['underlying'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_options_daily_underlying', table_name='options_daily')
    op.drop_index('ix_options_daily_date', table_name='options_daily')
    op.drop_table('options_daily')

