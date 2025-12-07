import { useState } from 'react';
import { useQuery } from 'react-query';
import { api, SectorSummary } from '../api/client';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface SectorComparisonProps {
  sectors: SectorSummary[];
}

function SectorComparison({ sectors }: SectorComparisonProps) {
  const [selectedSectors, setSelectedSectors] = useState<string[]>(
    sectors.slice(0, 3).map((s) => s.sector_id)
  );
  const [metric, setMetric] = useState<'returns' | 'sentiment'>('returns');

  const { data: comparison, isLoading } = useQuery(
    ['sector-comparison', selectedSectors, metric],
    async () => {
      if (selectedSectors.length === 0) return null;
      const sectorIds = selectedSectors.join(',');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/analytics/sectors/compare?sector_ids=${sectorIds}&metric=${metric}`
      );
      if (!response.ok) return null;
      return response.json();
    },
    { enabled: selectedSectors.length > 0 }
  );

  const handleSectorToggle = (sectorId: string) => {
    setSelectedSectors((prev) =>
      prev.includes(sectorId)
        ? prev.filter((id) => id !== sectorId)
        : [...prev, sectorId].slice(0, 5) // Max 5 sectors
    );
  };

  // Prepare chart data
  const chartData = comparison?.comparison
    ? Object.entries(comparison.comparison).map(([sectorId, values]: [string, any]) => {
        const sector = sectors.find((s) => s.sector_id === sectorId);
        if (metric === 'returns') {
          return {
            sector: sector?.name || sectorId.replace('NIFTY_', ''),
            '1D': values[0] * 100,
            '5D': values[1] * 100,
            '1M': values[2] * 100,
          };
        } else {
          return {
            sector: sector?.name || sectorId.replace('NIFTY_', ''),
            '1D': values[0],
            '7D': values[1],
          };
        }
      })
    : [];

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-100">Sector Comparison</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setMetric('returns')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              metric === 'returns'
                ? 'bg-blue-600 text-white'
                : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
            }`}
          >
            Returns
          </button>
          <button
            onClick={() => setMetric('sentiment')}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              metric === 'sentiment'
                ? 'bg-blue-600 text-white'
                : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
            }`}
          >
            Sentiment
          </button>
        </div>
      </div>

      {/* Sector Selection */}
      <div className="mb-4">
        <div className="text-sm text-dark-400 mb-2">Select sectors to compare (max 5):</div>
        <div className="flex flex-wrap gap-2">
          {sectors.map((sector) => (
            <button
              key={sector.sector_id}
              onClick={() => handleSectorToggle(sector.sector_id)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                selectedSectors.includes(sector.sector_id)
                  ? 'bg-blue-600 text-white'
                  : 'bg-dark-700 text-dark-300 hover:bg-dark-600 border border-dark-600'
              }`}
            >
              {sector.name}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {isLoading ? (
        <div className="text-center py-8 text-dark-400">Loading comparison...</div>
      ) : chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          {metric === 'returns' ? (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="sector" tick={{ fontSize: 12, fill: '#d1d5db' }} />
              <YAxis tick={{ fontSize: 12, fill: '#d1d5db' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
                labelStyle={{ color: '#f3f4f6' }}
              />
              <Legend wrapperStyle={{ color: '#d1d5db' }} />
              <Bar dataKey="1D" fill="#3b82f6" name="1 Day Return %" />
              <Bar dataKey="5D" fill="#10b981" name="5 Day Return %" />
              <Bar dataKey="1M" fill="#f59e0b" name="1 Month Return %" />
            </BarChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="sector" tick={{ fontSize: 12, fill: '#d1d5db' }} />
              <YAxis tick={{ fontSize: 12, fill: '#d1d5db' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f3f4f6' }}
                labelStyle={{ color: '#f3f4f6' }}
              />
              <Legend wrapperStyle={{ color: '#d1d5db' }} />
              <Line
                type="monotone"
                dataKey="1D"
                stroke="#3b82f6"
                strokeWidth={2}
                name="1 Day Sentiment"
              />
              <Line
                type="monotone"
                dataKey="7D"
                stroke="#10b981"
                strokeWidth={2}
                name="7 Day Sentiment"
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      ) : (
        <div className="text-center py-8 text-dark-400">
          Select sectors to compare
        </div>
      )}
    </div>
  );
}

export default SectorComparison;

