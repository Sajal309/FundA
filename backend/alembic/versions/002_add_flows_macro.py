"""Add flows and macro tables

Revision ID: 002_flows_macro
Revises: 001_initial
Create Date: 2025-11-28 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_flows_macro'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create fii_dii_daily table
    op.create_table(
        'fii_dii_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=True),
        sa.Column('fii_buy', sa.BigInteger(), nullable=True),
        sa.Column('fii_sell', sa.BigInteger(), nullable=True),
        sa.Column('dii_buy', sa.BigInteger(), nullable=True),
        sa.Column('dii_sell', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fii_dii_daily_date', 'fii_dii_daily', ['date'], unique=False)
    op.create_index('ix_fii_dii_daily_ticker', 'fii_dii_daily', ['ticker'], unique=False)

    # Create sector_flows_daily table
    op.create_table(
        'sector_flows_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('fii_net_inr', sa.BigInteger(), nullable=True),
        sa.Column('dii_net_inr', sa.BigInteger(), nullable=True),
        sa.Column('fii_gross', sa.BigInteger(), nullable=True),
        sa.Column('dii_gross', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id', 'date', name='uq_sector_flows')
    )
    op.create_index('ix_sector_flows_daily_date', 'sector_flows_daily', ['date'], unique=False)
    op.create_index('ix_sector_flows_daily_sector_id', 'sector_flows_daily', ['sector_id'], unique=False)

    # Create macro_daily table
    op.create_table(
        'macro_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('usd_inr_close', sa.Numeric(10, 4), nullable=True),
        sa.Column('usd_inr_pct_1d', sa.Float(), nullable=True),
        sa.Column('brent_close', sa.Numeric(10, 2), nullable=True),
        sa.Column('brent_pct_7d', sa.Float(), nullable=True),
        sa.Column('gold_close', sa.Numeric(10, 2), nullable=True),
        sa.Column('us_10y_close', sa.Numeric(6, 4), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_macro_daily_date')
    )
    op.create_index('ix_macro_daily_date', 'macro_daily', ['date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_macro_daily_date', table_name='macro_daily')
    op.drop_table('macro_daily')
    op.drop_index('ix_sector_flows_daily_sector_id', table_name='sector_flows_daily')
    op.drop_index('ix_sector_flows_daily_date', table_name='sector_flows_daily')
    op.drop_table('sector_flows_daily')
    op.drop_index('ix_fii_dii_daily_ticker', table_name='fii_dii_daily')
    op.drop_index('ix_fii_dii_daily_date', table_name='fii_dii_daily')
    op.drop_table('fii_dii_daily')

