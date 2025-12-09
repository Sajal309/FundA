/**
 * Unit tests for columnMapper utility
 */
import { normalizeHeader, mapRowToUiKeys, getUiFieldKey } from '../columnMapper';

describe('normalizeHeader', () => {
  it('should normalize header strings correctly', () => {
    expect(normalizeHeader('Name')).toBe('name');
    expect(normalizeHeader('Ticker')).toBe('ticker');
    expect(normalizeHeader('CMP Rs.')).toBe('cmprs');
    expect(normalizeHeader('Mar Cap Rs.Cr.')).toBe('marcaprs');
    expect(normalizeHeader('P/E')).toBe('pe');
    expect(normalizeHeader('Div Yld %')).toBe('divyld');
    expect(normalizeHeader('Qtr Profit Var %')).toBe('qtrprofitvar');
    expect(normalizeHeader('ROCE %')).toBe('roce');
    expect(normalizeHeader('Free Cash Flow Rs.Cr.')).toBe('freecashflowrs');
    expect(normalizeHeader('Debt / Eq')).toBe('debteq');
    expect(normalizeHeader('ROE %')).toBe('roe');
    expect(normalizeHeader('ROE 3Yr %')).toBe('roe3yr');
    expect(normalizeHeader('Pledged %')).toBe('pledged');
    expect(normalizeHeader('Prom. Hold. %')).toBe('promhold');
    expect(normalizeHeader('Public Hold %')).toBe('publichold');
    expect(normalizeHeader('M.Cap / Sales')).toBe('mcapsales');
    expect(normalizeHeader('52w %')).toBe('52w');
    expect(normalizeHeader('ROE 5Yr %')).toBe('roe5yr');
  });

  it('should handle case variations', () => {
    expect(normalizeHeader('MARKET CAP')).toBe('marketcap');
    expect(normalizeHeader('market cap')).toBe('marketcap');
    expect(normalizeHeader('Market Cap')).toBe('marketcap');
  });

  it('should handle whitespace and punctuation', () => {
    expect(normalizeHeader('  Name  ')).toBe('name');
    expect(normalizeHeader('P/E (TTM)')).toBe('pettm');
    expect(normalizeHeader('Debt-to-Equity')).toBe('debt-toequity');
  });
});

describe('getUiFieldKey', () => {
  it('should map known headers to UI field keys', () => {
    expect(getUiFieldKey('Name')).toBe('name');
    expect(getUiFieldKey('Ticker')).toBe('ticker');
    expect(getUiFieldKey('CMP Rs.')).toBe('cmp');
    expect(getUiFieldKey('Mar Cap Rs.Cr.')).toBe('market_cap');
    expect(getUiFieldKey('P/E')).toBe('pe');
    expect(getUiFieldKey('Div Yld %')).toBe('dividend_yield');
    expect(getUiFieldKey('Qtr Profit Var %')).toBe('qtr_profit_var_pct');
    expect(getUiFieldKey('ROCE %')).toBe('roce');
    expect(getUiFieldKey('Free Cash Flow Rs.Cr.')).toBe('free_cash_flow');
    expect(getUiFieldKey('Debt / Eq')).toBe('debt_to_equity');
    expect(getUiFieldKey('ROE %')).toBe('roe');
    expect(getUiFieldKey('ROE 3Yr %')).toBe('roe_3y');
    expect(getUiFieldKey('Pledged %')).toBe('pledged_percent');
    expect(getUiFieldKey('Prom. Hold. %')).toBe('promoter_holding');
    expect(getUiFieldKey('Public Hold %')).toBe('public_holding');
    expect(getUiFieldKey('M.Cap / Sales')).toBe('mcap_to_sales');
    expect(getUiFieldKey('52w %')).toBe('percent_change_52w');
    expect(getUiFieldKey('ROE 5Yr %')).toBe('roe_5y');
  });

  it('should return null for unknown headers', () => {
    expect(getUiFieldKey('Unknown Field')).toBe(null);
    expect(getUiFieldKey('Random Column')).toBe(null);
  });
});

describe('mapRowToUiKeys', () => {
  it('should map a row with standard field names', () => {
    const row = {
      name: 'HDFC Bank',
      ticker: 'HDFCBANK',
      'CMP Rs.': 1650.50,
      'Mar Cap Rs.Cr.': 1250000,
      'P/E': 18.5,
      'Div Yld %': 1.2,
      'ROCE %': 15.8,
    };

    const mapped = mapRowToUiKeys(row);
    expect(mapped.name).toBe('HDFC Bank');
    expect(mapped.ticker).toBe('HDFCBANK');
    expect(mapped.cmp).toBe(1650.50);
    expect(mapped.market_cap).toBe(1250000);
    expect(mapped.pe).toBe(18.5);
    expect(mapped.dividend_yield).toBe(1.2);
    expect(mapped.roce).toBe(15.8);
  });

  it('should map a row with alternative field names', () => {
    const row = {
      Name: 'Infosys',
      Symbol: 'INFY',
      Price: 1450.75,
      'Market Capitalization': 600000,
      'Stock P/E': 25.3,
      'Dividend yield': 2.1,
      'Return on capital employed': 28.5,
    };

    const mapped = mapRowToUiKeys(row);
    expect(mapped.name).toBe('Infosys');
    expect(mapped.ticker).toBe('INFY');
    expect(mapped.cmp).toBe(1450.75);
    expect(mapped.market_cap).toBe(600000);
    expect(mapped.pe).toBe(25.3);
    expect(mapped.dividend_yield).toBe(2.1);
    expect(mapped.roce).toBe(28.5);
  });

  it('should handle missing fields gracefully', () => {
    const row = {
      name: 'Test Company',
      ticker: 'TEST',
    };

    const mapped = mapRowToUiKeys(row);
    expect(mapped.name).toBe('Test Company');
    expect(mapped.ticker).toBe('TEST');
    expect(mapped.cmp).toBeUndefined();
    expect(mapped.market_cap).toBeUndefined();
  });

  it('should preserve url field if present', () => {
    const row = {
      name: 'Test Company',
      ticker: 'TEST',
      url: 'https://example.com/stock',
    };

    const mapped = mapRowToUiKeys(row);
    expect(mapped.url).toBe('https://example.com/stock');
  });

  it('should handle mixed case and formatting variations', () => {
    const row = {
      'NAME': 'Company',
      'TICKER': 'TICK',
      'cmp rs.': 100,
      'MAR CAP RS.CR.': 50000,
    };

    const mapped = mapRowToUiKeys(row);
    expect(mapped.name).toBe('Company');
    expect(mapped.ticker).toBe('TICK');
    expect(mapped.cmp).toBe(100);
    expect(mapped.market_cap).toBe(50000);
  });
});

