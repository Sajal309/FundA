"""add_standardized_screener_fields

Revision ID: b64eaa5a27e2
Revises: 5aef5afceaa4
Create Date: 2025-12-09 21:59:25.640247

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'b64eaa5a27e2'
down_revision = '9a72ed45e121'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # Create table if it does not exist (fresh databases in this branch)
    if 'stock_fundamentals' not in inspector.get_table_names():
        op.create_table(
            'stock_fundamentals',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('ticker', sa.String(), nullable=False, index=True),
            sa.Column('date', sa.Date(), nullable=False, index=True),
            sa.Column('market_cap', sa.Numeric(20, 2), nullable=True),
            sa.Column('sales', sa.Numeric(20, 2), nullable=True),
            sa.Column('pe', sa.Numeric(8, 2), nullable=True),
            sa.Column('dividend_yield', sa.Numeric(6, 2), nullable=True),
            sa.Column('roe', sa.Numeric(6, 2), nullable=True),
            sa.Column('roe_3y', sa.Numeric(6, 2), nullable=True),
            sa.Column('roe_5y', sa.Numeric(6, 2), nullable=True),
            sa.Column('roce', sa.Numeric(6, 2), nullable=True),
            sa.Column('roa', sa.Numeric(6, 2), nullable=True),
            sa.Column('operating_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('ebit_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('ebitda_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('gross_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('net_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('sales_growth_5y', sa.Numeric(6, 2), nullable=True),
            sa.Column('profit_growth_5y', sa.Numeric(6, 2), nullable=True),
            sa.Column('revenue_growth_5y', sa.Numeric(6, 2), nullable=True),
            sa.Column('qtr_profit_var_pct', sa.Numeric(6, 2), nullable=True),
            sa.Column('qtr_sales_var_pct', sa.Numeric(6, 2), nullable=True),
            sa.Column('debt_to_equity', sa.Numeric(8, 2), nullable=True),
            sa.Column('interest_coverage', sa.Numeric(8, 2), nullable=True),
            sa.Column('net_interest_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('gross_npa', sa.Numeric(6, 2), nullable=True),
            sa.Column('net_npa', sa.Numeric(6, 2), nullable=True),
            sa.Column('provision_coverage', sa.Numeric(6, 2), nullable=True),
            sa.Column('casa_ratio', sa.Numeric(6, 2), nullable=True),
            sa.Column('capital_adequacy', sa.Numeric(6, 2), nullable=True),
            sa.Column('aum_growth_5y', sa.Numeric(6, 2), nullable=True),
            sa.Column('solvency_ratio', sa.Numeric(6, 2), nullable=True),
            sa.Column('vnb_margin', sa.Numeric(6, 2), nullable=True),
            sa.Column('embedded_value_growth_5y', sa.Numeric(6, 2), nullable=True),
            sa.Column('opex_to_sales', sa.Numeric(6, 2), nullable=True),
            sa.Column('rnd_to_sales', sa.Numeric(6, 2), nullable=True),
            sa.Column('export_share', sa.Numeric(6, 2), nullable=True),
            sa.Column('bed_occupancy', sa.Numeric(6, 2), nullable=True),
            sa.Column('inventory_days', sa.Integer(), nullable=True),
            sa.Column('order_book_growth_3y', sa.Numeric(6, 2), nullable=True),
            sa.Column('order_book_to_sales', sa.Numeric(8, 2), nullable=True),
            sa.Column('order_book_visibility_years', sa.Numeric(4, 1), nullable=True),
            sa.Column('arpu_growth', sa.Numeric(6, 2), nullable=True),
            sa.Column('free_cash_flow', sa.Numeric(20, 2), nullable=True),
            sa.Column('pledged_percent', sa.Numeric(6, 2), nullable=True),
            sa.Column('promoter_holding', sa.Numeric(6, 2), nullable=True),
            sa.Column('public_holding', sa.Numeric(6, 2), nullable=True),
            sa.UniqueConstraint('ticker', 'date', name='uq_stock_fundamentals')
        )
        return

    # Existing databases: add missing standardized columns defensively
    existing_cols = {col["name"] for col in inspector.get_columns('stock_fundamentals')}
    columns_to_add = [
        sa.Column('sales', sa.Numeric(20, 2), nullable=True),
        sa.Column('pe', sa.Numeric(8, 2), nullable=True),
        sa.Column('dividend_yield', sa.Numeric(6, 2), nullable=True),
        sa.Column('roe_3y', sa.Numeric(6, 2), nullable=True),
        sa.Column('roe_5y', sa.Numeric(6, 2), nullable=True),
        sa.Column('qtr_profit_var_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('qtr_sales_var_pct', sa.Numeric(6, 2), nullable=True),
        sa.Column('pledged_percent', sa.Numeric(6, 2), nullable=True),
        sa.Column('promoter_holding', sa.Numeric(6, 2), nullable=True),
        sa.Column('public_holding', sa.Numeric(6, 2), nullable=True),
    ]

    for column in columns_to_add:
        if column.name not in existing_cols:
            op.add_column('stock_fundamentals', column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'stock_fundamentals' not in inspector.get_table_names():
        return

    existing_cols = {col["name"] for col in inspector.get_columns('stock_fundamentals')}
    columns_to_drop = [
        'public_holding',
        'promoter_holding',
        'pledged_percent',
        'qtr_sales_var_pct',
        'qtr_profit_var_pct',
        'roe_5y',
        'roe_3y',
        'dividend_yield',
        'pe',
        'sales',
    ]

    for col_name in columns_to_drop:
        if col_name in existing_cols:
            op.drop_column('stock_fundamentals', col_name)

