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

interface CorrelationMatrixProps {
  lookbackDays?: number;
}

function CorrelationMatrix({ lookbackDays = 30 }: CorrelationMatrixProps) {
  const { data, isLoading } = useQuery(
    ['correlations', lookbackDays],
    () => api.getSectorCorrelations(lookbackDays),
    { refetchInterval: 300000 } // Refetch every 5 minutes
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Sector Correlations</h3>
        <div className="text-center py-8 text-dark-400">Loading correlations...</div>
      </div>
    );
  }

  if (!data || !data.correlations) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Sector Correlations</h3>
        <div className="text-center py-8 text-dark-400">No correlation data available</div>
      </div>
    );
  }

  // Parse correlations into matrix format
  const correlations = data.correlations;
  const sectorPairs = Object.keys(correlations);
  
  // Extract unique sectors
  const sectors = new Set<string>();
  sectorPairs.forEach((pair) => {
    const [s1, s2] = pair.split('_');
    sectors.add(s1);
    sectors.add(s2);
  });
  
  const sectorList = Array.from(sectors).sort();
  
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
      <h3 className="text-lg font-semibold mb-4 text-dark-100">Sector Correlation Matrix ({lookbackDays} days)</h3>
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
    </div>
  );
}

export default CorrelationMatrix;

