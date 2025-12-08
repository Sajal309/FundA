import { useMemo } from 'react';
import { useQuery } from 'react-query';
import { api } from '../api/client';
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

interface BreadthSector {
  sector_id: string;
  name: string;
  above_50dma_pct: number;
  above_200dma_pct: number | null;
  highs_3m_pct: number;
  lows_3m_pct: number | null;
}

interface BreadthResponse {
  as_of: string;
  sectors: BreadthSector[];
}

function BreadthLeadership() {
  const { data, isLoading } = useQuery<BreadthResponse>(
    'breadth',
    async () => {
      // Use relative URL to go through Vite proxy
      const apiUrl = import.meta.env.VITE_API_URL && !import.meta.env.VITE_API_URL.includes('localhost')
        ? import.meta.env.VITE_API_URL
        : '';
      const response = await fetch(`${apiUrl}/api/v1/breadth`);
      if (!response.ok) throw new Error('Failed to fetch breadth data');
      return response.json();
    },
    { refetchInterval: 300000 }
  );

  // Filter to canonical sectors only - must be called before early returns
  const canonicalSectors = useMemo(() => {
    if (!data?.sectors) return [];
    return data.sectors.filter(s => CANONICAL_SECTORS.includes(s.sector_id));
  }, [data?.sectors]);

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Breadth & Leadership</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (!data || !data.sectors || data.sectors.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Breadth & Leadership</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

  const chartData = canonicalSectors.map((sector) => ({
    name: sector.name.replace('Nifty ', ''),
    above_50dma: sector.above_50dma_pct * 100,
    above_200dma: (sector.above_200dma_pct || 0) * 100,
    highs_3m: sector.highs_3m_pct * 100,
    lows_3m: (sector.lows_3m_pct || 0) * 100,
  }));

  const getBreadthColor = (pct: number): string => {
    if (pct >= 0.7) return '#10b981'; // green - broad participation
    if (pct >= 0.5) return '#3b82f6'; // blue - moderate
    if (pct >= 0.3) return '#f59e0b'; // yellow - narrow
    return '#ef4444'; // red - very narrow
  };

  const getBreadthLabel = (pct: number): string => {
    if (pct >= 0.7) return 'Broad';
    if (pct >= 0.5) return 'Moderate';
    if (pct >= 0.3) return 'Narrow';
    return 'Very Narrow';
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-100">Breadth & Leadership</h3>
        <span className="text-xs text-dark-400">As of {new Date(data.as_of).toLocaleDateString()}</span>
      </div>

      {/* Breadth Table */}
      <div className="mb-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-dark-700">
          <thead className="bg-dark-700">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-dark-400 uppercase">Sector</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-dark-400 uppercase">Above 50DMA</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-dark-400 uppercase">Above 200DMA</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-dark-400 uppercase">3M Highs</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-dark-400 uppercase">3M Lows</th>
            </tr>
          </thead>
          <tbody className="bg-dark-800 divide-y divide-dark-700">
            {canonicalSectors.map((sector) => {
              const breadth50 = sector.above_50dma_pct;
              const breadth200 = sector.above_200dma_pct || 0;
              const highs = sector.highs_3m_pct;
              const lows = sector.lows_3m_pct || 0;
              
              return (
                <tr key={sector.sector_id} className="hover:bg-dark-700">
                  <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-dark-100">
                    {sector.name}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-dark-600 rounded-full h-2">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${breadth50 * 100}%`,
                            backgroundColor: getBreadthColor(breadth50),
                          }}
                        />
                      </div>
                      <span className="text-sm text-dark-300">
                        {(breadth50 * 100).toFixed(2)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">
                    {sector.above_200dma_pct !== null ? (
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-dark-600 rounded-full h-2">
                          <div
                            className="h-2 rounded-full"
                            style={{
                              width: `${breadth200 * 100}%`,
                              backgroundColor: getBreadthColor(breadth200),
                            }}
                          />
                        </div>
                        <span className="text-sm text-dark-300">
                          {(breadth200 * 100).toFixed(2)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-dark-500">N/A</span>
                    )}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        highs >= 0.1 ? 'bg-green-900/30 text-green-400' : 'bg-dark-700 text-dark-400'
                      }`}>
                        {(highs * 100).toFixed(2)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">
                    {sector.lows_3m_pct !== null ? (
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          lows >= 0.1 ? 'bg-red-900/30 text-red-400' : 'bg-dark-700 text-dark-400'
                        }`}>
                          {(lows * 100).toFixed(2)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-dark-500">N/A</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Chart */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-dark-100 mb-3">Breadth Comparison (% Above 50DMA)</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10, fill: '#d1d5db' }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#d1d5db' }} />
            <Tooltip 
              formatter={(value: number) => [`${value.toFixed(2)}%`, '% Above 50DMA']}
              labelFormatter={(label) => `Sector: ${label}`}
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
              labelStyle={{ color: '#f3f4f6' }}
            />
            <Legend wrapperStyle={{ color: '#d1d5db' }} />
            <Bar dataKey="above_50dma" name="% Above 50DMA">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBreadthColor(entry.above_50dma / 100)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-dark-400">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }} />
          <span>Broad (≥70%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3b82f6' }} />
          <span>Moderate (50-70%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }} />
          <span>Narrow (30-50%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }} />
          <span>Very Narrow (&lt;30%)</span>
        </div>
      </div>
    </div>
  );
}

export default BreadthLeadership;

