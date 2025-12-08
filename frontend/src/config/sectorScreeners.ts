export type SectorKey =
  | "banks"
  | "nbfc"
  | "insurance"
  | "it"
  | "software"
  | "fmcg"
  | "pharma"
  | "hospitals"
  | "diagnostics"
  | "real_estate"
  | "cement"
  | "metals"
  | "capital_goods"
  | "defence"
  | "infrastructure"
  | "telecom"
  | "chemicals"
  | "agrochemicals"
  | "auto_oem"
  | "auto_ancillary"
  | "textiles"
  | "retail"
  | "oil_gas"
  | "renewables"
  | "logistics"
  | "consumer_durables"
  | "media";

export interface SectorScreenerConfig {
  key: SectorKey;
  label: string;
  filterQuery: string;        // human readable, for reference / logs
  primarySort: { field: string; direction: "asc" | "desc" };
  secondarySort?: { field: string; direction: "asc" | "desc" };
  columns: { field: string; label: string; tooltip?: string }[];
}

export const SECTOR_SCREENERS: Record<SectorKey, SectorScreenerConfig> = {
  banks: {
    key: "banks",
    label: "Banks",
    filterQuery: `
      Sector = "Banks" AND
      Return on Assets > 1 AND
      Net Interest Margin > 3 AND
      Gross NPA < 3 AND
      Net NPA < 1 AND
      Provision Coverage Ratio > 70 AND
      CASA Ratio > 35 AND
      Capital Adequacy Ratio > 15 AND
      Profit Growth 5Years > 12
    `,
    primarySort: { field: "roa", direction: "desc" },
    secondarySort: { field: "netInterestMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "marketCap", label: "Mkt Cap (Cr)" },
      { field: "roa", label: "ROA %" },
      { field: "netInterestMargin", label: "NIM %" },
      { field: "grossNpa", label: "GNPA %" },
      { field: "netNpa", label: "NNPA %" },
      { field: "provisionCoverage", label: "PCR %" },
      { field: "casaRatio", label: "CASA %" },
      { field: "capitalAdequacy", label: "CAR %" },
      { field: "profitGrowth5Y", label: "Profit CAGR 5Y %" }
    ]
  },
  nbfc: {
    key: "nbfc",
    label: "NBFC / HFC",
    filterQuery: `
      Sector = "NBFC" AND
      ROA > 1.5 AND
      ROE > 12 AND
      Gross NPA < 3 AND
      Net NPA < 1 AND
      Capital Adequacy Ratio > 18 AND
      AUM Growth 5Years > 12 AND
      Debt to Equity < 4
    `,
    primarySort: { field: "roa", direction: "desc" },
    secondarySort: { field: "roe", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "marketCap", label: "Mkt Cap (Cr)" },
      { field: "roa", label: "ROA %" },
      { field: "roe", label: "ROE %" },
      { field: "grossNpa", label: "GNPA %" },
      { field: "netNpa", label: "NNPA %" },
      { field: "capitalAdequacy", label: "CAR %" },
      { field: "aumGrowth5Y", label: "AUM CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  insurance: {
    key: "insurance",
    label: "Insurance",
    filterQuery: `
      Sector = "Insurance" AND
      Solvency Ratio > 1.8 AND
      Embedded Value Growth 5Years > 10 AND
      VNB Margin > 15 AND
      Operating Expense Ratio < 25 AND
      Return on Equity > 12
    `,
    primarySort: { field: "vnbMargin", direction: "desc" },
    secondarySort: { field: "embeddedValueGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "marketCap", label: "Mkt Cap (Cr)" },
      { field: "solvencyRatio", label: "Solvency" },
      { field: "vnbMargin", label: "VNB Margin %" },
      { field: "embeddedValueGrowth5Y", label: "EV CAGR 5Y %" },
      { field: "opexToSales", label: "Opex % Sales" },
      { field: "roe", label: "ROE %" }
    ]
  },
  it: {
    key: "it",
    label: "IT Services",
    filterQuery: `
      Sector = "IT" AND
      EBIT Margin > 18 AND
      Profit Growth 5Years > 12 AND
      Free Cash Flow Rs.Cr. > 0 AND
      Return on Equity > 18 AND
      Return on Capital Employed > 20 AND
      Debt to Equity < 0.3
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "profitGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "marketCap", label: "Mkt Cap (Cr)" },
      { field: "roe", label: "ROE %" },
      { field: "roce", label: "ROCE %" },
      { field: "ebitMargin", label: "EBIT Margin %" },
      { field: "profitGrowth5Y", label: "Profit CAGR 5Y %" },
      { field: "freeCashFlow", label: "FCF (Cr)" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  software: {
    key: "software",
    label: "Software / SaaS",
    filterQuery: `
      Sector = "Software" AND
      Revenue Growth 5Years > 12 AND
      Gross Margin > 50 AND
      EBITDA Margin > 18 AND
      Free Cash Flow Rs.Cr. > 0 AND
      ROE > 15
    `,
    primarySort: { field: "revenueGrowth5Y", direction: "desc" },
    secondarySort: { field: "ebitdaMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "revenueGrowth5Y", label: "Rev CAGR 5Y %" },
      { field: "grossMargin", label: "Gross Margin %" },
      { field: "ebitdaMargin", label: "EBITDA Margin %" },
      { field: "roe", label: "ROE %" },
      { field: "freeCashFlow", label: "FCF (Cr)" }
    ]
  },
  fmcg: {
    key: "fmcg",
    label: "FMCG",
    filterQuery: `
      Sector = "FMCG" AND
      ROE > 20 AND
      ROCE > 20 AND
      Operating Margin > 15 AND
      Sales Growth 5Years > 8 AND
      Debt to Equity < 0.3
    `,
    primarySort: { field: "roe", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roe", label: "ROE %" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  pharma: {
    key: "pharma",
    label: "Pharmaceuticals",
    filterQuery: `
      Sector = "Pharmaceuticals" AND
      ROCE > 15 AND
      ROE > 15 AND
      R&D to Sales > 5 AND
      Sales Growth 5Years > 10 AND
      Debt to Equity < 0.4 AND
      Export Revenue % > 40
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "roe", label: "ROE %" },
      { field: "rndToSales", label: "R&D % Sales" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "exportShare", label: "Exports %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  hospitals: {
    key: "hospitals",
    label: "Hospitals",
    filterQuery: `
      Sector = "Hospitals" AND
      EBITDA Margin > 18 AND
      Bed Occupancy > 55 AND
      ROCE > 15 AND
      Sales Growth 5Years > 12 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "ebitdaMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "ebitdaMargin", label: "EBITDA Margin %" },
      { field: "bedOccupancy", label: "Occupancy %" },
      { field: "roce", label: "ROCE %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  diagnostics: {
    key: "diagnostics",
    label: "Diagnostics",
    filterQuery: `
      Sector = "Diagnostics" AND
      ROE > 18 AND
      Operating Margin > 20 AND
      Profit Growth 5Years > 12 AND
      Debt to Equity < 0.3
    `,
    primarySort: { field: "roe", direction: "desc" },
    secondarySort: { field: "profitGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roe", label: "ROE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "profitGrowth5Y", label: "Profit CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  real_estate: {
    key: "real_estate",
    label: "Real Estate",
    filterQuery: `
      Sector = "Real Estate" AND
      Debt to Equity < 1 AND
      Interest Coverage > 3 AND
      Inventory Days < 400 AND
      Sales Growth 5Years > 10 AND
      ROCE > 12
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "interestCoverage", label: "Interest Cov." },
      { field: "inventoryDays", label: "Inventory Days" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  cement: {
    key: "cement",
    label: "Cement",
    filterQuery: `
      Sector = "Cement" AND
      ROCE > 15 AND
      Operating Margin > 18 AND
      Debt to Equity < 0.7 AND
      Sales Growth 5Years > 8 AND
      Profit Growth 5Years > 10
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "operatingMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "profitGrowth5Y", label: "Profit CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  metals: {
    key: "metals",
    label: "Metals & Mining",
    filterQuery: `
      Sector = "Metals" AND
      ROCE > 18 AND
      Debt to Equity < 0.8 AND
      Operating Margin > 15 AND
      Interest Coverage > 3 AND
      Sales Growth 5Years > 8
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "operatingMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "interestCoverage", label: "Interest Cov." },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  capital_goods: {
    key: "capital_goods",
    label: "Capital Goods / Engineering",
    filterQuery: `
      Sector = "Capital Goods" AND
      Order Book Growth 3Years > 12 AND
      ROCE > 18 AND
      Operating Margin > 12 AND
      Debt to Equity < 0.5 AND
      Sales Growth 5Years > 10
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "orderBookGrowth3Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "orderBookGrowth3Y", label: "Order Book CAGR 3Y %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  defence: {
    key: "defence",
    label: "Defence",
    filterQuery: `
      Sector = "Defence" AND
      ROCE > 20 AND
      Operating Margin > 15 AND
      Order Book Visibility > 2Years AND
      Sales Growth 5Years > 12 AND
      Debt to Equity < 0.4
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "orderBookVisibilityYears", label: "OB Visibility (Yrs)" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  infrastructure: {
    key: "infrastructure",
    label: "Infrastructure",
    filterQuery: `
      Sector = "Infrastructure" AND
      Order Book to Sales > 2 AND
      Interest Coverage > 2 AND
      ROCE > 12 AND
      Debt to Equity < 1 AND
      Sales Growth 5Years > 10
    `,
    primarySort: { field: "orderBookToSales", direction: "desc" },
    secondarySort: { field: "roce", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "orderBookToSales", label: "OB / Sales" },
      { field: "roce", label: "ROCE %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "interestCoverage", label: "Interest Cov." },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  telecom: {
    key: "telecom",
    label: "Telecom",
    filterQuery: `
      Sector = "Telecom" AND
      ARPU Growth > 5 AND
      EBITDA Margin > 35 AND
      ROCE > 12 AND
      Debt to Equity < 2
    `,
    primarySort: { field: "arpuGrowth", direction: "desc" },
    secondarySort: { field: "ebitdaMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "arpuGrowth", label: "ARPU Growth %" },
      { field: "ebitdaMargin", label: "EBITDA Margin %" },
      { field: "roce", label: "ROCE %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  chemicals: {
    key: "chemicals",
    label: "Chemicals",
    filterQuery: `
      Sector = "Chemicals" AND
      ROCE > 18 AND
      Operating Margin > 15 AND
      Sales Growth 5Years > 12 AND
      Export % > 30 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "exportShare", label: "Exports %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  agrochemicals: {
    key: "agrochemicals",
    label: "Agrochemicals",
    filterQuery: `
      Sector = "Agrochemicals" AND
      ROCE > 20 AND
      Operating Margin > 18 AND
      Export % > 40 AND
      Sales Growth 5Years > 10 AND
      Debt to Equity < 0.4
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "exportShare", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "exportShare", label: "Exports %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  auto_oem: {
    key: "auto_oem",
    label: "Auto OEM",
    filterQuery: `
      Sector = "Automobile" AND
      ROCE > 18 AND
      Operating Margin > 12 AND
      Sales Growth 5Years > 10 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  auto_ancillary: {
    key: "auto_ancillary",
    label: "Auto Ancillaries",
    filterQuery: `
      Sector = "Auto Ancillary" AND
      ROCE > 18 AND
      Operating Margin > 12 AND
      Sales Growth 5Years > 10 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  textiles: {
    key: "textiles",
    label: "Textiles & Apparel",
    filterQuery: `
      Sector = "Textiles" AND
      ROCE > 12 AND
      Operating Margin > 10 AND
      Export % > 30 AND
      Sales Growth 5Years > 8 AND
      Debt to Equity < 0.8
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "exportShare", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "exportShare", label: "Exports %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  retail: {
    key: "retail",
    label: "Retail",
    filterQuery: `
      Sector = "Retail" AND
      ROCE > 18 AND
      Operating Margin > 8 AND
      Sales Growth 5Years > 15 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "salesGrowth5Y", direction: "desc" },
    secondarySort: { field: "roce", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  oil_gas: {
    key: "oil_gas",
    label: "Oil & Gas",
    filterQuery: `
      Sector = "Oil & Gas" AND
      ROCE > 15 AND
      Operating Margin > 12 AND
      Interest Coverage > 3 AND
      Debt to Equity < 0.8
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "operatingMargin", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "interestCoverage", label: "Interest Cov." },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  renewables: {
    key: "renewables",
    label: "Renewable Energy",
    filterQuery: `
      Sector = "Renewable Energy" AND
      ROCE > 10 AND
      Operating Margin > 20 AND
      Debt to Equity < 2 AND
      Sales Growth 5Years > 12
    `,
    primarySort: { field: "salesGrowth5Y", direction: "desc" },
    secondarySort: { field: "roce", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  logistics: {
    key: "logistics",
    label: "Logistics",
    filterQuery: `
      Sector = "Logistics" AND
      ROCE > 15 AND
      Operating Margin > 12 AND
      Sales Growth 5Years > 10 AND
      Debt to Equity < 0.7
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  consumer_durables: {
    key: "consumer_durables",
    label: "Consumer Durables",
    filterQuery: `
      Sector = "Consumer Durables" AND
      ROCE > 18 AND
      Operating Margin > 12 AND
      Sales Growth 5Years > 10 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  },
  media: {
    key: "media",
    label: "Media & Entertainment",
    filterQuery: `
      Sector = "Media" AND
      ROCE > 12 AND
      Operating Margin > 10 AND
      Sales Growth 5Years > 8 AND
      Debt to Equity < 0.5
    `,
    primarySort: { field: "roce", direction: "desc" },
    secondarySort: { field: "salesGrowth5Y", direction: "desc" },
    columns: [
      { field: "name", label: "Name" },
      { field: "ticker", label: "Ticker" },
      { field: "roce", label: "ROCE %" },
      { field: "operatingMargin", label: "OPM %" },
      { field: "salesGrowth5Y", label: "Sales CAGR 5Y %" },
      { field: "debtToEquity", label: "D/E" }
    ]
  }
};

