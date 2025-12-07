import { useQuery } from 'react-query';
import { api, PerformanceMetrics as PerformanceMetricsType } from '../api/client';
import { formatPercent, formatNumber } from '../utils/formatting';

interface PerformanceMetricsProps {
  sectorId: string;
  lookbackDays?: number;
}

function PerformanceMetrics({ sectorId, lookbackDays = 252 }: PerformanceMetricsProps) {
  const { data: metrics, isLoading } = useQuery(
    ['performance-metrics', sectorId, lookbackDays],
    () => api.getPerformanceMetrics(sectorId, lookbackDays),
    { enabled: !!sectorId }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Performance Metrics</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Performance Metrics</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <h3 className="text-lg font-semibold mb-4 text-dark-100">Performance Metrics ({lookbackDays} days)</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Annualized Return</div>
          <div className={`text-lg font-bold ${metrics.annualized_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.annualized_return)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Sharpe Ratio</div>
          <div className={`text-lg font-bold ${metrics.sharpe_ratio >= 1 ? 'text-green-400' : metrics.sharpe_ratio >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
            {formatNumber(metrics.sharpe_ratio)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Max Drawdown</div>
          <div className="text-lg font-bold text-red-400">
            {formatPercent(metrics.max_drawdown)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Win Rate</div>
          <div className={`text-lg font-bold ${metrics.win_rate >= 0.5 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.win_rate)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Volatility</div>
          <div className="text-lg font-bold text-dark-300">
            {formatPercent(metrics.volatility)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Profit Factor</div>
          <div className={`text-lg font-bold ${metrics.profit_factor >= 1 ? 'text-green-400' : 'text-red-400'}`}>
            {formatNumber(metrics.profit_factor)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Total Return</div>
          <div className={`text-lg font-bold ${metrics.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.total_return)}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">RSI (14)</div>
          <div className={`text-lg font-bold ${
            metrics.current_rsi !== null 
              ? (metrics.current_rsi > 70 ? 'text-red-400' : metrics.current_rsi < 30 ? 'text-green-400' : 'text-dark-300')
              : 'text-dark-500'
          }`}>
            {metrics.current_rsi !== null ? formatNumber(metrics.current_rsi, 2) : 'N/A'}
          </div>
        </div>
        <div className="p-3 bg-dark-700 rounded">
          <div className="text-xs text-dark-400 mb-1">Avg Daily Return</div>
          <div className={`text-lg font-bold ${metrics.avg_daily_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(metrics.avg_daily_return)}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PerformanceMetrics;

