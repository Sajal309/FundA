import { useState, useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import { api, SectorSummary, ForecastResponse } from '../api/client';
import Navigation from '../components/Navigation';
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
import DataFreshness from '../components/DataFreshness';
import HelpIcon from '../components/HelpIcon';

// Sectors to hide in main view and show under "Other Indexes"
const OTHER_INDEXES = new Set([
  'NIFTY_100',
  'NIFTY_200',
  'NIFTY_500',
  'NIFTY_ALPHA_50',
  'NIFTY_COMMODITIES',
  'NIFTY_DIVIDEND_OPPORTUNITIES_50',
  'NIFTY_LOW_VOLATILITY_50',
  'NIFTY_MIDCAP_50',
  'NIFTY_MIDCAP_100',
  'NIFTY_MIDCAP_150',
  'NIFTY_NEXT_50',
  'NIFTY_QUALITY_30',
  'NIFTY_SMALLCAP_50',
  'NIFTY_SMALLCAP_100',
  'NIFTY_SMALLCAP_250',
]);

// OtherIndexesSection component
function OtherIndexesSection({ 
  otherIndexes, 
  forecasts, 
  onSectorClick 
}: { 
  otherIndexes: SectorSummary[];
  forecasts?: ForecastResponse[];
  onSectorClick: (sectorId: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-dark-700 rounded-lg bg-dark-800/50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-dark-700/50 transition-colors rounded-t-lg"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-dark-100">Other Indexes</span>
          <span className="text-sm text-dark-400">({otherIndexes.length} indexes)</span>
        </div>
        <svg
          className={`w-5 h-5 text-dark-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isExpanded && (
        <div className="p-4 border-t border-dark-700">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
            {otherIndexes.map((sector) => {
              const forecast = forecasts?.find((f) => f.sector_id === sector.sector_id);
              return (
                <SectorTile
                  key={sector.sector_id}
                  sector={sector}
                  forecast={forecast}
                  onClick={() => onSectorClick(sector.sector_id)}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function Dashboard() {
  const queryClient = useQueryClient();
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [showDriverCard, setShowDriverCard] = useState(false);
  const [driverCardSector, setDriverCardSector] = useState<string | null>(null);

  const { data: sectorsResponse, isLoading: sectorsLoading, error: sectorsError, dataUpdatedAt } = useQuery(
    'sectors-with-metadata',
    async () => {
      try {
        return await api.getSectorsWithMetadata();
      } catch (error) {
        console.error('Failed to fetch sectors:', error);
        throw error;
      }
    },
    { 
      refetchInterval: 300000, // Refetch every 5 minutes
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch sectors:', error);
      }
    }
  );

  const sectors = sectorsResponse?.data || [];
  const sectorsMetadata = sectorsResponse?.metadata;

  // Separate main sectors from other indexes
  const { mainSectors, otherIndexes } = useMemo(() => {
    if (!Array.isArray(sectors)) {
      return { mainSectors: [], otherIndexes: [] };
    }
    const main: SectorSummary[] = [];
    const other: SectorSummary[] = [];
    
    sectors.forEach((sector) => {
      if (OTHER_INDEXES.has(sector.sector_id)) {
        other.push(sector);
      } else {
        main.push(sector);
      }
    });
    
    return { mainSectors: main, otherIndexes: other };
  }, [sectors]);

  const { data: forecasts, isLoading: forecastsLoading, refetch: refetchForecasts } = useQuery(
    ['forecasts', sectors],
    async () => {
      if (!sectors || !Array.isArray(sectors)) return [];
      const forecastPromises = sectors.map((sector) =>
        api.getSectorForecast(sector.sector_id).catch(() => null)
      );
      const results = await Promise.all(forecastPromises);
      return results.filter((f): f is ForecastResponse => f !== null);
    },
    { 
      enabled: !!sectors && Array.isArray(sectors),
      refetchInterval: 300000, // Refetch every 5 minutes
      staleTime: 60000, // Consider data stale after 1 minute
    }
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

  if (sectorsError) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-400 mb-4">Error loading sectors</div>
          <div className="text-sm text-dark-400">
            {sectorsError instanceof Error ? sectorsError.message : 'Unknown error'}
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Debug logging
  console.log('Dashboard render:', { 
    sectors, 
    isArray: Array.isArray(sectors), 
    length: Array.isArray(sectors) ? sectors.length : 'N/A',
    isLoading: sectorsLoading,
    error: sectorsError 
  });

  if (!sectors || !Array.isArray(sectors) || sectors.length === 0) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-dark-100 mb-4">No sectors data available</div>
          <div className="text-sm text-dark-400">
            {sectorsLoading && 'Loading...'}
            {sectorsError && `Error: ${sectorsError instanceof Error ? sectorsError.message : 'Unknown error'}`}
            {!sectorsLoading && !sectorsError && 'No data returned from API'}
          </div>
          <div className="text-xs text-dark-500 mt-2">
            Debug: sectors={sectors ? (Array.isArray(sectors) ? `${sectors.length} items` : typeof sectors) : 'null/undefined'}
          </div>
        </div>
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
            <div className="flex items-center gap-4">
              {sectorsMetadata && (
                <DataFreshness
                  lastUpdated={sectorsMetadata.last_updated}
                  fetchedAt={sectorsMetadata.fetched_at}
                  isLive={sectorsMetadata.is_live}
                  source="Market data"
                  refreshInterval={300000}
                  compact
                />
              )}
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-dark-600 bg-dark-700 text-dark-100 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => {
                  // Invalidate and refetch all forecast-related queries
                  queryClient.invalidateQueries(['forecasts']);
                  queryClient.invalidateQueries(['quarter-outlook']);
                  queryClient.invalidateQueries(['forecast']);
                  refetchForecasts();
                }}
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
              {mainSectors.length} sectors{otherIndexes.length > 0 ? ` (+ ${otherIndexes.length} other indexes)` : ''}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
            {mainSectors.map((sector) => {
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

          {/* Other Indexes - Collapsible */}
          {otherIndexes.length > 0 && (
            <div className="mt-6">
              <OtherIndexesSection
                otherIndexes={otherIndexes}
                forecasts={forecasts}
                onSectorClick={setSelectedSector}
              />
            </div>
          )}
        </section>

        {/* Forecast Ribbon */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-xl font-semibold text-dark-100">3-Month Forecasts</h2>
            <HelpIcon
              title="3-Month Forecasts"
              content={`This table shows 3-month forward-looking predictions for all sectors.

What it shows:
• Forecast Label: Directional prediction (UP, NEUTRAL, DOWN)
• Probability: Distribution of UP/NEUTRAL/DOWN probabilities
• Expected Return: Projected 3-month return percentage

What to infer:
• UP forecasts with high probability suggest strong momentum ahead
• NEUTRAL forecasts indicate range-bound or uncertain conditions
• DOWN forecasts warn of potential weakness or headwinds
• Compare expected returns across sectors to identify opportunities
• Use probabilities to assess confidence - higher probabilities = more conviction
• Combine with other metrics (breadth, valuation) for confirmation`}
            />
          </div>
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

