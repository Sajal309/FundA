"""Sector-wise ranking configuration for stock scoring."""
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field


@dataclass
class MetricWeight:
    """Weight configuration for a metric."""
    key: str
    weight: float


@dataclass
class SectorRankingConfig:
    """Configuration for ranking stocks within a sector."""
    key: str
    label: str
    metrics: Dict[str, List[MetricWeight]] = field(default_factory=dict)
    primary_sort: Optional[Dict[str, str]] = None
    columns: List[Dict[str, str]] = field(default_factory=list)


# Metric keys available for ranking
METRIC_KEYS = [
    "roce", "roe", "opm", "npm", "sales_growth_5y", "profit_growth_5y",
    "debt_to_equity", "pledged_percent", "promoter_holding", "pe", "pb",
    "percent_change_52w", "free_cash_flow", "roe_3y", "roce_3y",
    "qtr_profit_var_pct", "qtr_sales_var_pct", "mcap_to_sales"
]


# Sector ranking configurations
SECTOR_RANKING_CONFIGS: Dict[str, SectorRankingConfig] = {
    "it": SectorRankingConfig(
        key="it",
        label="IT",
        metrics={
            "positive": [
                MetricWeight("roce", 35.0),
                MetricWeight("roe", 20.0),
                MetricWeight("operating_margin", 15.0),
                MetricWeight("profit_growth_5y", 15.0),
                MetricWeight("sales_growth_5y", 10.0),
                MetricWeight("free_cash_flow", 5.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
                MetricWeight("pe", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "roe", "label": "ROE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "pe", "label": "P/E"},
            {"field": "profit_growth_5y", "label": "Profit Growth 5Y %"},
        ]
    ),
    "fmcg": SectorRankingConfig(
        key="fmcg",
        label="FMCG",
        metrics={
            "positive": [
                MetricWeight("roe", 30.0),
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 15.0),
                MetricWeight("sales_growth_5y", 12.0),
                MetricWeight("profit_growth_5y", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
                MetricWeight("pe", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
            {"field": "roe", "label": "ROE %"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "pe", "label": "P/E"},
        ]
    ),
    "pharma": SectorRankingConfig(
        key="pharma",
        label="Pharma",
        metrics={
            "positive": [
                MetricWeight("roce", 25.0),
                MetricWeight("operating_margin", 20.0),
                MetricWeight("profit_growth_5y", 20.0),
                MetricWeight("sales_growth_5y", 15.0),
                MetricWeight("roe", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
                MetricWeight("pe", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "profit_growth_5y", "label": "Profit Growth 5Y %"},
        ]
    ),
    "cement": SectorRankingConfig(
        key="cement",
        label="Cement",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 25.0),
                MetricWeight("profit_growth_5y", 15.0),
                MetricWeight("sales_growth_5y", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
        ]
    ),
    "chemicals": SectorRankingConfig(
        key="chemicals",
        label="Chemicals",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 25.0),
                MetricWeight("sales_growth_5y", 20.0),
                MetricWeight("profit_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
        ]
    ),
    "auto": SectorRankingConfig(
        key="auto",
        label="Auto",
        metrics={
            "positive": [
                MetricWeight("roce", 25.0),
                MetricWeight("roe", 20.0),
                MetricWeight("operating_margin", 15.0),
                MetricWeight("sales_growth_5y", 15.0),
                MetricWeight("profit_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
                MetricWeight("pe", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "roe", "label": "ROE %"},
            {"field": "operating_margin", "label": "OPM %"},
        ]
    ),
    "banks": SectorRankingConfig(
        key="banks",
        label="Banks",
        metrics={
            "positive": [
                MetricWeight("roa", 30.0),
                MetricWeight("net_interest_margin", 20.0),
                MetricWeight("profit_growth_5y", 10.0),
                MetricWeight("capital_adequacy", 8.0),
                MetricWeight("casa_ratio", 7.0),  # casa
            ],
            "negative": [
                MetricWeight("gross_npa", 25.0),  # gnpa
                MetricWeight("net_npa", 20.0),  # nnpa
                MetricWeight("debt_to_equity", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "market_cap", "label": "Mkt Cap (Cr)"},
            {"field": "roa", "label": "ROA %"},
            {"field": "net_interest_margin", "label": "NIM %"},
            {"field": "gross_npa", "label": "GNPA %"},
            {"field": "net_npa", "label": "NNPA %"},
            {"field": "provision_coverage", "label": "PCR %"},
            {"field": "casa_ratio", "label": "CASA %"},
            {"field": "capital_adequacy", "label": "CAR %"},
            {"field": "profit_growth_5y", "label": "Profit CAGR 5Y %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "nbfc": SectorRankingConfig(
        key="nbfc",
        label="NBFC / HFC",
        metrics={
            "positive": [
                MetricWeight("roa", 25.0),
                MetricWeight("roe", 20.0),
                MetricWeight("profit_growth_5y", 15.0),
                MetricWeight("free_cash_flow", 8.0),
            ],
            "negative": [
                MetricWeight("gross_npa", 22.0),
                MetricWeight("debt_to_equity", 25.0),
                MetricWeight("pledged_percent", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "market_cap", "label": "Mkt Cap (Cr)"},
            {"field": "roa", "label": "ROA %"},
            {"field": "roe", "label": "ROE %"},
            {"field": "gross_npa", "label": "GNPA %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "profit_growth_5y", "label": "Profit CAGR 5Y %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "insurance": SectorRankingConfig(
        key="insurance",
        label="Insurance",
        metrics={
            "positive": [
                MetricWeight("roe", 25.0),
                MetricWeight("profit_growth_5y", 20.0),
                MetricWeight("free_cash_flow", 8.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 15.0),
                MetricWeight("pe", 5.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "market_cap", "label": "Mkt Cap (Cr)"},
            {"field": "roe", "label": "ROE %"},
            {"field": "profit_growth_5y", "label": "Profit CAGR 5Y %"},
            {"field": "free_cash_flow", "label": "FCF (Cr)"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "hospitals": SectorRankingConfig(
        key="hospitals",
        label="Hospitals",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("ebitda_margin", 20.0),
                MetricWeight("profit_growth_5y", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "market_cap", "label": "Mkt Cap (Cr)"},
            {"field": "ebitda_margin", "label": "EBITDA Margin %"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "profit_growth_5y", "label": "Profit CAGR 5Y %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "diagnostics": SectorRankingConfig(
        key="diagnostics",
        label="Diagnostics",
        metrics={
            "positive": [
                MetricWeight("roe", 30.0),
                MetricWeight("operating_margin", 25.0),
                MetricWeight("profit_growth_5y", 20.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roe", "label": "ROE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "profit_growth_5y", "label": "Profit CAGR 5Y %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "real_estate": SectorRankingConfig(
        key="real_estate",
        label="Real Estate",
        metrics={
            "positive": [
                MetricWeight("roce", 25.0),
                MetricWeight("profit_growth_5y", 20.0),
                MetricWeight("sales_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 30.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "metals": SectorRankingConfig(
        key="metals",
        label="Metals",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 20.0),
                MetricWeight("sales_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
                MetricWeight("interest_coverage", 10.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "capital_goods": SectorRankingConfig(
        key="capital_goods",
        label="Capital Goods",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 15.0),
                MetricWeight("sales_growth_5y", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "defence": SectorRankingConfig(
        key="defence",
        label="Defence",
        metrics={
            "positive": [
                MetricWeight("roce", 35.0),
                MetricWeight("operating_margin", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "infrastructure": SectorRankingConfig(
        key="infrastructure",
        label="Infrastructure",
        metrics={
            "positive": [
                MetricWeight("roce", 20.0),
                MetricWeight("sales_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
                MetricWeight("interest_coverage", 10.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "interest_coverage", "label": "Interest Cov."},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "telecom": SectorRankingConfig(
        key="telecom",
        label="Telecom",
        metrics={
            "positive": [
                MetricWeight("ebitda_margin", 30.0),
                MetricWeight("roce", 25.0),
                MetricWeight("percent_change_52w", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 35.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "ebitda_margin", "label": "EBITDA Margin %"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "percent_change_52w", "label": "52w %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "agrochemicals": SectorRankingConfig(
        key="agrochemicals",
        label="Agrochemicals",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 25.0),
                MetricWeight("sales_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "renewables": SectorRankingConfig(
        key="renewables",
        label="Renewable Energy",
        metrics={
            "positive": [
                MetricWeight("sales_growth_5y", 30.0),
                MetricWeight("operating_margin", 25.0),
                MetricWeight("roce", 20.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "logistics": SectorRankingConfig(
        key="logistics",
        label="Logistics",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("sales_growth_5y", 20.0),
                MetricWeight("profit_growth_5y", 15.0),
                MetricWeight("operating_margin", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "consumer_durables": SectorRankingConfig(
        key="consumer_durables",
        label="Consumer Durables",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("roe", 20.0),
                MetricWeight("sales_growth_5y", 20.0),
                MetricWeight("operating_margin", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 20.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "roe", "label": "ROE %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "textiles": SectorRankingConfig(
        key="textiles",
        label="Textiles",
        metrics={
            "positive": [
                MetricWeight("roce", 25.0),
                MetricWeight("operating_margin", 15.0),
                MetricWeight("sales_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "retail": SectorRankingConfig(
        key="retail",
        label="Retail",
        metrics={
            "positive": [
                MetricWeight("sales_growth_5y", 35.0),
                MetricWeight("roce", 25.0),
                MetricWeight("operating_margin", 10.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 30.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "oil_gas": SectorRankingConfig(
        key="oil_gas",
        label="Oil & Gas",
        metrics={
            "positive": [
                MetricWeight("roce", 30.0),
                MetricWeight("operating_margin", 20.0),
                MetricWeight("profit_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
                MetricWeight("interest_coverage", 10.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "interest_coverage", "label": "Interest Cov."},
            {"field": "debt_to_equity", "label": "D/E"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
    "media": SectorRankingConfig(
        key="media",
        label="Media",
        metrics={
            "positive": [
                MetricWeight("roce", 25.0),
                MetricWeight("operating_margin", 20.0),
                MetricWeight("sales_growth_5y", 15.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 25.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "company_name", "label": "Name"},
            {"field": "ticker", "label": "Ticker"},
            {"field": "roce", "label": "ROCE %"},
            {"field": "operating_margin", "label": "OPM %"},
            {"field": "sales_growth_5y", "label": "Sales CAGR 5Y %"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    ),
}


def get_default_config() -> SectorRankingConfig:
    """Default fallback sector config."""
    return SectorRankingConfig(
        key="default",
        label="Default",
        metrics={
            "positive": [
                MetricWeight("roce", 40.0),
                MetricWeight("roe", 30.0),
                MetricWeight("profit_growth_5y", 20.0),
            ],
            "negative": [
                MetricWeight("debt_to_equity", 10.0),
            ]
        },
        primary_sort={"field": "score", "direction": "desc"},
        columns=[
            {"field": "ticker", "label": "Ticker"},
            {"field": "company_name", "label": "Company Name"},
            {"field": "score", "label": "Score"},
            {"field": "rank", "label": "Rank"},
        ]
    )


def get_ranking_config(sector_key: str) -> SectorRankingConfig:
    """Get ranking config for a sector, or return default if not found."""
    return SECTOR_RANKING_CONFIGS.get(sector_key.lower(), get_default_config())

