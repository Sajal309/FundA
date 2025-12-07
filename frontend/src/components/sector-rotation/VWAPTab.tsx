import { useQuery } from 'react-query';
import { api } from '../../api/client';

interface VWAPTabProps {
  level: 'sector' | 'industry';
  date: string;
}

function VWAPTab({ level, date }: VWAPTabProps) {
  const { data, isLoading, error } = useQuery(
    ['vwap', level, date],
    () => api.getSectorRotationVWAP(level, date),
    { enabled: !!date }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">Loading VWAP data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-red-400">Error loading VWAP data</div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">No VWAP data available</div>
      </div>
    );
  }

  const getColor = (value: number) => {
    if (value >= 80) return 'bg-green-600';
    if (value >= 60) return 'bg-green-500';
    if (value >= 40) return 'bg-yellow-500';
    if (value >= 20) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark-100 mb-2">
          VWAP Analysis for {level === 'sector' ? 'Sectors' : 'Industries'}
        </h2>
        <p className="text-sm text-dark-400">
          Percentage of market cap where price is above VWAP
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-dark-700 border-b border-dark-600">
              <th className="px-4 py-3 text-left font-medium text-dark-300">Name</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">MCap (Cr.)</th>
              <th className="px-4 py-3 text-center font-medium text-dark-300">Price &gt; VWAP (%)</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((row) => (
              <tr key={row.id} className="border-b border-dark-700 hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-dark-100">{row.name}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.mcap.toFixed(2)}</td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getColor(row.pct_mcap_price_above_vwap)}`}>
                    {row.pct_mcap_price_above_vwap.toFixed(2)}%
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

export default VWAPTab;

