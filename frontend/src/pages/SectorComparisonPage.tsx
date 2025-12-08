import { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { SECTOR_SCREENERS, SectorKey } from '../config/sectorScreeners';

function SectorComparisonPage() {
  const [selectedSectors, setSelectedSectors] = useState<SectorKey[]>(['banks', 'it', 'pharma']);
  const [limit] = useState(50);

  const { data, isLoading, error } = useQuery(
    ['sector-comparison', selectedSectors.join(','), limit],
    () => api.compareSectorScreeners(selectedSectors, limit),
    {
      enabled: selectedSectors.length > 0 && selectedSectors.length <= 5,
      refetchInterval: 300000,
    }
  );

  const handleSectorToggle = (sector: SectorKey) => {
    if (selectedSectors.includes(sector)) {
      setSelectedSectors(selectedSectors.filter(s => s !== sector));
    } else {
      if (selectedSectors.length < 5) {
        setSelectedSectors([...selectedSectors, sector]);
      } else {
        alert('Maximum 5 sectors can be compared at once');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-900 text-dark-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-dark-300">Loading comparison data...</p>
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
            <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Comparison</h2>
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
                className="px-4 py-2 bg-dark-700 text-dark-300 rounded-md hover:bg-dark-600 transition-colors"
              >
                Stock Screener
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Sector Screener Comparison</h1>
          <p className="text-dark-400">Compare top stocks across multiple sectors</p>
        </div>

        {/* Sector Selection */}
        <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700 mb-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Select Sectors to Compare (max 5)
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.values(SECTOR_SCREENERS).map((screener) => (
                <button
                  key={screener.key}
                  onClick={() => handleSectorToggle(screener.key as SectorKey)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedSectors.includes(screener.key as SectorKey)
                      ? 'bg-blue-600 text-white'
                      : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                  }`}
                >
                  {screener.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Comparison Results */}
        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.entries(data.sectors).map(([sectorKey, sectorData]) => (
              <div
                key={sectorKey}
                className="bg-dark-800 rounded-lg shadow-lg border border-dark-700 overflow-hidden"
              >
                <div className="p-4 border-b border-dark-700 bg-dark-700">
                  <h3 className="text-lg font-semibold">{sectorData.label}</h3>
                  <p className="text-sm text-dark-400">
                    {sectorData.count} stocks found
                    {sectorData.primary_sort_field && (
                      <span className="ml-2">• Sorted by {sectorData.primary_sort_field}</span>
                    )}
                  </p>
                </div>

                {sectorData.error ? (
                  <div className="p-4 text-center text-red-400">
                    <p className="text-sm">{sectorData.error}</p>
                  </div>
                ) : sectorData.top_5 && sectorData.top_5.length > 0 ? (
                  <div className="p-4">
                    <h4 className="text-sm font-medium text-dark-300 mb-3">Top 5 Stocks</h4>
                    <div className="space-y-2">
                      {sectorData.top_5.map((stock, idx) => (
                        <div
                          key={stock.ticker || idx}
                          className="flex items-center justify-between p-2 bg-dark-700 rounded hover:bg-dark-600 transition-colors"
                        >
                          <div className="flex-1">
                            <div className="font-medium text-dark-100">{stock.name || stock.ticker}</div>
                            <div className="text-xs text-dark-400">{stock.ticker}</div>
                          </div>
                          <div className="text-sm text-dark-300">
                            {stock[sectorData.primary_sort_field] != null
                              ? typeof stock[sectorData.primary_sort_field] === 'number'
                                ? `${stock[sectorData.primary_sort_field].toFixed(2)}%`
                                : String(stock[sectorData.primary_sort_field])
                              : '-'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 text-center text-dark-400">
                    <p className="text-sm">No stocks found</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {data && Object.keys(data.sectors).length === 0 && (
          <div className="bg-dark-800 rounded-lg shadow-lg p-12 text-center border border-dark-700">
            <p className="text-dark-400">Select sectors to compare</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default SectorComparisonPage;

