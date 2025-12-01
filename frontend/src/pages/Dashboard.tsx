import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { api, SectorSummary, ForecastResponse } from '../api/client';
import SectorTile from '../components/SectorTile';
import SectorDetail from '../components/SectorDetail';

function Dashboard() {
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );

  const { data: sectors, isLoading: sectorsLoading } = useQuery(
    'sectors',
    api.getSectors,
    { refetchInterval: 300000 } // Refetch every 5 minutes
  );

  const { data: forecasts, isLoading: forecastsLoading } = useQuery(
    ['forecasts', sectors],
    async () => {
      if (!sectors) return [];
      const forecastPromises = sectors.map((sector) =>
        api.getSectorForecast(sector.sector_id).catch(() => null)
      );
      const results = await Promise.all(forecastPromises);
      return results.filter((f): f is ForecastResponse => f !== null);
    },
    { enabled: !!sectors }
  );

  if (sectorsLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading sectors...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">SectorView</h1>
            <div className="flex items-center gap-4">
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Sector Heatmap */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Sector Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sectors?.map((sector) => {
              const forecast = forecasts?.find((f) => f.sector_id === sector.sector_id);
              return (
                <SectorTile
                  key={sector.sector_id}
                  sector={sector}
                  forecast={forecast}
                  onClick={() => setSelectedSector(sector.sector_id)}
                />
              );
            })}
          </div>
        </section>

        {/* Forecast Ribbon */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">3-Month Forecasts</h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sector
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Forecast
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Probability
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expected Return
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {forecastsLoading ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-4 text-center">
                        Loading forecasts...
                      </td>
                    </tr>
                  ) : (
                    forecasts?.map((forecast) => {
                      const sector = sectors?.find((s) => s.sector_id === forecast.sector_id);
                      const labelColors = {
                        UP: 'text-green-600 bg-green-50',
                        NEUTRAL: 'text-yellow-600 bg-yellow-50',
                        DOWN: 'text-red-600 bg-red-50',
                      };
                      const arrow = {
                        UP: '↑',
                        NEUTRAL: '→',
                        DOWN: '↓',
                      };
                      return (
                        <tr key={forecast.sector_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {sector?.name || forecast.sector_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                labelColors[forecast.forecast_3m_label as keyof typeof labelColors] || labelColors.NEUTRAL
                              }`}
                            >
                              {arrow[forecast.forecast_3m_label as keyof typeof arrow] || '→'}{' '}
                              {forecast.forecast_3m_label}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            UP: {(forecast.prob_up * 100).toFixed(0)}% | NEUTRAL:{' '}
                            {(forecast.prob_neutral * 100).toFixed(0)}% | DOWN:{' '}
                            {(forecast.prob_down * 100).toFixed(0)}%
                          </td>
                          <td
                            className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                              forecast.expected_return_pct >= 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {forecast.expected_return_pct >= 0 ? '+' : ''}
                            {forecast.expected_return_pct.toFixed(2)}%
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>

      {/* Sector Detail Modal */}
      {selectedSector && (
        <SectorDetail
          sectorId={selectedSector}
          onClose={() => setSelectedSector(null)}
        />
      )}
    </div>
  );
}

export default Dashboard;

