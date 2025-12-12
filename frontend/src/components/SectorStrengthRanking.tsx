import { useQuery } from 'react-query';
import { api } from '../api/client';
import HelpIcon from './HelpIcon';
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
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-semibold text-dark-100">Sector Strength Ranking</h3>
          <HelpIcon
            title="Sector Strength Ranking"
            content={`This section ranks sectors by their relative strength over a specified lookback period.

What it shows:
• Relative performance compared to the market (Nifty 50)
• Strength score based on momentum and price action
• Ranking from strongest to weakest sectors

What to infer:
• Top-ranked sectors show strong relative momentum
• Use this to identify sectors outperforming the market
• Combine with breadth metrics to confirm strength
• Rotate into stronger sectors, avoid weak ones
• Strength rankings help identify sector rotation opportunities`}
          />
        </div>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (!data || !data.rankings || data.rankings.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-semibold text-dark-100">Sector Strength Ranking</h3>
          <HelpIcon
            title="Sector Strength Ranking"
            content={`This section ranks sectors by their relative strength over a specified lookback period.

What it shows:
• Relative performance compared to the market (Nifty 50)
• Strength score based on momentum and price action
• Ranking from strongest to weakest sectors

What to infer:
• Top-ranked sectors show strong relative momentum
• Use this to identify sectors outperforming the market
• Combine with breadth metrics to confirm strength
• Rotate into stronger sectors, avoid weak ones
• Strength rankings help identify sector rotation opportunities`}
          />
        </div>
        <div className="text-dark-400">No data available</div>
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
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-lg font-semibold text-dark-100">Sector Strength Ranking ({lookbackDays} days)</h3>
        <HelpIcon
          title="Sector Strength Ranking"
          content={`This section ranks sectors by their relative strength over a specified lookback period.

What it shows:
• Relative performance compared to the market (Nifty 50)
• Strength score based on momentum and price action
• Ranking from strongest to weakest sectors

What to infer:
• Top-ranked sectors show strong relative momentum
• Use this to identify sectors outperforming the market
• Combine with breadth metrics to confirm strength
• Rotate into stronger sectors, avoid weak ones
• Strength rankings help identify sector rotation opportunities`}
        />
      </div>
      
      {/* Top 5 Sectors */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-dark-300 mb-3">Top Performers</h4>
        <div className="space-y-2">
          {data.rankings.slice(0, 5).map((sector, idx) => (
            <div key={sector.sector_id} className="flex items-center justify-between p-3 bg-dark-700 rounded border border-dark-600">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  idx === 0 ? 'bg-yellow-500 text-white' :
                  idx === 1 ? 'bg-gray-400 text-white' :
                  idx === 2 ? 'bg-orange-500 text-white' :
                  'bg-dark-600 text-dark-300'
                }`}>
                  {idx + 1}
                </div>
                <div>
                  <div className="font-medium text-dark-100">{sector.sector_id.replace('NIFTY_', '')}</div>
                  <div className="text-xs text-dark-400">
                    Return: {sector.total_return >= 0 ? '+' : ''}{sector.total_return.toFixed(2)}% | 
                    Momentum: {sector.momentum >= 0 ? '+' : ''}{sector.momentum.toFixed(2)}%
                  </div>
                </div>
              </div>
              <div className={`text-lg font-bold ${sector.strength_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {sector.strength_score >= 0 ? '+' : ''}{sector.strength_score.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-dark-300 mb-3">Strength Score Comparison</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10, fill: '#d1d5db' }} />
            <YAxis tick={{ fontSize: 10, fill: '#d1d5db' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
              labelStyle={{ color: '#f3f4f6' }}
            />
            <Legend wrapperStyle={{ color: '#d1d5db' }} />
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

