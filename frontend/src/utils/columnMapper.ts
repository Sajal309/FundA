/**
 * Column mapper utility to normalize incoming field names from various sources
 * (Screener.in CSV, database, etc.) to standardized UI field keys.
 */

/**
 * Normalize a header string by:
 * - Converting to lowercase
 * - Removing spaces, dots, %, and parentheses
 * - Trimming whitespace
 */
export function normalizeHeader(header: string): string {
  return header
    .toLowerCase()
    .replace(/[\s.%()]/g, '')
    .trim();
}

/**
 * Mapping from normalized header variants to UI field keys
 */
const FIELD_MAPPING: Record<string, string> = {
  // Name
  'name': 'name',
  'companyname': 'name',
  'company': 'name',
  
  // Ticker
  'ticker': 'ticker',
  'symbol': 'ticker',
  'code': 'ticker',
  
  // CMP / Price
  'cmprs': 'cmp',
  'price': 'cmp',
  'currentprice': 'cmp',
  'lastprice': 'cmp',
  
  // Market Cap
  'marcaprs': 'market_cap',
  'marketcap': 'market_cap',
  'marketcapitalization': 'market_cap',
  'mcap': 'market_cap',
  
  // P/E
  'pe': 'pe',
  'stockpe': 'pe',
  'priceearnings': 'pe',
  'priceearningsratio': 'pe',
  
  // Dividend Yield
  'divyld': 'dividend_yield',
  'dividendyield': 'dividend_yield',
  'dividend': 'dividend_yield',
  
  // Quarterly Profit Variation
  'qtrprofitvar': 'qtr_profit_var_pct',
  'quarterlyprofitvar': 'qtr_profit_var_pct',
  'qtrprofit': 'qtr_profit_var_pct',
  
  // Quarterly Sales Variation
  'qtrsalesvar': 'qtr_sales_var_pct',
  'quarterlysalesvar': 'qtr_sales_var_pct',
  'qtrsales': 'qtr_sales_var_pct',
  
  // ROCE
  'roce': 'roce',
  'returnoncapitalemployed': 'roce',
  
  // Free Cash Flow
  'freecashflowrs': 'free_cash_flow',
  'freecashflow': 'free_cash_flow',
  'fcf': 'free_cash_flow',
  
  // Debt to Equity
  'debteq': 'debt_to_equity',
  'debttoequity': 'debt_to_equity',
  'de': 'debt_to_equity',
  'd/e': 'debt_to_equity',
  
  // ROE
  'roe': 'roe',
  'returnonequity': 'roe',
  
  // ROE 3Yr
  'roe3yr': 'roe_3y',
  'roe3y': 'roe_3y',
  'roe3year': 'roe_3y',
  
  // Pledged
  'pledged': 'pledged_percent',
  'pledgedpercent': 'pledged_percent',
  
  // Promoter Holding
  'promhold': 'promoter_holding',
  'promoterholding': 'promoter_holding',
  'promholding': 'promoter_holding',
  
  // Public Holding
  'publichold': 'public_holding',
  'publicholding': 'public_holding',
  'publichold': 'public_holding',
  
  // Market Cap to Sales
  'mcapsales': 'mcap_to_sales',
  'mcap/sales': 'mcap_to_sales',
  'mcap2sales': 'mcap_to_sales',
  
  // 52 Week %
  '52w': 'percent_change_52w',
  '52week': 'percent_change_52w',
  '52weekpercent': 'percent_change_52w',
  
  // ROE 5Yr
  'roe5yr': 'roe_5y',
  'roe5y': 'roe_5y',
  'roe5year': 'roe_5y',
};

/**
 * Map a row object to UI field keys using the field mapping.
 * This function examines the keys in the row and maps them to standardized UI keys.
 */
export function mapRowToUiKeys(row: Record<string, any>): Record<string, any> {
  const mapped: Record<string, any> = {};
  
  // First, copy over known direct matches (name, ticker, etc.)
  if (row.name) mapped.name = row.name;
  if (row.ticker) mapped.ticker = row.ticker;
  if (row.url) mapped.url = row.url;
  
  // Map all other fields
  for (const [key, value] of Object.entries(row)) {
    if (key === 'name' || key === 'ticker' || key === 'url') {
      continue; // Already handled
    }
    
    const normalized = normalizeHeader(key);
    const uiKey = FIELD_MAPPING[normalized];
    
    if (uiKey) {
      mapped[uiKey] = value;
    } else {
      // If no mapping found, try direct match (case-insensitive)
      const lowerKey = key.toLowerCase();
      if (FIELD_MAPPING[lowerKey]) {
        mapped[FIELD_MAPPING[lowerKey]] = value;
      } else {
        // Keep original key as fallback
        mapped[key] = value;
      }
    }
  }
  
  return mapped;
}

/**
 * Get UI field key from a normalized header string.
 */
export function getUiFieldKey(header: string): string | null {
  const normalized = normalizeHeader(header);
  return FIELD_MAPPING[normalized] || null;
}

/**
 * UI column definitions in exact order as specified.
 */
export const UI_COLUMNS = [
  { field: 'rank', label: 'Rank', computed: true },
  { field: 'name', label: 'Name', link: true },
  { field: 'ticker', label: 'Ticker' },
  { field: 'cmp', label: 'CMP Rs.' },
  { field: 'market_cap', label: 'Mar Cap Rs.Cr.' },
  { field: 'pe', label: 'P/E' },
  { field: 'dividend_yield', label: 'Div Yld %' },
  { field: 'qtr_profit_var_pct', label: 'Qtr Profit Var %' },
  { field: 'qtr_sales_var_pct', label: 'Qtr Sales Var %' },
  { field: 'roce', label: 'ROCE %' },
  { field: 'free_cash_flow', label: 'Free Cash Flow Rs.Cr.' },
  { field: 'debt_to_equity', label: 'Debt / Eq' },
  { field: 'roe', label: 'ROE %' },
  { field: 'roe_3y', label: 'ROE 3Yr %' },
  { field: 'pledged_percent', label: 'Pledged %' },
  { field: 'promoter_holding', label: 'Prom. Hold. %' },
  { field: 'public_holding', label: 'Public Hold %' },
  { field: 'mcap_to_sales', label: 'M.Cap / Sales' },
  { field: 'percent_change_52w', label: '52w %' },
  { field: 'roe_5y', label: 'ROE 5Yr %' },
] as const;

