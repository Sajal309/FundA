import { useMemo } from 'react';
import { useQuery } from 'react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

// Canonical sectors list
const CANONICAL_SECTORS = [
  'NIFTY_AUTO',
  'NIFTY_BANK',
  'NIFTY_FMCG',
  'NIFTY_IT',
  'NIFTY_PHARMA',
  'NIFTY_METAL',
  'NIFTY_REALTY',
  'NIFTY_ENERGY',
  'NIFTY_INFRA',
];

interface EarningsWatchData {
  as_of: string;
  next_30d: Array<{
    sector_id: string;
    name: string;
    results_count: number;
    weight_in_sector: number;
  }>;
  revision_heatmap: Array<{
    sector_id: string;
    name: string;
    upgrades_pct_60d: number;
    downgrades_pct_60d: number;
    total_revisions: number;
  }>;
}

function EarningsWatch() {
  const { data, isLoading } = useQuery<EarningsWatchData>(
    'earnings-watch',
    async () => {
      // Use relative URL to go through Vite proxy
      const apiUrl = import.meta.env.VITE_API_URL && !import.meta.env.VITE_API_URL.includes('localhost')
        ? import.meta.env.VITE_API_URL
        : '';
      const response = await fetch(`${apiUrl}/api/v1/earnings-watch`);
      if (!response.ok) throw new Error('Failed to fetch earnings watch data');
      return response.json();
    },
    { refetchInterval: 300000 }
  );

  // Filter to canonical sectors only - must be called before early returns
  const canonicalNext30d = useMemo(() => {
    if (!data?.next_30d) return [];
    return data.next_30d.filter(s => CANONICAL_SECTORS.includes(s.sector_id));
  }, [data?.next_30d]);

  const canonicalRevisionHeatmap = useMemo(() => {
    if (!data?.revision_heatmap) return [];
    return data.revision_heatmap.filter(s => CANONICAL_SECTORS.includes(s.sector_id));
  }, [data?.revision_heatmap]);

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Earnings Watch</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Earnings Watch</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

  // Filter sectors with upcoming results
  const upcomingSectors = canonicalNext30d.filter(s => s.results_count > 0);
  const upcomingChartData = upcomingSectors.map(s => ({
    name: s.name.replace('Nifty ', ''),
    count: s.results_count,
  }));

  // Revision heatmap data
  const revisionData = canonicalRevisionHeatmap
    .filter(s => s.total_revisions > 0)
    .map(s => ({
      name: s.name.replace('Nifty ', ''),
      upgrades: s.upgrades_pct_60d * 100,
      downgrades: s.downgrades_pct_60d * 100,
      net: (s.upgrades_pct_60d - s.downgrades_pct_60d) * 100,
    }));

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-100">Earnings Watch</h3>
        <span className="text-xs text-dark-400">As of {new Date(data.as_of).toLocaleDateString()}</span>
      </div>

      {/* Upcoming Results */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-dark-300 mb-3">Upcoming Results (Next 30 Days)</h4>
        {upcomingSectors.length === 0 ? (
          <div className="text-sm text-dark-400">No upcoming earnings results scheduled</div>
        ) : (
          <>
            <div className="mb-4">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={upcomingChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10, fill: '#d1d5db' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#d1d5db' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
                    labelStyle={{ color: '#f3f4f6' }}
                  />
                  <Legend wrapperStyle={{ color: '#d1d5db' }} />
                  <Bar dataKey="count" name="Results Count" fill="#3b82f6">
                    {upcomingChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill="#3b82f6" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="text-xs text-dark-400">
              Total upcoming results: {upcomingSectors.reduce((sum, s) => sum + s.results_count, 0)}
            </div>
          </>
        )}
      </div>

      {/* Revision Heatmap */}
      <div>
        <h4 className="text-sm font-medium text-dark-300 mb-3">Revision Heatmap (Last 60 Days)</h4>
        {revisionData.length === 0 ? (
          <div className="text-sm text-dark-400">No revision data available</div>
        ) : (
          <>
            <div className="mb-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={revisionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10, fill: '#d1d5db' }} />
                  <YAxis domain={[-100, 100]} tick={{ fontSize: 10, fill: '#d1d5db' }} />
                  <Tooltip 
                    formatter={(value: number) => [`${value >= 0 ? '+' : ''}${value.toFixed(2)}%`, 'Net Revisions']}
                    labelFormatter={(label) => `Sector: ${label}`}
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
                    labelStyle={{ color: '#f3f4f6' }}
                  />
                  <Legend wrapperStyle={{ color: '#d1d5db' }} />
                  <Bar dataKey="upgrades" name="Upgrades %" fill="#10b981" />
                  <Bar dataKey="downgrades" name="Downgrades %" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
              {canonicalRevisionHeatmap
                .filter(s => s.total_revisions > 0)
                .map((sector) => {
                  const net = (sector.upgrades_pct_60d - sector.downgrades_pct_60d) * 100;
                  return (
                    <div key={sector.sector_id} className="p-2 bg-dark-700 rounded border border-dark-600">
                      <div className="font-medium text-dark-100">{sector.name}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-green-400">
                          ↑ {(sector.upgrades_pct_60d * 100).toFixed(2)}%
                        </span>
                        <span className="text-red-400">
                          ↓ {(sector.downgrades_pct_60d * 100).toFixed(2)}%
                        </span>
                        <span className={`ml-auto font-medium ${
                          net >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          Net: {net >= 0 ? '+' : ''}{net.toFixed(2)}%
                        </span>
                      </div>
                      <div className="text-dark-500 mt-1">
                        {sector.total_revisions} revisions
                      </div>
                    </div>
                  );
                })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default EarningsWatch;

