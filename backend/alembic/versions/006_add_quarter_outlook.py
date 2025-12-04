"""Add quarter outlook tables and extend sector_features

Revision ID: 006_quarter_outlook
Revises: 005_news_sentiment
Create Date: 2025-12-05 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_quarter_outlook'
down_revision = '005_news_sentiment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend sector_features with quarter outlook columns (check if they exist first)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('sector_features')]
    
    columns_to_add = [
        ('ret_3m', sa.Float()),
        ('ret_6m', sa.Float()),
        ('rel_1m_vs_nifty', sa.Float()),
        ('rel_3m_vs_nifty', sa.Float()),
        ('breadth_above_50dma', sa.Float()),
        ('breadth_3m_highs', sa.Float()),
        ('fii_net_inr_20d', sa.Numeric(15, 2)),
        ('fii_net_inr_percentile', sa.Float()),
        ('valuation_pe', sa.Float()),
        ('valuation_pe_percentile', sa.Float()),
        ('earnings_upgrades_pct_60d', sa.Float()),
        ('earnings_downgrades_pct_60d', sa.Float()),
        ('quarter_score', sa.Float()),
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            op.add_column('sector_features', sa.Column(col_name, col_type, nullable=True))
    
    # Create sector_breadth_daily table (if not exists)
    if 'sector_breadth_daily' not in inspector.get_table_names():
        op.create_table(
        'sector_breadth_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('total_constituents', sa.Integer(), nullable=True),
        sa.Column('above_50dma', sa.Integer(), nullable=True),
        sa.Column('above_200dma', sa.Integer(), nullable=True),
        sa.Column('making_3m_highs', sa.Integer(), nullable=True),
        sa.Column('making_3m_lows', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id', 'date', name='uq_sector_breadth')
    )
        op.create_index('ix_sector_breadth_daily_date', 'sector_breadth_daily', ['date'], unique=False)
        op.create_index('ix_sector_breadth_daily_sector_id', 'sector_breadth_daily', ['sector_id'], unique=False)
    
    # Create earnings_events table (if not exists)
    if 'earnings_events' not in inspector.get_table_names():
        op.create_table(
        'earnings_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('sector_id', sa.String(), nullable=True),
        sa.Column('eps_actual', sa.Numeric(10, 2), nullable=True),
        sa.Column('eps_estimate', sa.Numeric(10, 2), nullable=True),
        sa.Column('surprise_pct', sa.Float(), nullable=True),
        sa.Column('revision_direction', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index('ix_earnings_events_date', 'earnings_events', ['date'], unique=False)
        op.create_index('ix_earnings_events_ticker', 'earnings_events', ['ticker'], unique=False)
        op.create_index('ix_earnings_events_sector_id', 'earnings_events', ['sector_id'], unique=False)
    
    # Create sector_valuations_daily table (if not exists)
    if 'sector_valuations_daily' not in inspector.get_table_names():
        op.create_table(
        'sector_valuations_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('pe', sa.Numeric(10, 2), nullable=True),
        sa.Column('pb', sa.Numeric(10, 2), nullable=True),
        sa.Column('div_yield', sa.Numeric(6, 4), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id', 'date', name='uq_sector_valuations')
    )
        op.create_index('ix_sector_valuations_daily_date', 'sector_valuations_daily', ['date'], unique=False)
        op.create_index('ix_sector_valuations_daily_sector_id', 'sector_valuations_daily', ['sector_id'], unique=False)
    
    # Create market_sentiment_daily table (if not exists)
    if 'market_sentiment_daily' not in inspector.get_table_names():
        op.create_table(
        'market_sentiment_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('india_vix', sa.Numeric(6, 2), nullable=True),
        sa.Column('india_vix_percentile', sa.Float(), nullable=True),
        sa.Column('index_pcr', sa.Float(), nullable=True),
        sa.Column('breadth_nifty500_above_50dma', sa.Float(), nullable=True),
        sa.Column('news_sentiment_score_7d', sa.Float(), nullable=True),
        sa.Column('regime_label', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_market_sentiment_date')
    )
        op.create_index('ix_market_sentiment_daily_date', 'market_sentiment_daily', ['date'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_market_sentiment_daily_date', table_name='market_sentiment_daily')
    op.drop_table('market_sentiment_daily')
    op.drop_index('ix_sector_valuations_daily_sector_id', table_name='sector_valuations_daily')
    op.drop_index('ix_sector_valuations_daily_date', table_name='sector_valuations_daily')
    op.drop_table('sector_valuations_daily')
    op.drop_index('ix_earnings_events_sector_id', table_name='earnings_events')
    op.drop_index('ix_earnings_events_ticker', table_name='earnings_events')
    op.drop_index('ix_earnings_events_date', table_name='earnings_events')
    op.drop_table('earnings_events')
    op.drop_index('ix_sector_breadth_daily_sector_id', table_name='sector_breadth_daily')
    op.drop_index('ix_sector_breadth_daily_date', table_name='sector_breadth_daily')
    op.drop_table('sector_breadth_daily')
    
    op.drop_column('sector_features', 'quarter_score')
    op.drop_column('sector_features', 'earnings_downgrades_pct_60d')
    op.drop_column('sector_features', 'earnings_upgrades_pct_60d')
    op.drop_column('sector_features', 'valuation_pe_percentile')
    op.drop_column('sector_features', 'valuation_pe')
    op.drop_column('sector_features', 'fii_net_inr_percentile')
    op.drop_column('sector_features', 'fii_net_inr_20d')
    op.drop_column('sector_features', 'breadth_3m_highs')
    op.drop_column('sector_features', 'breadth_above_50dma')
    op.drop_column('sector_features', 'rel_3m_vs_nifty')
    op.drop_column('sector_features', 'rel_1m_vs_nifty')
    op.drop_column('sector_features', 'ret_6m')
    op.drop_column('sector_features', 'ret_3m')

