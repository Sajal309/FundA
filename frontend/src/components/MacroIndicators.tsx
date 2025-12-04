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
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Macro Indicators</h3>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Macro Indicators</h3>
        <div className="text-red-500">Error loading data: {String(error)}</div>
      </div>
    );
  }

  if (!macro || Object.keys(macro).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Macro Indicators</h3>
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  const formatChange = (value: number | null) => {
    if (value === null) return 'N/A';
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getChangeColor = (value: number | null) => {
    if (value === null) return 'text-gray-500';
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Macro Indicators</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* USD/INR */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm text-gray-600 mb-1">USD/INR</div>
          <div className="text-xl font-bold text-gray-900">
            {macro.usd_inr ? `₹${macro.usd_inr.toFixed(2)}` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.usd_inr_change_pct)}`}>
            {formatChange(macro.usd_inr_change_pct)}
          </div>
        </div>

        {/* Brent Crude */}
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
          <div className="text-sm text-gray-600 mb-1">Brent Crude</div>
          <div className="text-xl font-bold text-gray-900">
            {macro.brent_crude ? `$${macro.brent_crude.toFixed(2)}` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.brent_change_pct)}`}>
            {formatChange(macro.brent_change_pct)}
          </div>
        </div>

        {/* Gold */}
        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="text-sm text-gray-600 mb-1">Gold</div>
          <div className="text-xl font-bold text-gray-900">
            {macro.gold_price ? `$${macro.gold_price.toFixed(2)}` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.gold_change_pct)}`}>
            {formatChange(macro.gold_change_pct)}
          </div>
        </div>

        {/* US 10Y Yield */}
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <div className="text-sm text-gray-600 mb-1">US 10Y Yield</div>
          <div className="text-xl font-bold text-gray-900">
            {macro.us_10y_yield ? `${macro.us_10y_yield.toFixed(2)}%` : 'N/A'}
          </div>
          <div className={`text-sm font-medium ${getChangeColor(macro.us_10y_change)}`}>
            {macro.us_10y_change !== null ? `${macro.us_10y_change >= 0 ? '+' : ''}${macro.us_10y_change.toFixed(2)}%` : 'N/A'}
          </div>
        </div>
      </div>
      {macro.date && (
        <div className="mt-4 text-xs text-gray-500 text-center">
          Last updated: {new Date(macro.date).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

export default MacroIndicators;

