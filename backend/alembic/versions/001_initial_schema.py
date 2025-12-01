"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sector_time_series table
    op.create_table(
        'sector_time_series',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Numeric(15, 2), nullable=False),
        sa.Column('high', sa.Numeric(15, 2), nullable=False),
        sa.Column('low', sa.Numeric(15, 2), nullable=False),
        sa.Column('close', sa.Numeric(15, 2), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sector_time_series_sector_id', 'sector_time_series', ['sector_id'], unique=False)
    op.create_index('ix_sector_time_series_ts', 'sector_time_series', ['ts'], unique=False)

    # Create sector_features table
    op.create_table(
        'sector_features',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('ret_1d', sa.Float(), nullable=True),
        sa.Column('ret_5d', sa.Float(), nullable=True),
        sa.Column('ret_1m', sa.Float(), nullable=True),
        sa.Column('ma20', sa.Float(), nullable=True),
        sa.Column('ma50', sa.Float(), nullable=True),
        sa.Column('rsi', sa.Float(), nullable=True),
        sa.Column('fii_net_inr', sa.BigInteger(), nullable=True),
        sa.Column('brent_pct_change_7d', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id', 'date', name='uq_sector_features')
    )
    op.create_index('ix_sector_features_sector_id', 'sector_features', ['sector_id'], unique=False)
    op.create_index('ix_sector_features_date', 'sector_features', ['date'], unique=False)

    # Create sector_forecasts table
    op.create_table(
        'sector_forecasts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('forecast_3m_label', sa.String(), nullable=False),
        sa.Column('prob_up', sa.Float(), nullable=False),
        sa.Column('prob_neutral', sa.Float(), nullable=False),
        sa.Column('prob_down', sa.Float(), nullable=False),
        sa.Column('expected_return_pct', sa.Float(), nullable=False),
        sa.Column('top_drivers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id', 'date', name='uq_sector_forecasts')
    )
    op.create_index('ix_sector_forecasts_sector_id', 'sector_forecasts', ['sector_id'], unique=False)
    op.create_index('ix_sector_forecasts_date', 'sector_forecasts', ['date'], unique=False)

    # Create sector_constituents table
    op.create_table(
        'sector_constituents',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('weight_pct', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sector_constituents_sector_id', 'sector_constituents', ['sector_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sector_constituents_sector_id', table_name='sector_constituents')
    op.drop_table('sector_constituents')
    op.drop_index('ix_sector_forecasts_date', table_name='sector_forecasts')
    op.drop_index('ix_sector_forecasts_sector_id', table_name='sector_forecasts')
    op.drop_table('sector_forecasts')
    op.drop_index('ix_sector_features_date', table_name='sector_features')
    op.drop_index('ix_sector_features_sector_id', table_name='sector_features')
    op.drop_table('sector_features')
    op.drop_index('ix_sector_time_series_ts', table_name='sector_time_series')
    op.drop_index('ix_sector_time_series_sector_id', table_name='sector_time_series')
    op.drop_table('sector_time_series')

