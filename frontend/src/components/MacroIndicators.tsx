import { useQuery } from 'react-query';
import { api } from '../api/client';

function MacroIndicators() {
  const { data: macro, isLoading, error } = useQuery(
    'macro-summary',
    () => api.getMacroSummary(30),
    { 
      refetchInterval: 300000,
      retry: 2,
      onError: (err) => console.error('Macro indicators error:', err)
    }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Macro Indicators</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Macro Indicators</h3>
        <div className="text-red-400">Error loading data: {String(error)}</div>
      </div>
    );
  }

  if (!macro || Object.keys(macro).length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Macro Indicators</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

  const formatChange = (value: number | null) => {
    if (value === null) return 'N/A';
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getChangeColor = (value: number | null) => {
    if (value === null) return 'text-dark-500';
    return value >= 0 ? 'text-green-400' : 'text-red-400';
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <h3 className="text-lg font-semibold mb-4 text-dark-100">Macro Indicators</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* USD/INR */}
        <div className="p-4 bg-blue-900/10 rounded-lg border border-blue-600/30">
          <div className="text-sm text-dark-400 mb-1">USD/INR</div>
          <div className="text-xl font-bold text-dark-100">
            {macro.usd_inr ? `₹${macro.usd_inr.toFixed(2)}` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.usd_inr_change_pct)}`}>
            {formatChange(macro.usd_inr_change_pct)}
          </div>
        </div>

        {/* Brent Crude */}
        <div className="p-4 bg-orange-900/10 rounded-lg border border-orange-600/30">
          <div className="text-sm text-dark-400 mb-1">Brent Crude</div>
          <div className="text-xl font-bold text-dark-100">
            {macro.brent_crude ? `$${macro.brent_crude.toFixed(2)}` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.brent_change_pct)}`}>
            {formatChange(macro.brent_change_pct)}
          </div>
        </div>

        {/* Gold */}
        <div className="p-4 bg-yellow-900/10 rounded-lg border border-yellow-600/30">
          <div className="text-sm text-dark-400 mb-1">Gold</div>
          <div className="text-xl font-bold text-dark-100">
            {macro.gold_price ? `$${macro.gold_price.toFixed(2)}` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.gold_change_pct)}`}>
            {formatChange(macro.gold_change_pct)}
          </div>
        </div>

        {/* US 10Y Yield */}
        <div className="p-4 bg-purple-900/10 rounded-lg border border-purple-600/30">
          <div className="text-sm text-dark-400 mb-1">US 10Y Yield</div>
          <div className="text-xl font-bold text-dark-100">
            {macro.us_10y_yield ? `${macro.us_10y_yield.toFixed(2)}%` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.us_10y_change)}`}>
            {macro.us_10y_change !== null ? `${macro.us_10y_change >= 0 ? '+' : ''}${macro.us_10y_change.toFixed(2)}%` : 'N/A'}
          </div>
        </div>
      </div>
      {macro.date && (
        <div className="mt-4 text-xs text-dark-500 text-center">
          Last updated: {new Date(macro.date).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

export default MacroIndicators;

