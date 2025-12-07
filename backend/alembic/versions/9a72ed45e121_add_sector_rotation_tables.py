"""add_sector_rotation_tables

Revision ID: 9a72ed45e121
Revises: 007_quarter_score_forecasts
Create Date: 2025-12-06 23:18:43.385118

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9a72ed45e121'
down_revision = '007_quarter_score_forecasts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create industries table
    if 'industries' not in existing_tables:
        op.create_table(
            'industries',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('industry_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('industry_id')
        )
        op.create_index('ix_industries_industry_id', 'industries', ['industry_id'], unique=True)
    
    # Create stocks table
    if 'stocks' not in existing_tables:
        op.create_table(
            'stocks',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('ticker', sa.String(), nullable=False),
            sa.Column('company_name', sa.String(), nullable=False),
            sa.Column('sector_id', sa.String(), nullable=True),
            sa.Column('industry_id', sa.String(), nullable=True),
            sa.Column('isin', sa.String(), nullable=True),
            sa.Column('exchange', sa.String(), nullable=True),
            sa.Column('shares_outstanding', sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ticker')
        )
        op.create_index('ix_stocks_ticker', 'stocks', ['ticker'], unique=True)
        op.create_index('ix_stocks_sector_id', 'stocks', ['sector_id'], unique=False)
        op.create_index('ix_stocks_industry_id', 'stocks', ['industry_id'], unique=False)
    
    # Create stock_time_series table
    if 'stock_time_series' not in existing_tables:
        op.create_table(
            'stock_time_series',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('ticker', sa.String(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('open', sa.Numeric(15, 2), nullable=False),
            sa.Column('high', sa.Numeric(15, 2), nullable=False),
            sa.Column('low', sa.Numeric(15, 2), nullable=False),
            sa.Column('close', sa.Numeric(15, 2), nullable=False),
            sa.Column('volume', sa.BigInteger(), nullable=False),
            sa.Column('deliverable_volume', sa.BigInteger(), nullable=True),
            sa.Column('turnover', sa.Numeric(20, 2), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ticker', 'date', name='uq_stock_time_series')
        )
        op.create_index('ix_stock_time_series_ticker', 'stock_time_series', ['ticker'], unique=False)
        op.create_index('ix_stock_time_series_date', 'stock_time_series', ['date'], unique=False)
    
    # Create stock_market_caps table
    if 'stock_market_caps' not in existing_tables:
        op.create_table(
            'stock_market_caps',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('ticker', sa.String(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('market_cap', sa.Numeric(20, 2), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ticker', 'date', name='uq_stock_market_caps')
        )
        op.create_index('ix_stock_market_caps_ticker', 'stock_market_caps', ['ticker'], unique=False)
        op.create_index('ix_stock_market_caps_date', 'stock_market_caps', ['date'], unique=False)
    
    # Create stock_technical_indicators table
    if 'stock_technical_indicators' not in existing_tables:
        op.create_table(
            'stock_technical_indicators',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('ticker', sa.String(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('sma20', sa.Numeric(15, 2), nullable=True),
            sa.Column('sma50', sa.Numeric(15, 2), nullable=True),
            sa.Column('sma100', sa.Numeric(15, 2), nullable=True),
            sa.Column('rsi14', sa.Numeric(6, 2), nullable=True),
            sa.Column('rs55', sa.Float(), nullable=True),
            sa.Column('return_1m', sa.Float(), nullable=True),
            sa.Column('return_3m', sa.Float(), nullable=True),
            sa.Column('return_6m', sa.Float(), nullable=True),
            sa.Column('vwap', sa.Numeric(15, 2), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ticker', 'date', name='uq_stock_technical_indicators')
        )
        op.create_index('ix_stock_technical_indicators_ticker', 'stock_technical_indicators', ['ticker'], unique=False)
        op.create_index('ix_stock_technical_indicators_date', 'stock_technical_indicators', ['date'], unique=False)
    
    # Create stock_rolling_stats table
    if 'stock_rolling_stats' not in existing_tables:
        op.create_table(
            'stock_rolling_stats',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('ticker', sa.String(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('avg_traded_value_20d', sa.Numeric(20, 2), nullable=True),
            sa.Column('avg_delivery_value_20d', sa.Numeric(20, 2), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('ticker', 'date', name='uq_stock_rolling_stats')
        )
        op.create_index('ix_stock_rolling_stats_ticker', 'stock_rolling_stats', ['ticker'], unique=False)
        op.create_index('ix_stock_rolling_stats_date', 'stock_rolling_stats', ['date'], unique=False)
    
    # Create sector_breadth_snapshots table
    if 'sector_breadth_snapshots' not in existing_tables:
        op.create_table(
            'sector_breadth_snapshots',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('sector_id', sa.String(), nullable=False),
            sa.Column('total_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('total_stocks', sa.Integer(), nullable=False),
            sa.Column('pct_mcap_rs55_gt0', sa.Float(), nullable=True),
            sa.Column('pct_mcap_rsi_gt50', sa.Float(), nullable=True),
            sa.Column('pct_mcap_above_sma20', sa.Float(), nullable=True),
            sa.Column('pct_mcap_above_sma50', sa.Float(), nullable=True),
            sa.Column('pct_mcap_above_sma100', sa.Float(), nullable=True),
            sa.Column('pct_count_rs55_gt0', sa.Float(), nullable=True),
            sa.Column('pct_count_rsi_gt50', sa.Float(), nullable=True),
            sa.Column('pct_count_above_sma20', sa.Float(), nullable=True),
            sa.Column('pct_count_above_sma50', sa.Float(), nullable=True),
            sa.Column('pct_count_above_sma100', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sector_id', 'date', name='uq_sector_breadth_snapshots')
        )
        op.create_index('ix_sector_breadth_snapshots_date', 'sector_breadth_snapshots', ['date'], unique=False)
        op.create_index('ix_sector_breadth_snapshots_sector_id', 'sector_breadth_snapshots', ['sector_id'], unique=False)
    
    # Create industry_breadth_snapshots table
    if 'industry_breadth_snapshots' not in existing_tables:
        op.create_table(
            'industry_breadth_snapshots',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('industry_id', sa.String(), nullable=False),
            sa.Column('total_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('total_stocks', sa.Integer(), nullable=False),
            sa.Column('pct_mcap_rs55_gt0', sa.Float(), nullable=True),
            sa.Column('pct_mcap_rsi_gt50', sa.Float(), nullable=True),
            sa.Column('pct_mcap_above_sma20', sa.Float(), nullable=True),
            sa.Column('pct_mcap_above_sma50', sa.Float(), nullable=True),
            sa.Column('pct_mcap_above_sma100', sa.Float(), nullable=True),
            sa.Column('pct_count_rs55_gt0', sa.Float(), nullable=True),
            sa.Column('pct_count_rsi_gt50', sa.Float(), nullable=True),
            sa.Column('pct_count_above_sma20', sa.Float(), nullable=True),
            sa.Column('pct_count_above_sma50', sa.Float(), nullable=True),
            sa.Column('pct_count_above_sma100', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('industry_id', 'date', name='uq_industry_breadth_snapshots')
        )
        op.create_index('ix_industry_breadth_snapshots_date', 'industry_breadth_snapshots', ['date'], unique=False)
        op.create_index('ix_industry_breadth_snapshots_industry_id', 'industry_breadth_snapshots', ['industry_id'], unique=False)
    
    # Create sector_momentum_scores table
    if 'sector_momentum_scores' not in existing_tables:
        op.create_table(
            'sector_momentum_scores',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('sector_id', sa.String(), nullable=False),
            sa.Column('total_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('total_stocks', sa.Integer(), nullable=False),
            sa.Column('score_1m', sa.Float(), nullable=True),
            sa.Column('score_3m', sa.Float(), nullable=True),
            sa.Column('score_6m', sa.Float(), nullable=True),
            sa.Column('return_1m', sa.Float(), nullable=True),
            sa.Column('return_3m', sa.Float(), nullable=True),
            sa.Column('return_6m', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sector_id', 'date', name='uq_sector_momentum_scores')
        )
        op.create_index('ix_sector_momentum_scores_date', 'sector_momentum_scores', ['date'], unique=False)
        op.create_index('ix_sector_momentum_scores_sector_id', 'sector_momentum_scores', ['sector_id'], unique=False)
    
    # Create industry_momentum_scores table
    if 'industry_momentum_scores' not in existing_tables:
        op.create_table(
            'industry_momentum_scores',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('industry_id', sa.String(), nullable=False),
            sa.Column('total_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('total_stocks', sa.Integer(), nullable=False),
            sa.Column('score_1m', sa.Float(), nullable=True),
            sa.Column('score_3m', sa.Float(), nullable=True),
            sa.Column('score_6m', sa.Float(), nullable=True),
            sa.Column('return_1m', sa.Float(), nullable=True),
            sa.Column('return_3m', sa.Float(), nullable=True),
            sa.Column('return_6m', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('industry_id', 'date', name='uq_industry_momentum_scores')
        )
        op.create_index('ix_industry_momentum_scores_date', 'industry_momentum_scores', ['date'], unique=False)
        op.create_index('ix_industry_momentum_scores_industry_id', 'industry_momentum_scores', ['industry_id'], unique=False)
    
    # Create sector_delivery_stats table
    if 'sector_delivery_stats' not in existing_tables:
        op.create_table(
            'sector_delivery_stats',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('sector_id', sa.String(), nullable=False),
            sa.Column('stocks_count', sa.Integer(), nullable=False),
            sa.Column('sector_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('sector_mcap_change_abs', sa.Numeric(20, 2), nullable=True),
            sa.Column('sector_mcap_change_pct', sa.Float(), nullable=True),
            sa.Column('traded_value', sa.Numeric(20, 2), nullable=True),
            sa.Column('traded_value_avg', sa.Numeric(20, 2), nullable=True),
            sa.Column('traded_value_multiple', sa.Float(), nullable=True),
            sa.Column('delivery_value', sa.Numeric(20, 2), nullable=True),
            sa.Column('delivery_value_avg', sa.Numeric(20, 2), nullable=True),
            sa.Column('delivery_value_multiple', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sector_id', 'date', name='uq_sector_delivery_stats')
        )
        op.create_index('ix_sector_delivery_stats_date', 'sector_delivery_stats', ['date'], unique=False)
        op.create_index('ix_sector_delivery_stats_sector_id', 'sector_delivery_stats', ['sector_id'], unique=False)
    
    # Create industry_delivery_stats table
    if 'industry_delivery_stats' not in existing_tables:
        op.create_table(
            'industry_delivery_stats',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('industry_id', sa.String(), nullable=False),
            sa.Column('stocks_count', sa.Integer(), nullable=False),
            sa.Column('industry_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('industry_mcap_change_abs', sa.Numeric(20, 2), nullable=True),
            sa.Column('industry_mcap_change_pct', sa.Float(), nullable=True),
            sa.Column('traded_value', sa.Numeric(20, 2), nullable=True),
            sa.Column('traded_value_avg', sa.Numeric(20, 2), nullable=True),
            sa.Column('traded_value_multiple', sa.Float(), nullable=True),
            sa.Column('delivery_value', sa.Numeric(20, 2), nullable=True),
            sa.Column('delivery_value_avg', sa.Numeric(20, 2), nullable=True),
            sa.Column('delivery_value_multiple', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('industry_id', 'date', name='uq_industry_delivery_stats')
        )
        op.create_index('ix_industry_delivery_stats_date', 'industry_delivery_stats', ['date'], unique=False)
        op.create_index('ix_industry_delivery_stats_industry_id', 'industry_delivery_stats', ['industry_id'], unique=False)
    
    # Create sector_vwap_snapshots table
    if 'sector_vwap_snapshots' not in existing_tables:
        op.create_table(
            'sector_vwap_snapshots',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('sector_id', sa.String(), nullable=False),
            sa.Column('total_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('pct_mcap_price_above_vwap', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sector_id', 'date', name='uq_sector_vwap_snapshots')
        )
        op.create_index('ix_sector_vwap_snapshots_date', 'sector_vwap_snapshots', ['date'], unique=False)
        op.create_index('ix_sector_vwap_snapshots_sector_id', 'sector_vwap_snapshots', ['sector_id'], unique=False)
    
    # Create industry_vwap_snapshots table
    if 'industry_vwap_snapshots' not in existing_tables:
        op.create_table(
            'industry_vwap_snapshots',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('industry_id', sa.String(), nullable=False),
            sa.Column('total_mcap', sa.Numeric(20, 2), nullable=False),
            sa.Column('pct_mcap_price_above_vwap', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('industry_id', 'date', name='uq_industry_vwap_snapshots')
        )
        op.create_index('ix_industry_vwap_snapshots_date', 'industry_vwap_snapshots', ['date'], unique=False)
        op.create_index('ix_industry_vwap_snapshots_industry_id', 'industry_vwap_snapshots', ['industry_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('industry_vwap_snapshots')
    op.drop_table('sector_vwap_snapshots')
    op.drop_table('industry_delivery_stats')
    op.drop_table('sector_delivery_stats')
    op.drop_table('industry_momentum_scores')
    op.drop_table('sector_momentum_scores')
    op.drop_table('industry_breadth_snapshots')
    op.drop_table('sector_breadth_snapshots')
    op.drop_table('stock_rolling_stats')
    op.drop_table('stock_technical_indicators')
    op.drop_table('stock_market_caps')
    op.drop_table('stock_time_series')
    op.drop_table('stocks')
    op.drop_table('industries')
