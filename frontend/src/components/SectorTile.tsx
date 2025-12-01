import { SectorSummary, ForecastResponse } from '../api/client';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface SectorTileProps {
  sector: SectorSummary;
  forecast?: ForecastResponse;
  onClick: () => void;
}

function SectorTile({ sector, forecast, onClick }: SectorTileProps) {
  const sparklineData = sector.sparkline.map((value, index) => ({
    value,
    index,
  }));

  const getColorClass = () => {
    if (!forecast) return 'bg-gray-100';
    if (forecast.forecast_3m_label === 'UP') return 'bg-green-50 border-green-200';
    if (forecast.forecast_3m_label === 'DOWN') return 'bg-red-50 border-red-200';
    return 'bg-yellow-50 border-yellow-200';
  };

  return (
    <div
      className={`p-4 rounded-lg border-2 cursor-pointer hover:shadow-lg transition-shadow ${getColorClass()}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900">{sector.name}</h3>
        <span className="text-sm text-gray-600">
          {sector.latest_close.toLocaleString('en-IN', {
            maximumFractionDigits: 0,
          })}
        </span>
      </div>

      <div className="h-16 mb-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={sparklineData}>
            <Line
              type="monotone"
              dataKey="value"
              stroke={forecast?.forecast_3m_label === 'UP' ? '#10b981' : forecast?.forecast_3m_label === 'DOWN' ? '#ef4444' : '#f59e0b'}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-sm">
        <span
          className={
            sector.ret_1m >= 0 ? 'text-green-600' : 'text-red-600'
          }
        >
          1M: {sector.ret_1m >= 0 ? '+' : ''}
          {sector.ret_1m.toFixed(2)}%
        </span>
        {forecast && (
          <span
            className={`font-medium ${
              forecast.forecast_3m_label === 'UP'
                ? 'text-green-600'
                : forecast.forecast_3m_label === 'DOWN'
                ? 'text-red-600'
                : 'text-yellow-600'
            }`}
          >
            {forecast.forecast_3m_label}
          </span>
        )}
      </div>
    </div>
  );
}

export default SectorTile;

