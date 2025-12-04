import { useQuery } from 'react-query';
import { api } from '../api/client';
import { useState, useEffect } from 'react';

interface VolatilityHeatmapProps {
  lookbackDays?: number;
}

function VolatilityHeatmap({ lookbackDays = 30 }: VolatilityHeatmapProps) {
  const { data: sectors } = useQuery('sectors', api.getSectors, { refetchInterval: 300000 });
  const [volatilityData, setVolatilityData] = useState<Array<{
    sector_id: string;
    name: string;
    volatility: number;
  }>>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!sectors || sectors.length === 0) {
      setIsLoading(false);
      return;
    }

    const fetchVolatilities = async () => {
      setIsLoading(true);
      try {
        const results = await Promise.all(
          sectors.map(async (sector) => {
            try {
              const metrics = await api.getPerformanceMetrics(sector.sector_id, lookbackDays);
              return {
                sector_id: sector.sector_id,
                name: sector.name,
                volatility: metrics.volatility,
              };
            } catch {
              return null;
            }
          })
        );
        
        const validData = results
          .filter((r): r is NonNullable<typeof r> => r !== null)
          .sort((a, b) => b.volatility - a.volatility);
        
        setVolatilityData(validData);
      } catch (error) {
        console.error('Error fetching volatility data:', error);
        setVolatilityData([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (sectors && sectors.length > 0) {
      fetchVolatilities();
    } else {
      setIsLoading(false);
    }
  }, [sectors, lookbackDays]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Volatility Heatmap ({lookbackDays} days)</h3>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (volatilityData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Volatility Heatmap</h3>
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  // Normalize volatility for color coding
  const maxVol = Math.max(...volatilityData.map(d => d.volatility));
  const minVol = Math.min(...volatilityData.map(d => d.volatility));
  const range = maxVol - minVol;

  const getColor = (volatility: number) => {
    if (range === 0) return 'bg-gray-300';
    const normalized = (volatility - minVol) / range;
    if (normalized > 0.75) return 'bg-red-500';
    if (normalized > 0.5) return 'bg-orange-400';
    if (normalized > 0.25) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  const getTextColor = (volatility: number) => {
    if (range === 0) return 'text-gray-800';
    const normalized = (volatility - minVol) / range;
    if (normalized > 0.5) return 'text-white';
    return 'text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Volatility Heatmap ({lookbackDays} days)</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {volatilityData.map((item) => (
          <div
            key={item.sector_id}
            className={`${getColor(item.volatility)} ${getTextColor(item.volatility)} rounded-lg p-4 text-center`}
          >
            <div className="font-semibold text-sm mb-1">{item.name}</div>
            <div className="text-lg font-bold">
              {(item.volatility * 100).toFixed(1)}%
            </div>
            <div className="text-xs opacity-90 mt-1">Annualized</div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-400 rounded"></div>
          <span>Low</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-400 rounded"></div>
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-400 rounded"></div>
          <span>High</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Very High</span>
        </div>
      </div>
    </div>
  );
}

export default VolatilityHeatmap;

