import { useQuery } from 'react-query';
import { api, BetaMetrics } from '../api/client';
import { formatPercent, formatNumber } from '../utils/formatting';

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
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Risk Metrics</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Risk Metrics</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

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
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <h3 className="text-lg font-semibold mb-4 text-dark-100">Risk Metrics vs {marketSectorId.replace('NIFTY_', '')}</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="p-4 bg-red-900/20 rounded-lg border border-red-800/50">
          <div className="text-sm text-dark-400 mb-1">Beta</div>
          <div className={`text-2xl font-bold ${getBetaColor(metrics.beta).replace('600', '400')}`}>
            {formatNumber(metrics.beta)}
          </div>
          <div className="text-xs text-dark-400 mt-1">{getBetaLabel(metrics.beta)}</div>
        </div>
        <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-800/50">
          <div className="text-sm text-dark-400 mb-1">Correlation</div>
          <div className="text-2xl font-bold text-blue-400">
            {formatNumber(metrics.correlation_to_market)}
          </div>
          <div className="text-xs text-dark-400 mt-1">
            {Math.abs(metrics.correlation_to_market) > 0.7 ? 'High correlation' : 
             Math.abs(metrics.correlation_to_market) > 0.4 ? 'Moderate' : 'Low correlation'}
          </div>
        </div>
        <div className="p-4 bg-green-900/20 rounded-lg border border-green-800/50">
          <div className="text-sm text-dark-400 mb-1">Alpha</div>
          <div className={`text-2xl font-bold ${metrics.alpha >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.alpha)}
          </div>
          <div className="text-xs text-dark-400 mt-1">Excess return</div>
        </div>
        <div className="p-4 bg-dark-700 rounded-lg border border-dark-600">
          <div className="text-sm text-dark-400 mb-1">Sector Return</div>
          <div className={`text-xl font-bold ${metrics.sector_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.sector_return)}
          </div>
        </div>
        <div className="p-4 bg-dark-700 rounded-lg border border-dark-600">
          <div className="text-sm text-dark-400 mb-1">Market Return</div>
          <div className={`text-xl font-bold ${metrics.market_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.market_return)}
          </div>
        </div>
      </div>
      <div className="mt-4 p-3 bg-dark-700 rounded text-sm text-dark-300">
        <strong className="text-dark-100">Beta Interpretation:</strong> Beta &gt; 1 means the sector moves more than the market. 
        Beta &lt; 1 means it moves less. Beta = 1 means it moves with the market.
      </div>
    </div>
  );
}

export default RiskMetrics;

