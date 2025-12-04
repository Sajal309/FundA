import { useQuery } from 'react-query';
import { api, BetaMetrics } from '../api/client';

interface RiskMetricsProps {
  sectorId: string;
  marketSectorId?: string;
  lookbackDays?: number;
}

function RiskMetrics({ sectorId, marketSectorId = 'NIFTY_50', lookbackDays = 252 }: RiskMetricsProps) {
  const { data: metrics, isLoading } = useQuery(
    ['risk-metrics', sectorId, marketSectorId, lookbackDays],
    () => api.getBetaAndCorrelation(sectorId, marketSectorId, lookbackDays),
    { enabled: !!sectorId }
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Risk Metrics</h3>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Risk Metrics</h3>
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(2);

  const getBetaColor = (beta: number) => {
    if (beta > 1.2) return 'text-red-600';
    if (beta > 0.8) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getBetaLabel = (beta: number) => {
    if (beta > 1.2) return 'High Volatility';
    if (beta > 0.8) return 'Moderate';
    return 'Low Volatility';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Risk Metrics vs {marketSectorId.replace('NIFTY_', '')}</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
          <div className="text-sm text-gray-600 mb-1">Beta</div>
          <div className={`text-2xl font-bold ${getBetaColor(metrics.beta)}`}>
            {formatNumber(metrics.beta)}
          </div>
          <div className="text-xs text-gray-500 mt-1">{getBetaLabel(metrics.beta)}</div>
        </div>
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm text-gray-600 mb-1">Correlation</div>
          <div className="text-2xl font-bold text-blue-600">
            {formatNumber(metrics.correlation_to_market)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {Math.abs(metrics.correlation_to_market) > 0.7 ? 'High correlation' : 
             Math.abs(metrics.correlation_to_market) > 0.4 ? 'Moderate' : 'Low correlation'}
          </div>
        </div>
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="text-sm text-gray-600 mb-1">Alpha</div>
          <div className={`text-2xl font-bold ${metrics.alpha >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.alpha)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Excess return</div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg border">
          <div className="text-sm text-gray-600 mb-1">Sector Return</div>
          <div className={`text-xl font-bold ${metrics.sector_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.sector_return)}
          </div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg border">
          <div className="text-sm text-gray-600 mb-1">Market Return</div>
          <div className={`text-xl font-bold ${metrics.market_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.market_return)}
          </div>
        </div>
      </div>
      <div className="mt-4 p-3 bg-gray-50 rounded text-sm text-gray-600">
        <strong>Beta Interpretation:</strong> Beta &gt; 1 means the sector moves more than the market. 
        Beta &lt; 1 means it moves less. Beta = 1 means it moves with the market.
      </div>
    </div>
  );
}

export default RiskMetrics;

