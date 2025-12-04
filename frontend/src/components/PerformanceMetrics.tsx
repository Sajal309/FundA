import { useQuery } from 'react-query';
import { api, PerformanceMetrics as PerformanceMetricsType } from '../api/client';

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
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
  const formatNumber = (value: number, decimals: number = 2) => value.toFixed(decimals);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Performance Metrics ({lookbackDays} days)</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Annualized Return</div>
          <div className={`text-lg font-bold ${metrics.annualized_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.annualized_return)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Sharpe Ratio</div>
          <div className={`text-lg font-bold ${metrics.sharpe_ratio >= 1 ? 'text-green-600' : metrics.sharpe_ratio >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
            {formatNumber(metrics.sharpe_ratio)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Max Drawdown</div>
          <div className="text-lg font-bold text-red-600">
            {formatPercent(metrics.max_drawdown)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Win Rate</div>
          <div className={`text-lg font-bold ${metrics.win_rate >= 0.5 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.win_rate)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Volatility</div>
          <div className="text-lg font-bold">
            {formatPercent(metrics.volatility)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Profit Factor</div>
          <div className={`text-lg font-bold ${metrics.profit_factor >= 1 ? 'text-green-600' : 'text-red-600'}`}>
            {formatNumber(metrics.profit_factor)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Total Return</div>
          <div className={`text-lg font-bold ${metrics.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.total_return)}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">RSI (14)</div>
          <div className={`text-lg font-bold ${
            metrics.current_rsi !== null 
              ? (metrics.current_rsi > 70 ? 'text-red-600' : metrics.current_rsi < 30 ? 'text-green-600' : 'text-gray-600')
              : 'text-gray-400'
          }`}>
            {metrics.current_rsi !== null ? formatNumber(metrics.current_rsi, 1) : 'N/A'}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <div className="text-xs text-gray-600 mb-1">Avg Daily Return</div>
          <div className={`text-lg font-bold ${metrics.avg_daily_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercent(metrics.avg_daily_return)}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PerformanceMetrics;

