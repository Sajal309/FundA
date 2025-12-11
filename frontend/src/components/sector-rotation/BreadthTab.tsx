import { useState } from 'react';
import { useQuery } from 'react-query';
import { api } from '../../api/client';
import DataFreshness from '../DataFreshness';

interface BreadthTabProps {
  level: 'sector' | 'industry';
  date: string;
}

function BreadthTab({ level, date }: BreadthTabProps) {
  const [metricType, setMetricType] = useState<'mcap' | 'count'>('mcap');

  const { data, isLoading, error } = useQuery(
    ['breadth', level, date, metricType],
    () => api.getSectorRotationBreadth(level, date, metricType),
    { enabled: !!date }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">Loading breadth data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-red-400">Error loading breadth data</div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">No breadth data available</div>
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
        <div className="flex items-start justify-between mb-2">
          <div>
            <h2 className="text-xl font-semibold text-dark-100 mb-2">
              Which {level === 'sector' ? 'Sector' : 'Industry'} is the right {level === 'sector' ? 'Sector' : 'Industry'} to invest now?
            </h2>
            <p className="text-sm text-dark-400">
              Track how the money is moving from one {level === 'sector' ? 'Sector' : 'Industry'} to another
            </p>
          </div>
          {data.metadata && (
            <DataFreshness
              lastUpdated={data.metadata.last_updated}
              fetchedAt={data.metadata.fetched_at}
              isLive={data.metadata.is_live}
              source={`${level === 'sector' ? 'Sector' : 'Industry'} breadth`}
              compact
            />
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMetricType('mcap')}
            className={`px-3 py-1 rounded text-sm ${
              metricType === 'mcap'
                ? 'bg-blue-600 text-white'
                : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
            }`}
          >
            Per(%)
          </button>
          <button
            onClick={() => setMetricType('count')}
            className={`px-3 py-1 rounded text-sm ${
              metricType === 'count'
                ? 'bg-blue-600 text-white'
                : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
            }`}
          >
            Count
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-dark-700 border-b border-dark-600">
              <th className="px-4 py-3 text-left font-medium text-dark-300">Name</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">MCap (Cr.)</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Stocks</th>
              <th className="px-4 py-3 text-center font-medium text-dark-300" colSpan={5}>
                MCap Above
              </th>
            </tr>
            <tr className="bg-dark-700 border-b border-dark-600">
              <th className="px-4 py-2"></th>
              <th className="px-4 py-2"></th>
              <th className="px-4 py-2"></th>
              <th className="px-4 py-2 text-center font-medium text-dark-300">RS 55 &gt; 0</th>
              <th className="px-4 py-2 text-center font-medium text-dark-300">RSI &gt; 50</th>
              <th className="px-4 py-2 text-center font-medium text-dark-300">SMA 20</th>
              <th className="px-4 py-2 text-center font-medium text-dark-300">SMA 50</th>
              <th className="px-4 py-2 text-center font-medium text-dark-300">SMA 100</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((row) => (
              <tr key={row.id} className="border-b border-dark-700 hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-dark-100">{row.name}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.mcap.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.stocks}</td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getColor(row.metrics.pct_rs55_gt0)}`}>
                    {row.metrics.pct_rs55_gt0.toFixed(2)}%
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getColor(row.metrics.pct_rsi_gt50)}`}>
                    {row.metrics.pct_rsi_gt50.toFixed(2)}%
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getColor(row.metrics.pct_above_sma20)}`}>
                    {row.metrics.pct_above_sma20.toFixed(2)}%
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getColor(row.metrics.pct_above_sma50)}`}>
                    {row.metrics.pct_above_sma50.toFixed(2)}%
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className={`inline-block px-3 py-1 rounded text-white font-medium ${getColor(row.metrics.pct_above_sma100)}`}>
                    {row.metrics.pct_above_sma100.toFixed(2)}%
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

export default BreadthTab;

