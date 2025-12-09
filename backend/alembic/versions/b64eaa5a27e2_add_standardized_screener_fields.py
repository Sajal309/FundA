"""add_standardized_screener_fields

Revision ID: b64eaa5a27e2
Revises: 5aef5afceaa4
Create Date: 2025-12-09 21:59:25.640247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b64eaa5a27e2'
down_revision = '9a72ed45e121'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to stock_fundamentals table for standardized screener fields
    op.add_column('stock_fundamentals', sa.Column('sales', sa.Numeric(20, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('pe', sa.Numeric(8, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('dividend_yield', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('roe_3y', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('roe_5y', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('qtr_profit_var_pct', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('qtr_sales_var_pct', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('pledged_percent', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('promoter_holding', sa.Numeric(6, 2), nullable=True))
    op.add_column('stock_fundamentals', sa.Column('public_holding', sa.Numeric(6, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('stock_fundamentals', 'public_holding')
    op.drop_column('stock_fundamentals', 'promoter_holding')
    op.drop_column('stock_fundamentals', 'pledged_percent')
    op.drop_column('stock_fundamentals', 'qtr_sales_var_pct')
    op.drop_column('stock_fundamentals', 'qtr_profit_var_pct')
    op.drop_column('stock_fundamentals', 'roe_5y')
    op.drop_column('stock_fundamentals', 'roe_3y')
    op.drop_column('stock_fundamentals', 'dividend_yield')
    op.drop_column('stock_fundamentals', 'pe')
    op.drop_column('stock_fundamentals', 'sales')

