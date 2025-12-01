"""Add news and sentiment tables

Revision ID: 005_news_sentiment
Revises: 004_options_features
Create Date: 2025-11-28 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_news_sentiment'
down_revision = '004_options_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create news_headlines table
    op.create_table(
        'news_headlines',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('headline', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('sector_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sentiment_label', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_news_headlines_date', 'news_headlines', ['date'], unique=False)

    # Create sector_sentiment_daily table
    op.create_table(
        'sector_sentiment_daily',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('sector_id', sa.String(), nullable=False),
        sa.Column('sentiment_score_1d', sa.Float(), nullable=True),
        sa.Column('sentiment_score_7d', sa.Float(), nullable=True),
        sa.Column('headline_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id', 'date', name='uq_sector_sentiment')
    )
    op.create_index('ix_sector_sentiment_daily_date', 'sector_sentiment_daily', ['date'], unique=False)
    op.create_index('ix_sector_sentiment_daily_sector_id', 'sector_sentiment_daily', ['sector_id'], unique=False)

    # Add sentiment fields to sector_features
    op.add_column('sector_features', sa.Column('sentiment_score_1d', sa.Float(), nullable=True))
    op.add_column('sector_features', sa.Column('sentiment_score_7d', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('sector_features', 'sentiment_score_7d')
    op.drop_column('sector_features', 'sentiment_score_1d')
    op.drop_index('ix_sector_sentiment_daily_sector_id', table_name='sector_sentiment_daily')
    op.drop_index('ix_sector_sentiment_daily_date', table_name='sector_sentiment_daily')
    op.drop_table('sector_sentiment_daily')
    op.drop_index('ix_news_headlines_date', table_name='news_headlines')
    op.drop_table('news_headlines')

