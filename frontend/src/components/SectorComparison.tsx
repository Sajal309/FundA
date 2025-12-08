import { useState, useMemo } from 'react';
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

interface SectorComparisonProps {
  sectors: SectorSummary[];
}

function SectorComparison({ sectors }: SectorComparisonProps) {
  // Filter to canonical sectors only
  const canonicalSectors = useMemo(() => {
    return sectors.filter(s => CANONICAL_SECTORS.includes(s.sector_id));
  }, [sectors]);

  const [selectedSectors, setSelectedSectors] = useState<string[]>(
    canonicalSectors.slice(0, 3).map((s) => s.sector_id)
  );
  const [metric, setMetric] = useState<'returns' | 'sentiment'>('returns');

  const { data: comparison, isLoading } = useQuery(
    ['sector-comparison', selectedSectors, metric],
    async () => {
      if (selectedSectors.length === 0) return null;
      const sectorIds = selectedSectors.join(',');
      const response = await fetch(
        // Use relative URL to go through Vite proxy
        (() => {
          const apiUrl = import.meta.env.VITE_API_URL && !import.meta.env.VITE_API_URL.includes('localhost')
            ? import.meta.env.VITE_API_URL
            : '';
          return `${apiUrl}/api/v1/analytics/sectors/compare?sector_ids=${sectorIds}&metric=${metric}`;
        })()
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
        : [...prev, sectorId].slice(0, 3) // Max 3 sectors for quarter outlook
    );
  };

  // Prepare chart data
  const chartData = comparison?.comparison
    ? Object.entries(comparison.comparison).map(([sectorId, values]: [string, any]) => {
        const sector = canonicalSectors.find((s) => s.sector_id === sectorId);
        if (metric === 'returns') {
          // Values: [ret_1m, ret_3m, ret_6m, rel_3m_vs_nifty]
          return {
            sector: sector?.name || sectorId.replace('NIFTY_', ''),
            '1M': (values[0] || 0) * 100,
            '3M': (values[1] || 0) * 100,
            '6M': (values[2] || 0) * 100,
            '3M vs Nifty': (values[3] || 0) * 100,
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
        <div className="text-sm text-dark-400 mb-2">Select sectors to compare (max 3):</div>
        <div className="flex flex-wrap gap-2">
          {canonicalSectors.map((sector) => (
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
              <Bar dataKey="1M" fill="#3b82f6" name="1 Month Return %" />
              <Bar dataKey="3M" fill="#10b981" name="3 Month Return %" />
              <Bar dataKey="6M" fill="#f59e0b" name="6 Month Return %" />
              <Bar dataKey="3M vs Nifty" fill="#8b5cf6" name="3M vs Nifty %" />
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

