import { useQuery } from 'react-query';
import { api } from '../api/client';

function MarketSummary() {
  const { data: flows } = useQuery(
    'market-flows',
    () => api.getFlowsAnalysis(undefined, 7),
    { refetchInterval: 300000 }
  );

  const { data: correlations } = useQuery(
    'market-correlations',
    () => api.getSectorCorrelations(30),
    { refetchInterval: 300000 }
  );

  // Calculate average correlation
  const avgCorrelation = correlations?.correlations
    ? Object.values(correlations.correlations).reduce((a: number, b: number) => a + b, 0) /
      Object.keys(correlations.correlations).length
    : null;

  return (
    <div className="bg-gradient-to-r from-blue-900/50 to-blue-800/50 rounded-lg shadow-lg p-6 border border-blue-700/30 text-dark-100">
      <h3 className="text-xl font-bold mb-4">Market Summary</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div className="text-sm opacity-90 mb-1">FII Flows (7d)</div>
          <div className="text-2xl font-bold">
            {flows ? (
              <span className={flows.total_fii_net >= 0 ? 'text-green-300' : 'text-red-300'}>
                ₹{(flows.total_fii_net / 1000000).toFixed(2)} Cr
              </span>
            ) : (
              'N/A'
            )}
          </div>
        </div>
        <div>
          <div className="text-sm opacity-90 mb-1">DII Flows (7d)</div>
          <div className="text-2xl font-bold">
            {flows ? (
              <span className={flows.total_dii_net >= 0 ? 'text-green-300' : 'text-red-300'}>
                ₹{(flows.total_dii_net / 1000000).toFixed(2)} Cr
              </span>
            ) : (
              'N/A'
            )}
          </div>
        </div>
        <div>
          <div className="text-sm opacity-90 mb-1">Avg Sector Correlation</div>
          <div className="text-2xl font-bold">
            {avgCorrelation !== null ? avgCorrelation.toFixed(2) : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MarketSummary;

