import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { api } from '../api/client';
import BreadthTab from '../components/sector-rotation/BreadthTab';
import ScoresTab from '../components/sector-rotation/ScoresTab';
import DeliveriesTab from '../components/sector-rotation/DeliveriesTab';
import VWAPTab from '../components/sector-rotation/VWAPTab';

type PrimaryTab = 'breadth' | 'scores' | 'deliveries' | 'vwap';
type SecondaryTab = 'sector' | 'industry';

function SectorRotationPage() {
  const [primaryTab, setPrimaryTab] = useState<PrimaryTab>('breadth');
  const [secondaryTab, setSecondaryTab] = useState<SecondaryTab>('sector');
  const [selectedDate, setSelectedDate] = useState<string>('');

  // Fetch available dates
  const { data: availableDates } = useQuery(
    ['sector-rotation-dates', secondaryTab],
    () => api.getSectorRotationAvailableDates(secondaryTab),
    {
      onSuccess: (dates) => {
        if (dates.length > 0 && !selectedDate) {
          setSelectedDate(dates[0]); // Set to latest date
        }
      },
    }
  );

  const handleDateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDate(e.target.value);
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 shadow-sm border-b border-dark-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="text-dark-400 hover:text-dark-100 transition-colors"
              >
                ← Back
              </Link>
              <h1 className="text-2xl font-bold text-dark-100">Sector Rotation</h1>
            </div>
            <div className="flex items-center gap-4">
              {availableDates && availableDates.length > 0 && (
                <select
                  value={selectedDate}
                  onChange={handleDateChange}
                  className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-dark-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {availableDates.map((date) => (
                    <option key={date} value={date}>
                      {new Date(date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Primary Tabs */}
        <div className="mb-6 border-b border-dark-700">
          <nav className="flex space-x-8">
            {(['breadth', 'scores', 'deliveries', 'vwap'] as PrimaryTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setPrimaryTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  primaryTab === tab
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-dark-400 hover:text-dark-200 hover:border-dark-600'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        {/* Secondary Tabs */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex space-x-4">
            {(['sector', 'industry'] as SecondaryTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setSecondaryTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  secondaryTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}s
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {selectedDate && (
          <div className="mt-6">
            {primaryTab === 'breadth' && (
              <BreadthTab level={secondaryTab} date={selectedDate} />
            )}
            {primaryTab === 'scores' && (
              <ScoresTab level={secondaryTab} date={selectedDate} />
            )}
            {primaryTab === 'deliveries' && (
              <DeliveriesTab level={secondaryTab} date={selectedDate} />
            )}
            {primaryTab === 'vwap' && (
              <VWAPTab level={secondaryTab} date={selectedDate} />
            )}
          </div>
        )}

        {!selectedDate && availableDates && availableDates.length === 0 && (
          <div className="text-center py-12">
            <p className="text-dark-400">No data available for the selected level.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default SectorRotationPage;

