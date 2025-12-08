import { useState, useMemo } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { SECTOR_SCREENERS, SectorKey } from '../config/sectorScreeners';

interface ScreenerRow {
  [key: string]: any;
}

function StockScreenerPage() {
  const [selectedSector, setSelectedSector] = useState<SectorKey>('banks');
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const config = SECTOR_SCREENERS[selectedSector];

  const { data, isLoading, error } = useQuery(
    ['sector-screener', selectedSector],
    () => api.getSectorScreener(selectedSector, 100),
    {
      refetchInterval: 300000, // Refetch every 5 minutes
      onError: (err) => console.error('Screener error:', err),
    }
  );

  // Client-side sorting
  const sortedRows = useMemo(() => {
    if (!data?.rows) return [];
    
    let sorted = [...data.rows];
    
    if (sortField) {
      sorted.sort((a, b) => {
        const aVal = a[sortField];
        const bVal = b[sortField];
        
        // Handle null/undefined
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        
        // Compare values
        const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }
    
    return sorted;
  }, [data?.rows, sortField, sortDirection]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      // Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const formatValue = (value: any, field: string): string => {
    if (value == null) return '-';
    
    // Format percentages
    if (field.includes('%') || field.includes('Margin') || field.includes('ROE') || 
        field.includes('ROCE') || field.includes('ROA') || field.includes('NPA') ||
        field.includes('CAGR') || field.includes('Growth')) {
      return typeof value === 'number' ? `${value.toFixed(2)}%` : String(value);
    }
    
    // Format market cap (in crores)
    if (field.includes('Cap')) {
      if (typeof value === 'number') {
        if (value >= 100000) return `${(value / 100000).toFixed(2)}L Cr`;
        return `${value.toFixed(2)} Cr`;
      }
    }
    
    // Format ratios
    if (field.includes('D/E') || field.includes('Ratio') || field.includes('Cov.')) {
      return typeof value === 'number' ? value.toFixed(2) : String(value);
    }
    
    // Default: return as string
    return String(value);
  };

  const handleExportCSV = async () => {
    try {
      const blob = await api.exportSectorScreener(selectedSector, 100);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedSector}_screener_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export CSV. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-900 text-dark-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-dark-300">Loading screener data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-dark-900 text-dark-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Screener</h2>
            <p className="text-dark-300">{String(error)}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-900 text-dark-100">
      {/* Header */}
      <header className="bg-dark-800 shadow-sm border-b border-dark-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link to="/" className="text-2xl font-bold text-dark-100 hover:text-blue-400 transition-colors">
                SectorView
              </Link>
              <Link
                to="/"
                className="px-4 py-2 bg-dark-700 text-dark-300 rounded-md hover:bg-dark-600 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                to="/sector-rotation"
                className="px-4 py-2 bg-dark-700 text-dark-300 rounded-md hover:bg-dark-600 transition-colors"
              >
                Sector Rotation
              </Link>
              <Link
                to="/stock-screener"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Stock Screener
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Stock Screener</h1>
          <p className="text-dark-400">Screen stocks by sector using predefined criteria</p>
        </div>

        {/* Sector Selection */}
        <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700 mb-6">
          <div className="mb-4">
            <label htmlFor="sector-select" className="block text-sm font-medium text-dark-300 mb-2">
              Select Sector
            </label>
            <select
              id="sector-select"
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value as SectorKey)}
              className="w-full md:w-64 px-4 py-2 bg-dark-700 border border-dark-600 rounded-md text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              {Object.values(SECTOR_SCREENERS).map((screener) => (
                <option key={screener.key} value={screener.key}>
                  {screener.label}
                </option>
              ))}
            </select>
          </div>
          
          {config && (
            <div className="mt-4 p-4 bg-dark-700 rounded-md">
              <p className="text-sm text-dark-400 mb-2">Screening Criteria:</p>
              <p className="text-xs text-dark-300 whitespace-pre-line">{config.filterQuery.trim()}</p>
            </div>
          )}
        </div>

        {/* Results Table */}
        {data && (
          <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-700 overflow-hidden">
            <div className="p-4 border-b border-dark-700">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <h2 className="text-xl font-semibold">
                    {data.label} - {data.count} stocks found
                  </h2>
                  <div className="text-sm text-dark-400 mt-1">
                    Sorted by: {sortField || data.primarySort.field} ({sortDirection || data.primarySort.direction})
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleExportCSV}
                    disabled={sortedRows.length === 0}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-dark-600 disabled:text-dark-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    <span>📥</span>
                    Export CSV
                  </button>
                </div>
              </div>
            </div>

            {sortedRows.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-dark-400">No stocks match the screening criteria.</p>
                <p className="text-sm text-dark-500 mt-2">
                  Try selecting a different sector or check if fundamentals data is available.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-dark-700">
                  <thead className="bg-dark-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider sticky left-0 bg-dark-700 z-10">
                        Rank
                      </th>
                      {data.columns.map((col) => (
                        <th
                          key={col.field}
                          className="px-4 py-3 text-left text-xs font-medium text-dark-300 uppercase tracking-wider cursor-pointer hover:bg-dark-600 transition-colors"
                          onClick={() => handleSort(col.field)}
                        >
                          <div className="flex items-center gap-2">
                            {col.label}
                            {sortField === col.field && (
                              <span className="text-blue-400">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                            {col.tooltip && (
                              <span
                                className="text-dark-500 cursor-help"
                                title={col.tooltip}
                              >
                                ℹ️
                              </span>
                            )}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-dark-800 divide-y divide-dark-700">
                    {sortedRows.map((row, idx) => (
                      <tr
                        key={row.ticker || idx}
                        className="hover:bg-dark-700 transition-colors"
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-dark-200 sticky left-0 bg-dark-800 z-10">
                          {idx + 1}
                        </td>
                        {data.columns.map((col) => (
                          <td
                            key={col.field}
                            className="px-4 py-3 whitespace-nowrap text-sm text-dark-300"
                          >
                            {formatValue(row[col.field], col.label)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default StockScreenerPage;

