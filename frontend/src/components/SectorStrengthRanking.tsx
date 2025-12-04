import { useQuery } from 'react-query';
import { api } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface SectorStrengthRankingProps {
  lookbackDays?: number;
}

function SectorStrengthRanking({ lookbackDays = 30 }: SectorStrengthRankingProps) {
  const { data, isLoading } = useQuery(
    ['sector-strength', lookbackDays],
    () => api.getSectorStrengthRanking(lookbackDays),
    { refetchInterval: 300000 }
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Sector Strength Ranking</h3>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!data || !data.rankings || data.rankings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Sector Strength Ranking</h3>
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  const chartData = data.rankings.map((r, idx) => ({
    name: r.sector_id.replace('NIFTY_', ''),
    strength: r.strength_score,
    return: r.total_return,
    momentum: r.momentum,
    rank: idx + 1,
  }));

  const getColor = (value: number) => {
    if (value > 5) return '#10b981'; // green
    if (value > 0) return '#3b82f6'; // blue
    if (value > -5) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Sector Strength Ranking ({lookbackDays} days)</h3>
      
      {/* Top 5 Sectors */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Top Performers</h4>
        <div className="space-y-2">
          {data.rankings.slice(0, 5).map((sector, idx) => (
            <div key={sector.sector_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  idx === 0 ? 'bg-yellow-500 text-white' :
                  idx === 1 ? 'bg-gray-400 text-white' :
                  idx === 2 ? 'bg-orange-500 text-white' :
                  'bg-gray-200 text-gray-700'
                }`}>
                  {idx + 1}
                </div>
                <div>
                  <div className="font-medium">{sector.sector_id.replace('NIFTY_', '')}</div>
                  <div className="text-xs text-gray-500">
                    Return: {sector.total_return >= 0 ? '+' : ''}{sector.total_return.toFixed(2)}% | 
                    Momentum: {sector.momentum >= 0 ? '+' : ''}{sector.momentum.toFixed(2)}%
                  </div>
                </div>
              </div>
              <div className={`text-lg font-bold ${sector.strength_score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {sector.strength_score >= 0 ? '+' : ''}{sector.strength_score.toFixed(1)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Strength Score Comparison</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="strength" name="Strength Score">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.strength)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default SectorStrengthRanking;

