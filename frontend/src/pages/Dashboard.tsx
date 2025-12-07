import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { api, SectorSummary, ForecastResponse } from '../api/client';
import SectorTile from '../components/SectorTile';
import SectorDetail from '../components/SectorDetail';
import CorrelationMatrix from '../components/CorrelationMatrix';
import SectorComparison from '../components/SectorComparison';
import MarketSummary from '../components/MarketSummary';
import SectorStrengthRanking from '../components/SectorStrengthRanking';
import QuarterOutlookRanking from '../components/QuarterOutlookRanking';
import DriverCard from '../components/DriverCard';
import BreadthLeadership from '../components/BreadthLeadership';
import MarketSentiment from '../components/MarketSentiment';
import EarningsWatch from '../components/EarningsWatch';
import MacroIndicators from '../components/MacroIndicators';
import NewsFeed from '../components/NewsFeed';
import VolatilityHeatmap from '../components/VolatilityHeatmap';

function Dashboard() {
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [showDriverCard, setShowDriverCard] = useState(false);
  const [driverCardSector, setDriverCardSector] = useState<string | null>(null);

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

  const { data: driverCardForecast } = useQuery(
    ['forecast', driverCardSector],
    () => api.getSectorForecast(driverCardSector!),
    { enabled: !!driverCardSector && showDriverCard }
  );

  const handleSectorClick = (sectorId: string) => {
    setDriverCardSector(sectorId);
    setShowDriverCard(true);
  };

  if (sectorsLoading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-xl text-dark-100">Loading sectors...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 shadow-sm border-b border-dark-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <h1 className="text-2xl font-bold text-dark-100">SectorView</h1>
              <Link
                to="/sector-rotation"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Sector Rotation
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-dark-600 bg-dark-700 text-dark-100 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        {/* Market Sentiment - Top Row */}
        <section className="mb-8">
          <MarketSentiment />
        </section>

        {/* Market Summary */}
        <section className="mb-8">
          <MarketSummary />
        </section>

        {/* Macro Indicators */}
        <section className="mb-8">
          <MacroIndicators />
        </section>

        {/* Analytics Overview */}
        <section className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CorrelationMatrix lookbackDays={30} />
          {sectors && <SectorComparison sectors={sectors} />}
        </section>

        {/* Quarter Outlook & Sector Strength */}
        <section className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <QuarterOutlookRanking onSectorClick={handleSectorClick} />
          <SectorStrengthRanking lookbackDays={30} />
        </section>

        {/* Breadth & Leadership */}
        <section className="mb-8">
          <BreadthLeadership />
        </section>

        {/* Volatility */}
        <section className="mb-8">
          <VolatilityHeatmap lookbackDays={30} />
        </section>

        {/* Earnings Watch */}
        <section className="mb-8">
          <EarningsWatch />
        </section>

        {/* News Feed */}
        <section className="mb-8">
          <NewsFeed limit={5} />
        </section>

        {/* Sector Performance Grid */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-dark-100">Sector Performance</h2>
            <div className="text-sm text-dark-400">
              {sectors ? `${sectors.length} sectors` : 'Loading...'}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
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
          <h2 className="text-xl font-semibold mb-4 text-dark-100">3-Month Forecasts</h2>
          <div className="bg-dark-800 rounded-lg shadow-lg overflow-hidden border border-dark-700">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-dark-700">
                <thead className="bg-dark-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">
                      Sector
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">
                      Forecast
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">
                      Probability
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-400 uppercase tracking-wider">
                      Expected Return
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-dark-800 divide-y divide-dark-700">
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
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-dark-100">
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
                            UP: {(forecast.prob_up * 100).toFixed(2)}% | NEUTRAL:{' '}
                            {(forecast.prob_neutral * 100).toFixed(2)}% | DOWN:{' '}
                            {(forecast.prob_down * 100).toFixed(2)}%
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

      {/* Driver Card Modal */}
      {showDriverCard && driverCardForecast && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="relative max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <DriverCard 
              forecast={driverCardForecast} 
              onClose={() => {
                setShowDriverCard(false);
                setDriverCardSector(null);
              }} 
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;

