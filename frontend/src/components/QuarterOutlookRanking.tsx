import { useQuery } from 'react-query';
import { api, QuarterOutlookSector } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import HelpIcon from './HelpIcon';

interface QuarterOutlookRankingProps {
  onSectorClick?: (sectorId: string) => void;
}

function QuarterOutlookRanking({ onSectorClick }: QuarterOutlookRankingProps) {
  const { data, isLoading, refetch } = useQuery(
    'quarter-outlook',
    api.getQuarterOutlook,
    { 
      refetchInterval: 300000, // Refetch every 5 minutes
      staleTime: 60000, // Consider data stale after 1 minute
    }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Quarter Outlook Ranking</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (!data || !data.sectors || data.sectors.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Quarter Outlook Ranking</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

  const getQuarterScoreLabel = (score: number, label?: string): string => {
    // Use label from API if available, otherwise compute from score
    if (label) return label;
    if (score >= 1.5) return 'Strong';
    if (score >= -0.5) return 'Neutral';
    return 'Weak';
  };

  const getQuarterScoreColor = (score: number): string => {
    if (score >= 1.5) return '#10b981'; // green
    if (score >= 0.5) return '#3b82f6'; // blue
    if (score >= -0.5) return '#f59e0b'; // yellow
    if (score >= -1.5) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const getForecastColor = (label: string): string => {
    if (label === 'UP') return '#10b981';
    if (label === 'NEUTRAL') return '#6b7280';
    return '#ef4444';
  };

  const chartData = data.sectors.map((sector, idx) => ({
    name: sector.name.replace('Nifty ', ''),
    quarter_score: sector.quarter_score,
    rank: idx + 1,
  }));

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-dark-100">Quarter Outlook Ranking</h3>
          <HelpIcon
            title="Quarter Outlook Ranking"
            content={`This section ranks sectors by their QuarterScore, a composite metric that predicts 3-month performance.

What it shows:
• QuarterScore: Combines momentum, breadth, flows, valuation, earnings, sentiment, and macro factors
• Forecast Label: UP, NEUTRAL, or DOWN prediction
• Expected Return: Projected 3-month return percentage

What to infer:
• Higher scores (green) indicate stronger fundamentals and positive momentum
• Lower scores (red) suggest weakness or headwinds
• Use this to identify sectors with the best risk-adjusted outlook
• Combine with other metrics for confirmation before making decisions`}
          />
        </div>
        <span className="text-xs text-dark-400">As of {new Date(data.as_of).toLocaleDateString()}</span>
      </div>
      
      {/* Top 5 Sectors */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-dark-300 mb-3">Top Sectors</h4>
        <div className="space-y-2">
          {data.sectors.slice(0, 5).map((sector, idx) => (
            <div
              key={sector.sector_id}
              onClick={() => onSectorClick?.(sector.sector_id)}
              className={`flex items-center justify-between p-3 bg-dark-700 rounded cursor-pointer hover:bg-dark-600 transition-colors border border-dark-600 ${
                onSectorClick ? 'cursor-pointer' : ''
              }`}
            >
              <div className="flex items-center gap-3 flex-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  idx === 0 ? 'bg-yellow-500 text-white' :
                  idx === 1 ? 'bg-gray-400 text-white' :
                  idx === 2 ? 'bg-orange-500 text-white' :
                  'bg-dark-500 text-dark-100'
                }`}>
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-dark-100">{sector.name}</div>
                  <div className="text-xs text-dark-400 flex items-center gap-2">
                    <span>Score: {sector.quarter_score >= 0 ? '+' : ''}{sector.quarter_score.toFixed(2)}</span>
                    <span className="text-dark-500">•</span>
                    <span className={`font-medium px-2 py-0.5 rounded text-xs`}
                      style={{ backgroundColor: getForecastColor(sector.forecast_3m_label) + '20', color: getForecastColor(sector.forecast_3m_label) }}>
                      {sector.forecast_3m_label}
                    </span>
                    <span className="text-dark-500">•</span>
                    <span>Exp. Return: {sector.expected_return_pct >= 0 ? '+' : ''}{sector.expected_return_pct.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
              <div className="ml-4">
                <div className={`text-sm font-medium px-2 py-1 rounded`}
                  style={{ backgroundColor: getQuarterScoreColor(sector.quarter_score) + '20', color: getQuarterScoreColor(sector.quarter_score) }}>
                  {sector.label || getQuarterScoreLabel(sector.quarter_score)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-dark-300 mb-3">QuarterScore Comparison</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10, fill: '#d1d5db' }} />
            <YAxis tick={{ fontSize: 10, fill: '#d1d5db' }} />
            <Tooltip 
              formatter={(value: number) => [`${value >= 0 ? '+' : ''}${value.toFixed(2)}`, 'QuarterScore']}
              labelFormatter={(label) => `Sector: ${label}`}
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
              labelStyle={{ color: '#f3f4f6' }}
            />
            <Legend wrapperStyle={{ color: '#d1d5db' }} />
            <Bar dataKey="quarter_score" name="QuarterScore">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getQuarterScoreColor(entry.quarter_score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default QuarterOutlookRanking;

