"""Sector screener configurations for backend."""
from typing import Dict, List, Optional, TypedDict
from dataclasses import dataclass

@dataclass
class SortConfig:
    field: str
    direction: str  # "asc" or "desc"

@dataclass
class ColumnConfig:
    field: str
    label: str
    tooltip: Optional[str] = None

@dataclass
class SectorScreenerConfig:
    key: str
    label: str
    filter_query: str  # Human readable for reference
    primary_sort: SortConfig
    secondary_sort: Optional[SortConfig] = None
    columns: List[ColumnConfig] = None
    
    def __post_init__(self):
        if self.columns is None:
            self.columns = []

# Sector name mapping for filtering
SECTOR_NAME_MAP = {
    "banks": ["Banks", "Banking", "NIFTY_BANK"],
    "nbfc": ["NBFC", "HFC", "Non-Banking Financial Company"],
    "insurance": ["Insurance"],
    "it": ["IT", "Information Technology", "NIFTY_IT"],
    "software": ["Software", "SaaS"],
    "fmcg": ["FMCG", "Fast Moving Consumer Goods", "NIFTY_FMCG"],
    "pharma": ["Pharmaceuticals", "Pharma", "NIFTY_PHARMA"],
    "hospitals": ["Hospitals", "Healthcare Services"],
    "diagnostics": ["Diagnostics", "Diagnostic Services"],
    "real_estate": ["Real Estate", "Realty", "NIFTY_REALTY"],
    "cement": ["Cement"],
    "metals": ["Metals", "Mining", "NIFTY_METAL"],
    "capital_goods": ["Capital Goods", "Engineering"],
    "defence": ["Defence", "Defense"],
    "infrastructure": ["Infrastructure", "NIFTY_INFRA"],
    "telecom": ["Telecom", "Telecommunications"],
    "chemicals": ["Chemicals"],
    "agrochemicals": ["Agrochemicals"],
    "auto_oem": ["Automobile", "Auto", "NIFTY_AUTO"],
    "auto_ancillary": ["Auto Ancillary", "Auto Components"],
    "textiles": ["Textiles", "Apparel"],
    "retail": ["Retail"],
    "oil_gas": ["Oil & Gas", "Energy", "NIFTY_ENERGY"],
    "renewables": ["Renewable Energy", "Renewables"],
    "logistics": ["Logistics"],
    "consumer_durables": ["Consumer Durables"],
    "media": ["Media", "Entertainment"],
}

# Field name mapping from config to database
FIELD_MAP = {
    "name": "company_name",
    "ticker": "ticker",
    "marketCap": "market_cap",
    "roa": "roa",
    "roe": "roe",
    "roce": "roce",
    "netInterestMargin": "net_interest_margin",
    "grossNpa": "gross_npa",
    "netNpa": "net_npa",
    "provisionCoverage": "provision_coverage",
    "casaRatio": "casa_ratio",
    "capitalAdequacy": "capital_adequacy",
    "profitGrowth5Y": "profit_growth_5y",
    "aumGrowth5Y": "aum_growth_5y",
    "debtToEquity": "debt_to_equity",
    "solvencyRatio": "solvency_ratio",
    "vnbMargin": "vnb_margin",
    "embeddedValueGrowth5Y": "embedded_value_growth_5y",
    "opexToSales": "opex_to_sales",
    "ebitMargin": "ebit_margin",
    "ebitdaMargin": "ebitda_margin",
    "freeCashFlow": "free_cash_flow",
    "revenueGrowth5Y": "revenue_growth_5y",
    "grossMargin": "gross_margin",
    "operatingMargin": "operating_margin",
    "salesGrowth5Y": "sales_growth_5y",
    "rndToSales": "rnd_to_sales",
    "exportShare": "export_share",
    "bedOccupancy": "bed_occupancy",
    "interestCoverage": "interest_coverage",
    "inventoryDays": "inventory_days",
    "orderBookGrowth3Y": "order_book_growth_3y",
    "orderBookToSales": "order_book_to_sales",
    "orderBookVisibilityYears": "order_book_visibility_years",
    "arpuGrowth": "arpu_growth",
}

SECTOR_SCREENERS: Dict[str, SectorScreenerConfig] = {
    "banks": SectorScreenerConfig(
        key="banks",
        label="Banks",
        filter_query="Sector = 'Banks' AND ROA > 1 AND NIM > 3 AND GNPA < 3 AND NNPA < 1 AND PCR > 70 AND CASA > 35 AND CAR > 15 AND Profit Growth 5Y > 12",
        primary_sort=SortConfig(field="roa", direction="desc"),
        secondary_sort=SortConfig(field="net_interest_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("marketCap", "Mkt Cap (Cr)"),
            ColumnConfig("roa", "ROA %"),
            ColumnConfig("netInterestMargin", "NIM %"),
            ColumnConfig("grossNpa", "GNPA %"),
            ColumnConfig("netNpa", "NNPA %"),
            ColumnConfig("provisionCoverage", "PCR %"),
            ColumnConfig("casaRatio", "CASA %"),
            ColumnConfig("capitalAdequacy", "CAR %"),
            ColumnConfig("profitGrowth5Y", "Profit CAGR 5Y %"),
        ]
    ),
    "nbfc": SectorScreenerConfig(
        key="nbfc",
        label="NBFC / HFC",
        filter_query="Sector = 'NBFC' AND ROA > 1.5 AND ROE > 12 AND GNPA < 3 AND NNPA < 1 AND CAR > 18 AND AUM Growth 5Y > 12 AND D/E < 4",
        primary_sort=SortConfig(field="roa", direction="desc"),
        secondary_sort=SortConfig(field="roe", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("marketCap", "Mkt Cap (Cr)"),
            ColumnConfig("roa", "ROA %"),
            ColumnConfig("roe", "ROE %"),
            ColumnConfig("grossNpa", "GNPA %"),
            ColumnConfig("netNpa", "NNPA %"),
            ColumnConfig("capitalAdequacy", "CAR %"),
            ColumnConfig("aumGrowth5Y", "AUM CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "insurance": SectorScreenerConfig(
        key="insurance",
        label="Insurance",
        filter_query="Sector = 'Insurance' AND Solvency > 1.8 AND EV Growth 5Y > 10 AND VNB Margin > 15 AND Opex % Sales < 25 AND ROE > 12",
        primary_sort=SortConfig(field="vnb_margin", direction="desc"),
        secondary_sort=SortConfig(field="embedded_value_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("marketCap", "Mkt Cap (Cr)"),
            ColumnConfig("solvencyRatio", "Solvency"),
            ColumnConfig("vnbMargin", "VNB Margin %"),
            ColumnConfig("embeddedValueGrowth5Y", "EV CAGR 5Y %"),
            ColumnConfig("opexToSales", "Opex % Sales"),
            ColumnConfig("roe", "ROE %"),
        ]
    ),
    "it": SectorScreenerConfig(
        key="it",
        label="IT Services",
        filter_query="Sector = 'IT' AND EBIT Margin > 18 AND Profit Growth 5Y > 12 AND FCF > 0 AND ROE > 18 AND ROCE > 20 AND D/E < 0.3",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="profit_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("marketCap", "Mkt Cap (Cr)"),
            ColumnConfig("roe", "ROE %"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("ebitMargin", "EBIT Margin %"),
            ColumnConfig("profitGrowth5Y", "Profit CAGR 5Y %"),
            ColumnConfig("freeCashFlow", "FCF (Cr)"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "software": SectorScreenerConfig(
        key="software",
        label="Software / SaaS",
        filter_query="Sector = 'Software' AND Revenue Growth 5Y > 12 AND Gross Margin > 50 AND EBITDA Margin > 18 AND FCF > 0 AND ROE > 15",
        primary_sort=SortConfig(field="revenue_growth_5y", direction="desc"),
        secondary_sort=SortConfig(field="ebitda_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("revenueGrowth5Y", "Rev CAGR 5Y %"),
            ColumnConfig("grossMargin", "Gross Margin %"),
            ColumnConfig("ebitdaMargin", "EBITDA Margin %"),
            ColumnConfig("roe", "ROE %"),
            ColumnConfig("freeCashFlow", "FCF (Cr)"),
        ]
    ),
    "fmcg": SectorScreenerConfig(
        key="fmcg",
        label="FMCG",
        filter_query="Sector = 'FMCG' AND ROE > 20 AND ROCE > 20 AND Operating Margin > 15 AND Sales Growth 5Y > 8 AND D/E < 0.3",
        primary_sort=SortConfig(field="roe", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roe", "ROE %"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "pharma": SectorScreenerConfig(
        key="pharma",
        label="Pharmaceuticals",
        filter_query="Sector = 'Pharmaceuticals' AND ROCE > 15 AND ROE > 15 AND R&D to Sales > 5 AND Sales Growth 5Y > 10 AND D/E < 0.4 AND Export % > 40",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("roe", "ROE %"),
            ColumnConfig("rndToSales", "R&D % Sales"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("exportShare", "Exports %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "hospitals": SectorScreenerConfig(
        key="hospitals",
        label="Hospitals",
        filter_query="Sector = 'Hospitals' AND EBITDA Margin > 18 AND Bed Occupancy > 55 AND ROCE > 15 AND Sales Growth 5Y > 12 AND D/E < 0.5",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="ebitda_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("ebitdaMargin", "EBITDA Margin %"),
            ColumnConfig("bedOccupancy", "Occupancy %"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "diagnostics": SectorScreenerConfig(
        key="diagnostics",
        label="Diagnostics",
        filter_query="Sector = 'Diagnostics' AND ROE > 18 AND Operating Margin > 20 AND Profit Growth 5Y > 12 AND D/E < 0.3",
        primary_sort=SortConfig(field="roe", direction="desc"),
        secondary_sort=SortConfig(field="profit_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roe", "ROE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("profitGrowth5Y", "Profit CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "real_estate": SectorScreenerConfig(
        key="real_estate",
        label="Real Estate",
        filter_query="Sector = 'Real Estate' AND D/E < 1 AND Interest Coverage > 3 AND Inventory Days < 400 AND Sales Growth 5Y > 10 AND ROCE > 12",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("interestCoverage", "Interest Cov."),
            ColumnConfig("inventoryDays", "Inventory Days"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "cement": SectorScreenerConfig(
        key="cement",
        label="Cement",
        filter_query="Sector = 'Cement' AND ROCE > 15 AND Operating Margin > 18 AND D/E < 0.7 AND Sales Growth 5Y > 8 AND Profit Growth 5Y > 10",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="operating_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("profitGrowth5Y", "Profit CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "metals": SectorScreenerConfig(
        key="metals",
        label="Metals & Mining",
        filter_query="Sector = 'Metals' AND ROCE > 18 AND D/E < 0.8 AND Operating Margin > 15 AND Interest Coverage > 3 AND Sales Growth 5Y > 8",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="operating_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("interestCoverage", "Interest Cov."),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "capital_goods": SectorScreenerConfig(
        key="capital_goods",
        label="Capital Goods / Engineering",
        filter_query="Sector = 'Capital Goods' AND Order Book Growth 3Y > 12 AND ROCE > 18 AND Operating Margin > 12 AND D/E < 0.5 AND Sales Growth 5Y > 10",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="order_book_growth_3y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("orderBookGrowth3Y", "Order Book CAGR 3Y %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "defence": SectorScreenerConfig(
        key="defence",
        label="Defence",
        filter_query="Sector = 'Defence' AND ROCE > 20 AND Operating Margin > 15 AND Order Book Visibility > 2Y AND Sales Growth 5Y > 12 AND D/E < 0.4",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("orderBookVisibilityYears", "OB Visibility (Yrs)"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "infrastructure": SectorScreenerConfig(
        key="infrastructure",
        label="Infrastructure",
        filter_query="Sector = 'Infrastructure' AND Order Book to Sales > 2 AND Interest Coverage > 2 AND ROCE > 12 AND D/E < 1 AND Sales Growth 5Y > 10",
        primary_sort=SortConfig(field="order_book_to_sales", direction="desc"),
        secondary_sort=SortConfig(field="roce", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("orderBookToSales", "OB / Sales"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("interestCoverage", "Interest Cov."),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "telecom": SectorScreenerConfig(
        key="telecom",
        label="Telecom",
        filter_query="Sector = 'Telecom' AND ARPU Growth > 5 AND EBITDA Margin > 35 AND ROCE > 12 AND D/E < 2",
        primary_sort=SortConfig(field="arpu_growth", direction="desc"),
        secondary_sort=SortConfig(field="ebitda_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("arpuGrowth", "ARPU Growth %"),
            ColumnConfig("ebitdaMargin", "EBITDA Margin %"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "chemicals": SectorScreenerConfig(
        key="chemicals",
        label="Chemicals",
        filter_query="Sector = 'Chemicals' AND ROCE > 18 AND Operating Margin > 15 AND Sales Growth 5Y > 12 AND Export % > 30 AND D/E < 0.5",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("exportShare", "Exports %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "agrochemicals": SectorScreenerConfig(
        key="agrochemicals",
        label="Agrochemicals",
        filter_query="Sector = 'Agrochemicals' AND ROCE > 20 AND Operating Margin > 18 AND Export % > 40 AND Sales Growth 5Y > 10 AND D/E < 0.4",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="export_share", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("exportShare", "Exports %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "auto_oem": SectorScreenerConfig(
        key="auto_oem",
        label="Auto OEM",
        filter_query="Sector = 'Automobile' AND ROCE > 18 AND Operating Margin > 12 AND Sales Growth 5Y > 10 AND D/E < 0.5",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "auto_ancillary": SectorScreenerConfig(
        key="auto_ancillary",
        label="Auto Ancillaries",
        filter_query="Sector = 'Auto Ancillary' AND ROCE > 18 AND Operating Margin > 12 AND Sales Growth 5Y > 10 AND D/E < 0.5",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "textiles": SectorScreenerConfig(
        key="textiles",
        label="Textiles & Apparel",
        filter_query="Sector = 'Textiles' AND ROCE > 12 AND Operating Margin > 10 AND Export % > 30 AND Sales Growth 5Y > 8 AND D/E < 0.8",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="export_share", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("exportShare", "Exports %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "retail": SectorScreenerConfig(
        key="retail",
        label="Retail",
        filter_query="Sector = 'Retail' AND ROCE > 18 AND Operating Margin > 8 AND Sales Growth 5Y > 15 AND D/E < 0.5",
        primary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        secondary_sort=SortConfig(field="roce", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "oil_gas": SectorScreenerConfig(
        key="oil_gas",
        label="Oil & Gas",
        filter_query="Sector = 'Oil & Gas' AND ROCE > 15 AND Operating Margin > 12 AND Interest Coverage > 3 AND D/E < 0.8",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="operating_margin", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("interestCoverage", "Interest Cov."),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "renewables": SectorScreenerConfig(
        key="renewables",
        label="Renewable Energy",
        filter_query="Sector = 'Renewable Energy' AND ROCE > 10 AND Operating Margin > 20 AND D/E < 2 AND Sales Growth 5Y > 12",
        primary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        secondary_sort=SortConfig(field="roce", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "logistics": SectorScreenerConfig(
        key="logistics",
        label="Logistics",
        filter_query="Sector = 'Logistics' AND ROCE > 15 AND Operating Margin > 12 AND Sales Growth 5Y > 10 AND D/E < 0.7",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "consumer_durables": SectorScreenerConfig(
        key="consumer_durables",
        label="Consumer Durables",
        filter_query="Sector = 'Consumer Durables' AND ROCE > 18 AND Operating Margin > 12 AND Sales Growth 5Y > 10 AND D/E < 0.5",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
    "media": SectorScreenerConfig(
        key="media",
        label="Media & Entertainment",
        filter_query="Sector = 'Media' AND ROCE > 12 AND Operating Margin > 10 AND Sales Growth 5Y > 8 AND D/E < 0.5",
        primary_sort=SortConfig(field="roce", direction="desc"),
        secondary_sort=SortConfig(field="sales_growth_5y", direction="desc"),
        columns=[
            ColumnConfig("name", "Name"),
            ColumnConfig("ticker", "Ticker"),
            ColumnConfig("roce", "ROCE %"),
            ColumnConfig("operatingMargin", "OPM %"),
            ColumnConfig("salesGrowth5Y", "Sales CAGR 5Y %"),
            ColumnConfig("debtToEquity", "D/E"),
        ]
    ),
}

