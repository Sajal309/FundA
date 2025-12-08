import { useState } from 'react';
import { useQuery } from 'react-query';
import { api } from '../api/client';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
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

interface CorrelationMatrixProps {
  lookbackDays?: number;
}

function CorrelationMatrix({ lookbackDays = 30 }: CorrelationMatrixProps) {
  const [showFullMatrix, setShowFullMatrix] = useState(false);
  
  const { data: correlationsData, isLoading: correlationsLoading } = useQuery(
    ['correlations', lookbackDays],
    () => api.getSectorCorrelations(lookbackDays),
    { refetchInterval: 300000 } // Refetch every 5 minutes
  );

  const { data: topCorrelationsData, isLoading: topCorrelationsLoading } = useQuery(
    ['top-correlations', lookbackDays],
    () => api.getTopCorrelations(lookbackDays, 3),
    { refetchInterval: 300000 }
  );

  if (correlationsLoading || topCorrelationsLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Sector Correlations</h3>
        <div className="text-center py-8 text-dark-400">Loading correlations...</div>
      </div>
    );
  }

  if (!correlationsData || !correlationsData.correlations) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Sector Correlations</h3>
        <div className="text-center py-8 text-dark-400">No correlation data available</div>
      </div>
    );
  }

  // Parse correlations into matrix format - filter to canonical sectors only
  const correlations = correlationsData.correlations;
  const sectorPairs = Object.keys(correlations);
  
  // Extract unique sectors, but filter to canonical only
  const sectors = new Set<string>();
  sectorPairs.forEach((pair) => {
    // Try to match canonical sectors in the pair key
    for (const canonSector of CANONICAL_SECTORS) {
      if (pair.includes(canonSector)) {
        sectors.add(canonSector);
      }
    }
  });
  
  // Ensure all canonical sectors are included even if no correlations found
  CANONICAL_SECTORS.forEach(s => sectors.add(s));
  
  const sectorList = Array.from(sectors).filter(s => CANONICAL_SECTORS.includes(s)).sort();
  
  // Build matrix data
  const matrixData: Array<{ x: string; y: string; value: number; sector1: string; sector2: string }> = [];
  
  sectorList.forEach((sector1) => {
    sectorList.forEach((sector2) => {
      if (sector1 === sector2) {
        matrixData.push({
          x: sector1,
          y: sector2,
          value: 1.0,
          sector1,
          sector2,
        });
      } else {
        const key1 = `${sector1}_${sector2}`;
        const key2 = `${sector2}_${sector1}`;
        const corr = correlations[key1] || correlations[key2] || 0;
        matrixData.push({
          x: sector1,
          y: sector2,
          value: corr,
          sector1,
          sector2,
        });
      }
    });
  });

  // Color scale for correlations
  const getColor = (value: number) => {
    if (value >= 0.8) return '#10b981'; // Green for high positive
    if (value >= 0.5) return '#3b82f6'; // Blue for moderate positive
    if (value >= 0) return '#94a3b8'; // Gray for low positive
    if (value >= -0.5) return '#f59e0b'; // Orange for low negative
    return '#ef4444'; // Red for high negative
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-100">Sector Correlations ({lookbackDays} days)</h3>
        <button
          onClick={() => setShowFullMatrix(!showFullMatrix)}
          className="px-3 py-1 text-sm bg-dark-700 text-dark-300 hover:bg-dark-600 rounded transition-colors"
        >
          {showFullMatrix ? 'Hide' : 'Show'} Full Matrix (Advanced)
        </button>
      </div>

      {/* Top Correlations Summary */}
      {topCorrelationsData && (
        <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-dark-700 rounded-lg p-3">
            <div className="text-xs text-dark-400 mb-2">Top Positive Correlations</div>
            <div className="space-y-1">
              {topCorrelationsData.top_positive.map((pair, idx) => (
                <div key={idx} className="text-sm text-dark-200">
                  <span className="text-green-400">{pair.a.replace('NIFTY_', '')}</span>
                  {' ↔ '}
                  <span className="text-green-400">{pair.b.replace('NIFTY_', '')}</span>
                  {' '}
                  <span className="text-dark-400">({pair.corr.toFixed(2)})</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-dark-700 rounded-lg p-3">
            <div className="text-xs text-dark-400 mb-2">Top Negative Correlations</div>
            <div className="space-y-1">
              {topCorrelationsData.top_negative.length > 0 ? (
                topCorrelationsData.top_negative.map((pair, idx) => (
                  <div key={idx} className="text-sm text-dark-200">
                    <span className="text-red-400">{pair.a.replace('NIFTY_', '')}</span>
                    {' ↔ '}
                    <span className="text-red-400">{pair.b.replace('NIFTY_', '')}</span>
                    {' '}
                    <span className="text-dark-400">({pair.corr.toFixed(2)})</span>
                  </div>
                ))
              ) : (
                <div className="text-sm text-dark-400">No significant negative correlations</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full Matrix - Collapsible */}
      {showFullMatrix && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-dark-700">
                  <th className="px-2 py-2 text-left font-medium text-dark-300"></th>
                  {sectorList.map((sector) => (
                    <th
                      key={sector}
                      className="px-2 py-2 text-left font-medium text-dark-300 whitespace-nowrap"
                      style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
                    >
                      {sector.replace('NIFTY_', '')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sectorList.map((sector1) => (
                  <tr key={sector1} className="border-b border-dark-700">
                    <td className="px-2 py-2 font-medium text-dark-300 whitespace-nowrap bg-dark-700">
                      {sector1.replace('NIFTY_', '')}
                    </td>
                    {sectorList.map((sector2) => {
                      const cellData = matrixData.find(
                        (d) => d.sector1 === sector1 && d.sector2 === sector2
                      );
                      const value = cellData?.value || 0;
                      const color = getColor(value);
                      return (
                        <td
                          key={`${sector1}-${sector2}`}
                          className="px-2 py-2 text-center"
                          style={{
                            backgroundColor: `${color}20`,
                            border: `1px solid ${color}40`,
                          }}
                        >
                          <div
                            className="inline-block px-2 py-1 rounded text-xs font-medium"
                            style={{
                              backgroundColor: color,
                              color: 'white',
                            }}
                          >
                            {value.toFixed(2)}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 flex items-center justify-center gap-4 text-xs text-dark-300">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
              <span>High (&gt;0.8)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3b82f6' }}></div>
              <span>Moderate (0.5-0.8)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#94a3b8' }}></div>
              <span>Low (0-0.5)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
              <span>Negative</span>
            </div>
          </div>
        </>
      )}

      {!showFullMatrix && (
        <div className="text-center py-4 text-dark-400 text-sm">
          Click "Show Full Matrix" to view the complete correlation matrix
        </div>
      )}
    </div>
  );
}

export default CorrelationMatrix;

