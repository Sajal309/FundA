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
    if (!forecast) return '';
    if (forecast.forecast_3m_label === 'UP') return 'border-green-500/50';
    if (forecast.forecast_3m_label === 'DOWN') return 'border-red-500/50';
    return 'border-yellow-500/50';
  };

  return (
    <div
      className={`p-4 rounded-lg border-2 cursor-pointer hover:shadow-lg transition-shadow bg-dark-800 border-dark-600 ${getColorClass()}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-dark-100">{sector.name}</h3>
        <span className="text-sm text-dark-400">
          {sector.latest_close > 0 ? sector.latest_close.toLocaleString('en-IN', {
            maximumFractionDigits: 0,
          }) : 'N/A'}
        </span>
      </div>

      {sector.sparkline && sector.sparkline.length > 0 && sector.sparkline[0] > 0 ? (
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
      ) : (
        <div className="h-16 mb-2 flex items-center justify-center text-dark-500 text-xs">
          No data available
        </div>
      )}

      <div className="flex items-center justify-between text-sm mb-2 text-dark-300">
        {sector.latest_close > 0 ? (
          <>
            <span
              className={
                sector.ret_1m > 0 ? 'text-green-400' : sector.ret_1m < 0 ? 'text-red-400' : 'text-dark-500'
              }
            >
              1M: {sector.ret_1m > 0 ? '+' : ''}
              {sector.ret_1m.toFixed(2)}%
            </span>
            {forecast && (
              <span
                className={`font-medium ${
                  forecast.forecast_3m_label === 'UP'
                    ? 'text-green-400'
                    : forecast.forecast_3m_label === 'DOWN'
                    ? 'text-red-400'
                    : 'text-yellow-400'
                }`}
              >
                {forecast.forecast_3m_label}
              </span>
            )}
          </>
        ) : (
          <span className="text-dark-500 text-xs">Data pending</span>
        )}
      </div>

      {/* Valuation & Sentiment Tags */}
      <div className="flex items-center gap-2 text-xs">
        {sector.valuation_pe !== null && sector.valuation_pe !== undefined && (
          <div className="flex items-center gap-1">
            <span className="text-dark-500">P/E:</span>
            <span className={`font-medium ${
              sector.valuation_state === 'cheap' ? 'text-green-400' :
              sector.valuation_state === 'expensive' ? 'text-red-400' :
              'text-dark-400'
            }`}>
              {sector.valuation_pe.toFixed(2)}x
            </span>
            {sector.valuation_state && (
              <span className={`px-1.5 py-0.5 rounded text-xs ${
                sector.valuation_state === 'cheap' ? 'bg-green-900/20 text-green-400' :
                sector.valuation_state === 'expensive' ? 'bg-red-900/20 text-red-400' :
                'bg-dark-700 text-dark-300'
              }`}>
                {sector.valuation_state}
              </span>
            )}
          </div>
        )}
        {sector.sentiment_score_7d !== null && sector.sentiment_score_7d !== undefined && (
          <div className="flex items-center gap-1 ml-auto">
            <span className={`text-lg ${
              sector.sentiment_score_7d > 65 ? 'text-green-400' :
              sector.sentiment_score_7d > 40 ? 'text-dark-400' :
              'text-red-400'
            }`}>
              {sector.sentiment_score_7d > 65 ? '🙂' :
               sector.sentiment_score_7d > 40 ? '😐' : '☹️'}
            </span>
            <span className="text-dark-400 text-xs">
              {sector.sentiment_score_7d.toFixed(2)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default SectorTile;

