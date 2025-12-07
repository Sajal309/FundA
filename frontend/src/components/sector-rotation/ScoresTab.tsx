import { useQuery } from 'react-query';
import { api } from '../../api/client';

interface ScoresTabProps {
  level: 'sector' | 'industry';
  date: string;
}

function ScoresTab({ level, date }: ScoresTabProps) {
  const { data, isLoading, error } = useQuery(
    ['scores', level, date],
    () => api.getSectorRotationScores(level, date),
    { enabled: !!date }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">Loading momentum scores...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-red-400">Error loading momentum scores</div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">No momentum score data available</div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 61) return 'bg-green-600';
    if (score >= 41) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 61) return 'Bullish';
    if (score >= 41) return 'Neutral';
    return 'Bearish';
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark-100 mb-2">
          Curious to see which {level === 'sector' ? 'sectors' : 'industries'} are in momentum across three different time horizons?
        </h2>
        <p className="text-sm text-dark-400">
          Track how the money is moving from one {level === 'sector' ? 'Sector' : 'Industry'} to another
        </p>
      </div>

      {/* Legend */}
      <div className="mb-6 flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500"></div>
          <span className="text-dark-300">Bearish (0-40)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-yellow-500"></div>
          <span className="text-dark-300">Neutral (41-60)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-600"></div>
          <span className="text-dark-300">Bullish (61-100)</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-dark-700 border-b border-dark-600">
              <th className="px-4 py-3 text-left font-medium text-dark-300">Name</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">MCap (Cr.)</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Stocks</th>
              <th className="px-4 py-3 text-center font-medium text-dark-300">1 Month</th>
              <th className="px-4 py-3 text-center font-medium text-dark-300">3 Months</th>
              <th className="px-4 py-3 text-center font-medium text-dark-300">6 Months</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((row) => (
              <tr key={row.id} className="border-b border-dark-700 hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-dark-100">{row.name}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.mcap.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.stocks}</td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getScoreColor(row.score_1m)}`}>
                    {row.score_1m.toFixed(2)}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getScoreColor(row.score_3m)}`}>
                    {row.score_3m.toFixed(2)}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getScoreColor(row.score_6m)}`}>
                    {row.score_6m.toFixed(2)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ScoresTab;

