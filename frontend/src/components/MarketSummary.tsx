import { useQuery } from 'react-query';
import { api } from '../api/client';

function MarketSummary() {
  const { data: flows } = useQuery(
    'market-flows',
    // Analyze a wider window of flows so we still have data even if the last few days are missing
    // We'll compute the last 7 available days on the client
    () => api.getFlowsAnalysis(undefined, 30),
    { refetchInterval: 300000 }
  );

  const { data: correlations } = useQuery(
    'market-correlations',
    () => api.getSectorCorrelations(30),
    { refetchInterval: 300000 }
  );

  // Aggregate FII/DII net flows for the last 7 AVAILABLE days (₹ Cr), not total traded amount
  let fii7dCr: string | null = null;
  let dii7dCr: string | null = null;

  if (flows?.flows_by_date && Object.keys(flows.flows_by_date).length > 0) {
    // Sort dates descending and take the latest 7 entries that actually have data
    const sortedEntries = Object.entries(flows.flows_by_date)
      .sort(([d1], [d2]) => (d1 < d2 ? 1 : d1 > d2 ? -1 : 0))
      .slice(0, 7);

    const fiiSum = sortedEntries.reduce(
      (acc: number, [, v]: [string, any]) => acc + (v?.fii || 0),
      0
    );
    const diiSum = sortedEntries.reduce(
      (acc: number, [, v]: [string, any]) => acc + (v?.dii || 0),
      0
    );

    // Convert from INR to Crores (1 Cr = 10^7)
    fii7dCr = (fiiSum / 1e7).toFixed(2);
    dii7dCr = (diiSum / 1e7).toFixed(2);
  }

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
          <div className="text-sm opacity-90 mb-1">FII Flows (last 7 days)</div>
          <div className="text-2xl font-bold">
            {fii7dCr !== null ? (
              <span className={parseFloat(fii7dCr) >= 0 ? 'text-green-300' : 'text-red-300'}>
                ₹{fii7dCr} Cr
              </span>
            ) : (
              'N/A'
            )}
          </div>
        </div>
        <div>
          <div className="text-sm opacity-90 mb-1">DII Flows (last 7 days)</div>
          <div className="text-2xl font-bold">
            {dii7dCr !== null ? (
              <span className={parseFloat(dii7dCr) >= 0 ? 'text-green-300' : 'text-red-300'}>
                ₹{dii7dCr} Cr
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

