import { useQuery } from 'react-query';
import { api } from '../api/client';
import { useState, useEffect, useMemo } from 'react';

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

interface VolatilityHeatmapProps {
  lookbackDays?: number;
}

function VolatilityHeatmap({ lookbackDays = 30 }: VolatilityHeatmapProps) {
  const { data: sectorsResponse } = useQuery('sectors', api.getSectors, { refetchInterval: 300000 });
  
  // Handle both array response and object response with metadata
  const sectors = Array.isArray(sectorsResponse) ? sectorsResponse : (sectorsResponse?.sectors || []);
  
  // Filter to canonical sectors only
  const canonicalSectors = useMemo(() => {
    if (!sectors || !Array.isArray(sectors)) return [];
    return sectors.filter(s => CANONICAL_SECTORS.includes(s.sector_id));
  }, [sectors]);
  
  const [volatilityData, setVolatilityData] = useState<Array<{
    sector_id: string;
    name: string;
    volatility: number;
  }>>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!canonicalSectors || canonicalSectors.length === 0) {
      setIsLoading(false);
      return;
    }

    const fetchVolatilities = async () => {
      setIsLoading(true);
      try {
        const results = await Promise.all(
          canonicalSectors.map(async (sector) => {
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

    if (canonicalSectors && canonicalSectors.length > 0) {
      fetchVolatilities();
    } else {
      setIsLoading(false);
    }
  }, [canonicalSectors, lookbackDays]);

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Volatility Heatmap ({lookbackDays} days)</h3>
        <div className="text-dark-400">Loading...</div>
      </div>
    );
  }

  if (volatilityData.length === 0) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
        <h3 className="text-lg font-semibold mb-4 text-dark-100">Volatility Heatmap</h3>
        <div className="text-dark-400">No data available</div>
      </div>
    );
  }

  // Map volatility to categories (annualized %)
  const getVolatilityCategory = (vol: number): { label: string; color: string; textColor: string } => {
    const volPercent = vol * 100; // Convert to percentage
    if (volPercent < 15) {
      return { label: 'Low', color: 'bg-green-500', textColor: 'text-white' };
    } else if (volPercent < 25) {
      return { label: 'Medium', color: 'bg-yellow-400', textColor: 'text-dark-900' };
    } else if (volPercent < 35) {
      return { label: 'High', color: 'bg-orange-400', textColor: 'text-white' };
    } else {
      return { label: 'Very High', color: 'bg-red-500', textColor: 'text-white' };
    }
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 border border-dark-700">
      <h3 className="text-lg font-semibold mb-4 text-dark-100">Volatility Heatmap ({lookbackDays} days)</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {volatilityData.map((item) => {
          const category = getVolatilityCategory(item.volatility);
          return (
            <div
              key={item.sector_id}
              className={`${category.color} ${category.textColor} rounded-lg p-4 text-center`}
            >
              <div className="font-semibold text-sm mb-1">{item.name.replace('Nifty ', '')}</div>
              <div className="text-lg font-bold">
                {(item.volatility * 100).toFixed(1)}%
              </div>
              <div className="text-xs opacity-90 mt-1">{category.label} (30d annualized)</div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex items-center justify-center gap-4 text-xs text-dark-400">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Low (&lt;15%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-400 rounded"></div>
          <span>Medium (15-25%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-400 rounded"></div>
          <span>High (25-35%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Very High (&gt;35%)</span>
        </div>
      </div>
    </div>
  );
}

export default VolatilityHeatmap;

