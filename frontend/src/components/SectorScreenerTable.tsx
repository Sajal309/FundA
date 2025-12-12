import { useState, useMemo, useEffect } from 'react';
import { useQuery } from 'react-query';
import { api } from '../api/client';
import { mapRowToUiKeys, UI_COLUMNS } from '../utils/columnMapper';
import DataFreshness from './DataFreshness';

interface SectorScreenerTableProps {
  sectorKey: string;
}

interface ScreenerResponse {
  sector: string;
  label: string;
  columns: Array<{ field: string; label: string; tooltip?: string }>;
  rows: Array<Record<string, any>>;
  count: number;
  primarySort: { field: string; direction: string };
  secondarySort?: { field: string; direction: string };
}

type SortField = string | null;
type SortDirection = 'asc' | 'desc';
type ViewMode = 'sector-wise' | 'regular';
type MarketCapCategory = 'all' | 'large' | 'mid' | 'small';

interface FilterState {
  marketCapCategory?: MarketCapCategory;
  market_cap_min?: number;
  market_cap_max?: number;
  cmp_min?: number;
  cmp_max?: number;
  roe_min?: number;
  roe_max?: number;
  roce_min?: number;
  roce_max?: number;
  pe_min?: number;
  pe_max?: number;
  dividend_yield_min?: number;
  debt_to_equity_max?: number;
  searchText?: string;
}

// Market cap ranges (in Crores)
const MARKET_CAP_RANGES = {
  large: { min: 20000, max: Infinity },
  mid: { min: 5000, max: 20000 },
  small: { min: 0, max: 5000 },
};

function SectorScreenerTable({ sectorKey }: SectorScreenerTableProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('sector-wise');
  const [sortField, setSortField] = useState<SortField>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({});

  // Load last selected sector, sort, and filters from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('lastSelectedSector');
    if (saved && saved !== sectorKey) {
      // Sector changed, reset sort to use ranking (score) by default
      setSortField(null);
      setSortDirection('desc');
      setFilters({});
      // Clear saved sort for old sector
      localStorage.removeItem(`screener-${saved}-sortField`);
      localStorage.removeItem(`screener-${saved}-sortDirection`);
    } else {
      // Load saved sort state (only if user explicitly sorted)
      const savedSortField = localStorage.getItem(`screener-${sectorKey}-sortField`);
      const savedSortDirection = localStorage.getItem(`screener-${sectorKey}-sortDirection`);
      // Only restore if it's not 'score' (we want score to be the default, not saved)
      // Also clear 'score' if it was saved (should use default instead)
      if (savedSortField && savedSortField !== 'score') {
        setSortField(savedSortField);
        if (savedSortDirection) setSortDirection(savedSortDirection as SortDirection);
      } else {
        // Default to ranking (score) - clear any saved 'score' preference
        setSortField(null);
        setSortDirection('desc');
        if (savedSortField === 'score') {
          localStorage.removeItem(`screener-${sectorKey}-sortField`);
          localStorage.removeItem(`screener-${sectorKey}-sortDirection`);
        }
      }

      // Load saved filters
      const savedFilters = localStorage.getItem(`screener-${sectorKey}-filters`);
      if (savedFilters) {
        try {
          setFilters(JSON.parse(savedFilters));
        } catch (e) {
          console.error('Failed to parse saved filters:', e);
        }
      }
    }
    localStorage.setItem('lastSelectedSector', sectorKey);
  }, [sectorKey]);

  const { data, isLoading, error } = useQuery<ScreenerResponse>(
    ['sector-screener', sectorKey],
    () => api.getSectorScreener(sectorKey, 100),
    {
      refetchInterval: 300000, // Refetch every 5 minutes
      onError: (err) => console.error('Screener error:', err),
    }
  );

  // Apply filters and sorting
  const processedRows = useMemo(() => {
    if (!data?.rows) return [];

    // For regular columns view, map to UI keys; for sector-wise, keep original
    let mapped = viewMode === 'regular' 
      ? data.rows.map((row) => mapRowToUiKeys(row))
      : data.rows;

    // Apply filters
    let filtered = mapped.filter((row) => {
      // Search text filter (name or ticker)
      if (filters.searchText) {
        const searchLower = filters.searchText.toLowerCase();
        const nameMatch = row.name?.toLowerCase().includes(searchLower);
        const tickerMatch = row.ticker?.toLowerCase().includes(searchLower);
        if (!nameMatch && !tickerMatch) return false;
      }

      // Market cap category filter
      if (filters.marketCapCategory && filters.marketCapCategory !== 'all') {
        const mcap = row.market_cap || row.marketCap;
        if (!mcap) return false;
        const range = MARKET_CAP_RANGES[filters.marketCapCategory];
        if (mcap < range.min || mcap >= range.max) return false;
      }

      // Market cap min/max filter (only if category is not set or is 'all')
      if (!filters.marketCapCategory || filters.marketCapCategory === 'all') {
        if (filters.market_cap_min !== undefined && filters.market_cap_min > 0) {
          const mcap = row.market_cap || row.marketCap;
          if (!mcap || mcap < filters.market_cap_min) return false;
        }
        if (filters.market_cap_max !== undefined && filters.market_cap_max > 0) {
          const mcap = row.market_cap || row.marketCap;
          if (!mcap || mcap > filters.market_cap_max) return false;
        }
      }

      // CMP filter
      if (filters.cmp_min !== undefined && filters.cmp_min > 0) {
        if (!row.cmp || row.cmp < filters.cmp_min) return false;
      }
      if (filters.cmp_max !== undefined && filters.cmp_max > 0) {
        if (!row.cmp || row.cmp > filters.cmp_max) return false;
      }

      // ROE filter
      if (filters.roe_min !== undefined && filters.roe_min > 0) {
        if (!row.roe || row.roe < filters.roe_min) return false;
      }
      if (filters.roe_max !== undefined && filters.roe_max > 0) {
        if (!row.roe || row.roe > filters.roe_max) return false;
      }

      // ROCE filter
      if (filters.roce_min !== undefined && filters.roce_min > 0) {
        if (!row.roce || row.roce < filters.roce_min) return false;
      }
      if (filters.roce_max !== undefined && filters.roce_max > 0) {
        if (!row.roce || row.roce > filters.roce_max) return false;
      }

      // P/E filter
      if (filters.pe_min !== undefined && filters.pe_min > 0) {
        if (!row.pe || row.pe < filters.pe_min) return false;
      }
      if (filters.pe_max !== undefined && filters.pe_max > 0) {
        if (!row.pe || row.pe > filters.pe_max) return false;
      }

      // Dividend yield filter
      if (filters.dividend_yield_min !== undefined && filters.dividend_yield_min > 0) {
        if (!row.dividend_yield || row.dividend_yield < filters.dividend_yield_min) return false;
      }

      // Debt to equity filter (max only, as lower is usually better)
      if (filters.debt_to_equity_max !== undefined && filters.debt_to_equity_max > 0) {
        if (!row.debt_to_equity || row.debt_to_equity > filters.debt_to_equity_max) return false;
      }

      return true;
    });

    // Check if backend provided ranking (has 'score' field)
    // Check BEFORE filtering to ensure we detect ranking even if some rows are filtered out
    const hasRanking = data.rows && data.rows.length > 0 && (
      'score' in data.rows[0] || 
      data.rows.some(row => row.score !== undefined && row.score !== null) ||
      data.primarySort?.field === 'score'
    );
    
    // Determine sort field and direction
    // If backend provided ranking (score field), default to score unless user explicitly sorted
    let defaultSortField: string;
    if (hasRanking && !sortField) {
      // Backend ranking is active - use score as default
      defaultSortField = 'score';
    } else {
      // Fallback to primarySort or other defaults
      defaultSortField = viewMode === 'regular' 
        ? (data.primarySort?.field || 'roce')
        : (data.primarySort?.field || (data?.columns?.[0]?.field) || 'name');
    }
    
    const currentSortField = sortField || defaultSortField;
    const currentSortDirection = sortField ? sortDirection : (hasRanking && currentSortField === 'score' ? 'desc' : (data.primarySort?.direction === 'asc' ? 'asc' : 'desc'));

    // CRITICAL: If backend provided ranking and user hasn't explicitly sorted, preserve backend order
    // Backend already sorted by score, so we should NOT re-sort
    // When hasRanking is true and sortField is null, defaultSortField will be 'score', so currentSortField will be 'score'
    if (hasRanking && !sortField) {
      // Backend already sorted by score, preserve that order
      // Just ensure rank is set (use backend rank if available, otherwise use index)
      // IMPORTANT: Don't re-sort - backend order is already correct
      return filtered.map((row, idx) => ({
        ...row,
        rank: row.rank !== undefined ? row.rank : idx + 1, // Use backend rank if available
      }));
    }

    // Sort rows (user explicitly sorted or no ranking available)
    filtered.sort((a, b) => {
      const aVal = a[currentSortField];
      const bVal = b[currentSortField];

      // Handle null/undefined
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      // String comparison for name/ticker
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        const comparison = aVal.localeCompare(bVal);
        return currentSortDirection === 'asc' ? comparison : -comparison;
      }

      // Numeric comparison
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return currentSortDirection === 'asc' ? comparison : -comparison;
    });

    // Add rank based on sorted order
    return filtered.map((row, idx) => ({
      ...row,
      rank: row.rank || idx + 1, // Preserve backend rank if available, otherwise use sorted position
    }));
  }, [data?.rows, data?.primarySort, sortField, sortDirection, viewMode, filters]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      // Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      // Default to desc for numeric fields, asc for text fields
      const isNumericField = ['name', 'ticker'].indexOf(field) === -1;
      setSortDirection(isNumericField ? 'desc' : 'asc');
    }
    // Save to localStorage
    localStorage.setItem(`screener-${sectorKey}-sortField`, field);
    localStorage.setItem(`screener-${sectorKey}-sortDirection`, sortField === field ? (sortDirection === 'asc' ? 'desc' : 'asc') : (['name', 'ticker'].indexOf(field) === -1 ? 'desc' : 'asc'));
  };

  const handleFilterChange = (key: keyof FilterState, value: any) => {
    setFilters((prev) => {
      const updated = { ...prev, [key]: value === '' ? undefined : value };
      // Save to localStorage
      localStorage.setItem(`screener-${sectorKey}-filters`, JSON.stringify(updated));
      return updated;
    });
  };

  const clearFilters = () => {
    setFilters({});
    localStorage.removeItem(`screener-${sectorKey}-filters`);
  };

  const hasActiveFilters = () => {
    return Object.entries(filters).some(([key, value]) => {
      if (key === 'marketCapCategory') return value !== undefined && value !== 'all';
      return value !== undefined && value !== '';
    });
  };

  const formatValue = (value: any, field: string): string => {
    if (value == null || value === '') return '-';

    // Rank is always a number
    if (field === 'rank') {
      return String(value);
    }

    // Normalize field name for checking (case-insensitive, remove spaces/special chars)
    const normalizedField = field.toLowerCase().replace(/[\s.%()]/g, '');

    // Format percentages - check both field name and label
    if (
      normalizedField.includes('yield') ||
      normalizedField.includes('var') ||
      normalizedField.includes('roe') ||
      normalizedField.includes('roce') ||
      normalizedField.includes('roa') ||
      normalizedField.includes('holding') ||
      normalizedField.includes('pledged') ||
      normalizedField.includes('nim') ||
      normalizedField.includes('npa') ||
      normalizedField.includes('pcr') ||
      normalizedField.includes('casa') ||
      normalizedField.includes('car') ||
      normalizedField.includes('cagr') ||
      normalizedField.includes('growth') ||
      normalizedField.includes('margin') ||
      normalizedField.includes('ratio') ||
      field.includes('%') ||
      field.includes('Percent')
    ) {
      if (typeof value === 'number') {
        return `${value.toFixed(2)}%`;
      }
      return String(value);
    }

    // Format market cap (convert to Cr if needed)
    if (
      normalizedField.includes('marketcap') ||
      normalizedField.includes('mktcap') ||
      normalizedField === 'market_cap' ||
      normalizedField.includes('freecashflow') ||
      normalizedField === 'free_cash_flow'
    ) {
      if (typeof value === 'number') {
        // If value is very large (likely in Rs), convert to Cr
        if (value >= 10000000) {
          return `${(value / 10000000).toFixed(2)} Cr`;
        }
        // If already in Cr format
        return `${value.toFixed(2)} Cr`;
      }
      return String(value);
    }

    // Format CMP/Price (2 decimal places)
    if (
      normalizedField === 'cmp' ||
      normalizedField.includes('price') ||
      normalizedField.includes('currentprice')
    ) {
      if (typeof value === 'number') {
        return value.toFixed(2);
      }
      return String(value);
    }

    // Format ratios (P/E, Debt/Equity, M.Cap/Sales, D/E)
    if (
      normalizedField === 'pe' ||
      normalizedField.includes('debtequity') ||
      normalizedField === 'debt_to_equity' ||
      normalizedField === 'mcap_to_sales' ||
      normalizedField.includes('de') ||
      normalizedField.includes('solvency')
    ) {
      if (typeof value === 'number') {
        return value.toFixed(2);
      }
      return String(value);
    }

    // Default: return as string
    return String(value);
  };

  const handleExportCSV = () => {
    if (processedRows.length === 0) {
      alert('No data to export');
      return;
    }

    // Determine columns based on view mode
    const columnsToExport = viewMode === 'regular' 
      ? UI_COLUMNS 
      : (data?.columns || []).map(col => ({ field: col.field, label: col.label }));

    // Create CSV header
    const headers = ['Rank', ...columnsToExport.map((col) => col.label)];
    const csvRows = [headers.join(',')];

    // Add data rows
    for (const row of processedRows) {
      const rank = row.rank || '';
      const values = columnsToExport.map((col) => {
        const value = row[col.field];
        if (value == null || value === '') return '';
        
        // Format value for CSV (handle commas in values)
        const formatted = viewMode === 'regular' 
          ? formatValue(value, col.field)
          : formatValue(value, col.label);
        // Escape quotes and wrap in quotes if contains comma
        if (formatted.includes(',') || formatted.includes('"')) {
          return `"${formatted.replace(/"/g, '""')}"`;
        }
        return formatted;
      });
      csvRows.push([rank, ...values].join(','));
    }

    // Create blob and download
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sectorKey}_screener_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-700 p-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-dark-300">Loading screener data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-700 p-6">
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-6 text-center">
          <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Screener</h2>
          <p className="text-dark-300">{String(error)}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-700 p-12">
        <div className="text-center">
          <p className="text-dark-400 text-lg mb-2">No stocks found for this sector.</p>
          <p className="text-sm text-dark-500">
            Try uploading Screener CSV or relax filters.
          </p>
        </div>
      </div>
    );
  }

  // Determine sort field and direction for display (matching logic from processedRows)
  // Check if backend provided ranking - use the same robust check as in processedRows
  const hasScoreFieldForDisplay = data?.rows && data.rows.length > 0 && (
    'score' in data.rows[0] || 
    data.rows.some(row => row.score !== undefined && row.score !== null)
  );
  const hasRankingForDisplay = hasScoreFieldForDisplay || data?.primarySort?.field === 'score';
  
  let defaultSortFieldForDisplay: string;
  if (hasRankingForDisplay && !sortField) {
    defaultSortFieldForDisplay = 'score';
  } else {
    defaultSortFieldForDisplay = viewMode === 'regular' 
      ? (data?.primarySort?.field || 'roce')
      : (data?.primarySort?.field || (data?.columns?.[0]?.field) || 'name');
  }
  
  const currentSortField = sortField || defaultSortFieldForDisplay;
  const currentSortDirection = sortField ? sortDirection : (hasRankingForDisplay && currentSortField === 'score' ? 'desc' : (data?.primarySort?.direction === 'asc' ? 'asc' : 'desc'));

  // Determine which columns to display
  const displayColumns = viewMode === 'regular' 
    ? UI_COLUMNS 
    : (data?.columns || []).map(col => ({ field: col.field, label: col.label, tooltip: col.tooltip }));

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
          <div>
            <h2 className="text-xl font-semibold">
              {data.label} - {processedRows.length} {hasActiveFilters() ? `of ${data.count}` : ''} stocks
            </h2>
            <div className="text-sm text-dark-400 mt-1">
              Sorted by: <span className="text-blue-400 font-medium">
                {currentSortField === 'score' ? 'Ranking Score' : currentSortField}
              </span> ({currentSortDirection === 'asc' ? 'Low to High' : 'High to Low'})
            </div>
            {data.metadata && (
              <div className="mt-2">
                <DataFreshness
                  lastUpdated={data.metadata.last_updated}
                  fetchedAt={data.metadata.fetched_at}
                  isLive={data.metadata.is_live}
                  source="Stock screener"
                  refreshInterval={300000}
                  compact
                />
              </div>
            )}
          </div>
          <button
            onClick={handleExportCSV}
            disabled={processedRows.length === 0}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-dark-600 disabled:text-dark-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <span>📥</span>
            Export CSV
          </button>
        </div>

        {/* View Mode Toggle and Filters */}
        <div className="flex items-center justify-between flex-wrap gap-4 border-t border-dark-700 pt-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-sm text-dark-400 mr-2">View:</span>
              <button
                onClick={() => setViewMode('sector-wise')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'sector-wise'
                    ? 'bg-blue-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                Sector Wise
              </button>
              <button
                onClick={() => setViewMode('regular')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'regular'
                    ? 'bg-blue-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                Regular Columns
              </button>
            </div>
            
            {/* Market Cap Category Filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-dark-400 mr-2">Market Cap:</span>
              {(['all', 'large', 'mid', 'small'] as MarketCapCategory[]).map((category) => (
                <button
                  key={category}
                  onClick={() => handleFilterChange('marketCapCategory', category === filters.marketCapCategory ? undefined : category)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    filters.marketCapCategory === category
                      ? 'bg-green-600 text-white'
                      : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                  }`}
                  title={
                    category === 'all' ? 'All stocks' :
                    category === 'large' ? 'Large Cap (> ₹20,000 Cr)' :
                    category === 'mid' ? 'Mid Cap (₹5,000 - ₹20,000 Cr)' :
                    'Small Cap (< ₹5,000 Cr)'
                  }
                >
                  {category === 'all' ? 'All' : category === 'large' ? 'Large' : category === 'mid' ? 'Mid' : 'Small'}
                  {category !== 'all' && ' Cap'}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasActiveFilters() && (
              <span className="text-xs text-blue-400">
                {processedRows.length} of {data.count} stocks
              </span>
            )}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                showFilters || hasActiveFilters()
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
              }`}
            >
              <span>🔍</span>
              Filters {hasActiveFilters() && `(${Object.keys(filters).filter(k => filters[k as keyof FilterState] !== undefined && filters[k as keyof FilterState] !== '').length})`}
            </button>
            {hasActiveFilters() && (
              <button
                onClick={clearFilters}
                className="px-3 py-2 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="border-t border-dark-700 pt-4 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  Search (Name/Ticker)
                </label>
                <input
                  type="text"
                  value={filters.searchText || ''}
                  onChange={(e) => handleFilterChange('searchText', e.target.value)}
                  placeholder="Search..."
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Market Cap */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  Market Cap (Cr) Min
                  {filters.marketCapCategory && filters.marketCapCategory !== 'all' && (
                    <span className="text-yellow-400 ml-1">(disabled - using category filter)</span>
                  )}
                </label>
                <input
                  type="number"
                  value={filters.market_cap_min || ''}
                  onChange={(e) => handleFilterChange('market_cap_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Min"
                  disabled={filters.marketCapCategory !== undefined && filters.marketCapCategory !== 'all'}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  Market Cap (Cr) Max
                  {filters.marketCapCategory && filters.marketCapCategory !== 'all' && (
                    <span className="text-yellow-400 ml-1">(disabled - using category filter)</span>
                  )}
                </label>
                <input
                  type="number"
                  value={filters.market_cap_max || ''}
                  onChange={(e) => handleFilterChange('market_cap_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Max"
                  disabled={filters.marketCapCategory !== undefined && filters.marketCapCategory !== 'all'}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {/* CMP */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  CMP (Rs) Min
                </label>
                <input
                  type="number"
                  value={filters.cmp_min || ''}
                  onChange={(e) => handleFilterChange('cmp_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  CMP (Rs) Max
                </label>
                <input
                  type="number"
                  value={filters.cmp_max || ''}
                  onChange={(e) => handleFilterChange('cmp_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* ROE */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  ROE % Min
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.roe_min || ''}
                  onChange={(e) => handleFilterChange('roe_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  ROE % Max
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.roe_max || ''}
                  onChange={(e) => handleFilterChange('roe_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* ROCE */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  ROCE % Min
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.roce_min || ''}
                  onChange={(e) => handleFilterChange('roce_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  ROCE % Max
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.roce_max || ''}
                  onChange={(e) => handleFilterChange('roce_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* P/E */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  P/E Min
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.pe_min || ''}
                  onChange={(e) => handleFilterChange('pe_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  P/E Max
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.pe_max || ''}
                  onChange={(e) => handleFilterChange('pe_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Dividend Yield */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  Div Yld % Min
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.dividend_yield_min || ''}
                  onChange={(e) => handleFilterChange('dividend_yield_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Min"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Debt to Equity */}
              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">
                  Debt / Eq Max
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={filters.debt_to_equity_max || ''}
                  onChange={(e) => handleFilterChange('debt_to_equity_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Max"
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-dark-700">
          <thead className="bg-dark-700 sticky top-0 z-10">
            <tr>
              {/* Rank column - always shown */}
              <th className="px-4 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider sticky left-0 bg-dark-700 z-20">
                Rank
              </th>
              {viewMode === 'regular' ? (
                // Regular columns view - ALL columns are sortable
                UI_COLUMNS.filter(col => col.field !== 'rank').map((col) => {
                  const isSorted = currentSortField === col.field;
                  
                  return (
                    <th
                      key={col.field}
                      className={`px-4 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider ${
                        col.field === 'name' ? 'sticky left-12 bg-dark-700 z-20' : ''
                      } cursor-pointer hover:bg-dark-600 transition-colors`}
                      onClick={() => handleSort(col.field)}
                      title={`Click to sort by ${col.label}`}
                    >
                      <div className="flex items-center gap-2">
                        {col.label}
                        {isSorted ? (
                          <span className="text-blue-400 font-bold">
                            {currentSortDirection === 'asc' ? '↑' : '↓'}
                          </span>
                        ) : (
                          <span className="text-dark-500 text-xs">↕</span>
                        )}
                      </div>
                    </th>
                  );
                })
              ) : (
                // Sector-wise columns view - ALL columns are sortable
                displayColumns.map((col) => {
                  const isSorted = currentSortField === col.field;
                  
                  return (
                    <th
                      key={col.field}
                      className={`px-4 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider ${
                        col.field === 'name' ? 'sticky left-12 bg-dark-700 z-20' : ''
                      } cursor-pointer hover:bg-dark-600 transition-colors`}
                      onClick={() => handleSort(col.field)}
                      title={col.tooltip || `Click to sort by ${col.label}`}
                    >
                      <div className="flex items-center gap-2">
                        {col.label}
                        {isSorted ? (
                          <span className="text-blue-400 font-bold">
                            {currentSortDirection === 'asc' ? '↑' : '↓'}
                          </span>
                        ) : (
                          <span className="text-dark-500 text-xs">↕</span>
                        )}
                        {col.tooltip && (
                          <span className="text-dark-500 cursor-help" title={col.tooltip}>
                            ℹ️
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })
              )}
            </tr>
          </thead>
          <tbody className="bg-dark-800 divide-y divide-dark-700">
            {processedRows.length === 0 ? (
              <tr>
                <td colSpan={displayColumns.length + 1} className="px-6 py-12 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-dark-400 text-lg font-medium">No stocks found</p>
                    <p className="text-dark-500 text-sm">
                      {hasActiveFilters() 
                        ? 'Try adjusting your filters or select a different market cap category.'
                        : 'No data available for this sector.'}
                    </p>
                    {hasActiveFilters() && (
                      <button
                        onClick={clearFilters}
                        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                      >
                        Clear All Filters
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              processedRows.map((row, idx) => (
                <tr
                  key={row.ticker || idx}
                  className="hover:bg-dark-700 transition-colors"
                >
                  {/* Rank cell - always shown */}
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-dark-200 sticky left-0 bg-dark-800 z-10">
                    {row.rank || idx + 1}
                  </td>
                  {viewMode === 'regular' ? (
                    // Regular columns view
                    UI_COLUMNS.filter(col => col.field !== 'rank').map((col) => {
                      const value = row[col.field];
                      const formatted = formatValue(value, col.field);
                      
                      return (
                        <td
                          key={col.field}
                          className={`px-4 py-3 whitespace-nowrap text-sm text-dark-300 ${
                            col.field === 'name' ? 'sticky left-12 bg-dark-800 z-10' : ''
                          }`}
                        >
                          {col.field === 'name' && row.url ? (
                            <a
                              href={row.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300 hover:underline"
                            >
                              {formatted}
                            </a>
                          ) : (
                            formatted
                          )}
                        </td>
                      );
                    })
                  ) : (
                    // Sector-wise columns view
                    displayColumns.map((col) => {
                      const value = row[col.field];
                      const formatted = formatValue(value, col.label);
                      
                      return (
                        <td
                          key={col.field}
                          className={`px-4 py-3 whitespace-nowrap text-sm text-dark-300 ${
                            col.field === 'name' ? 'sticky left-12 bg-dark-800 z-10' : ''
                          }`}
                        >
                          {formatted}
                        </td>
                      );
                    })
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default SectorScreenerTable;

