import { useState } from 'react';
import { Link } from 'react-router-dom';
import { SECTOR_SCREENERS, SectorKey } from '../config/sectorScreeners';
import SectorScreenerTable from '../components/SectorScreenerTable';

function StockScreenerPage() {
  const [selectedSector, setSelectedSector] = useState<SectorKey>('banks');

  const config = SECTOR_SCREENERS[selectedSector];

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
        <SectorScreenerTable sectorKey={selectedSector} />
      </main>
    </div>
  );
}

export default StockScreenerPage;

