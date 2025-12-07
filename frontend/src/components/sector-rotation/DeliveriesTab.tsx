import { useState } from 'react';
import { useQuery } from 'react-query';
import { api } from '../../api/client';

interface DeliveriesTabProps {
  level: 'sector' | 'industry';
  date: string;
}

type SortField = 'mcap' | 'mcap_change_pct' | 'traded_value_multiple' | 'delivery_value_multiple';
type SortDirection = 'asc' | 'desc';

function DeliveriesTab({ level, date }: DeliveriesTabProps) {
  const [sortField, setSortField] = useState<SortField>('mcap');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const { data, isLoading, error } = useQuery(
    ['deliveries', level, date],
    () => api.getSectorRotationDeliveries(level, date),
    { enabled: !!date }
  );

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">Loading delivery statistics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-red-400">Error loading delivery statistics</div>
      </div>
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <div className="text-center py-8 text-dark-400">No delivery data available</div>
      </div>
    );
  }

  // Sort data
  const sortedData = [...data.data].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];
    if (sortDirection === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const SortableHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <th
      className="px-4 py-3 text-right font-medium text-dark-300 cursor-pointer hover:text-dark-100"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center justify-end gap-1">
        {children}
        {sortField === field && (
          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </th>
  );

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-dark-100 mb-2">
          Looking for {level === 'sector' ? 'Sectors' : 'Industries'} with higher delivery?
        </h2>
        <p className="text-sm text-dark-400">
          Track how the money is moving from one {level === 'sector' ? 'Sector' : 'Industry'} to another
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-dark-700 border-b border-dark-600">
              <th className="px-4 py-3 text-left font-medium text-dark-300">Name</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Stocks</th>
              <SortableHeader field="mcap">MCap (Cr.)</SortableHeader>
              <SortableHeader field="mcap_change_pct">MCap Chg. (Cr.)</SortableHeader>
              <th className="px-4 py-3 text-right font-medium text-dark-300">MCap Chg. %</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Vol (Cr.)</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Vol Avg. (Cr.)</th>
              <SortableHeader field="traded_value_multiple">Vol Multiple (x)</SortableHeader>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Del (Cr.)</th>
              <th className="px-4 py-3 text-right font-medium text-dark-300">Del Avg. (Cr.)</th>
              <SortableHeader field="delivery_value_multiple">Del Multiple (x)</SortableHeader>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row) => (
              <tr key={row.id} className="border-b border-dark-700 hover:bg-dark-700/50">
                <td className="px-4 py-3 font-medium text-dark-100">{row.name}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.stocks}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.mcap.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.mcap_change_abs.toFixed(2)}</td>
                <td className={`px-4 py-3 text-right font-medium ${
                  row.mcap_change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {row.mcap_change_pct >= 0 ? '+' : ''}{row.mcap_change_pct.toFixed(2)}%
                </td>
                <td className="px-4 py-3 text-right text-dark-300">{row.traded_value.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.traded_value_avg.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300 font-medium">{row.traded_value_multiple.toFixed(2)}x</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.delivery_value.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300">{row.delivery_value_avg.toFixed(2)}</td>
                <td className="px-4 py-3 text-right text-dark-300 font-medium">{row.delivery_value_multiple.toFixed(2)}x</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DeliveriesTab;

