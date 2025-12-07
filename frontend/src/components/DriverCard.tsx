import { ForecastResponse } from '../api/client';

interface DriverCardProps {
  forecast: ForecastResponse;
  onClose?: () => void;
}

function DriverCard({ forecast, onClose }: DriverCardProps) {
  const drivers = forecast.drivers || {};
  const quarterScore = forecast.quarter_score;

  const getScoreColor = (score: number): string => {
    if (score >= 0.5) return '#10b981'; // green
    if (score >= 0.2) return '#3b82f6'; // blue
    if (score >= -0.2) return '#6b7280'; // gray
    if (score >= -0.5) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 0.5) return 'Strong Positive';
    if (score >= 0.2) return 'Positive';
    if (score >= -0.2) return 'Neutral';
    if (score >= -0.5) return 'Negative';
    return 'Strong Negative';
  };

  const pillarNames: Record<string, string> = {
    momentum: 'Momentum',
    breadth: 'Breadth',
    flows: 'Flows',
    earnings: 'Earnings',
    valuation: 'Valuation',
    sentiment: 'Sentiment',
    macro: 'Macro Overlay',
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-6 max-w-2xl mx-auto border border-dark-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-dark-100">{forecast.sector_id.replace('NIFTY_', 'Nifty ')}</h2>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              forecast.forecast_3m_label === 'UP' ? 'bg-green-900/20 text-green-400' :
              forecast.forecast_3m_label === 'DOWN' ? 'bg-red-900/20 text-red-400' :
              'bg-dark-700 text-dark-300'
            }`}>
              {forecast.forecast_3m_label}
            </span>
            {quarterScore !== null && quarterScore !== undefined && (
              <span className="text-lg font-semibold text-dark-300">
                QuarterScore: {quarterScore >= 0 ? '+' : ''}{quarterScore.toFixed(2)}
              </span>
            )}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-dark-400 hover:text-dark-300 text-2xl font-bold"
          >
            ×
          </button>
        )}
      </div>

      {/* Forecast Summary */}
      <div className="mb-6 p-4 bg-dark-700 rounded-lg">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-sm text-dark-400">Probability UP</div>
            <div className="text-xl font-bold text-green-400">{(forecast.prob_up * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-sm text-dark-400">Probability NEUTRAL</div>
            <div className="text-xl font-bold text-dark-300">{(forecast.prob_neutral * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div className="text-sm text-dark-400">Probability DOWN</div>
            <div className="text-xl font-bold text-red-400">{(forecast.prob_down * 100).toFixed(0)}%</div>
          </div>
        </div>
        <div className="mt-4 text-center">
          <div className="text-sm text-dark-400">Expected Return (3M)</div>
          <div className={`text-2xl font-bold ${forecast.expected_return_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {forecast.expected_return_pct >= 0 ? '+' : ''}{forecast.expected_return_pct.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Driver Breakdown */}
      {Object.keys(drivers).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4 text-dark-100">Driver Breakdown</h3>
          <div className="space-y-4">
            {Object.entries(drivers).map(([pillar, contrib]) => {
              const score = contrib.score || 0;
              const detail = contrib.detail || '';
              const color = getScoreColor(score);
              const label = getScoreLabel(score);
              
              // Normalize score to -1 to +1 for bar visualization
              const normalizedScore = Math.max(-1, Math.min(1, score));
              const barWidth = Math.abs(normalizedScore) * 100;
              const isPositive = normalizedScore >= 0;

              return (
                <div key={pillar} className="border border-dark-600 rounded-lg p-4 bg-dark-700">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-dark-100">
                      {pillarNames[pillar] || pillar.charAt(0).toUpperCase() + pillar.slice(1)}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold" style={{ color }}>
                        {score >= 0 ? '+' : ''}{score.toFixed(2)}
                      </span>
                      <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: color + '20', color }}>
                        {label}
                      </span>
                    </div>
                  </div>
                  
                  {/* Visual Bar */}
                  <div className="mb-2 h-2 bg-dark-600 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${isPositive ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${barWidth}%`, marginLeft: isPositive ? '0' : `${100 - barWidth}%` }}
                    />
                  </div>
                  
                  <div className="text-sm text-dark-300">{detail}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top Drivers (fallback if drivers not available) */}
      {Object.keys(drivers).length === 0 && forecast.top_drivers && forecast.top_drivers.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4 text-dark-100">Top Drivers</h3>
          <div className="space-y-2">
            {forecast.top_drivers.map((driver, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-dark-700 rounded">
                <div className="flex-1">
                  <div className="font-medium text-dark-100">{driver.driver}</div>
                  <div className="text-sm text-dark-300">{String(driver.value)}</div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  driver.impact === 'positive' ? 'bg-green-900/30 text-green-400' :
                  driver.impact === 'negative' ? 'bg-red-900/30 text-red-400' :
                  'bg-dark-600 text-dark-300'
                }`}>
                  {driver.impact}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Derivatives Sentiment */}
      {forecast.derivatives_sentiment && (
        <div className="mt-6 pt-4 border-t border-dark-600">
          <h4 className="text-sm font-semibold mb-2 text-dark-100">Derivatives Sentiment</h4>
          <div className="p-3 bg-dark-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-dark-100">
                {forecast.derivatives_sentiment.label}
              </span>
              <div className="flex items-center gap-3 text-xs text-dark-300">
                {forecast.derivatives_sentiment.pcr_oi !== null && (
                  <span>PCR: {forecast.derivatives_sentiment.pcr_oi.toFixed(2)}</span>
                )}
                {forecast.derivatives_sentiment.oi_change_1d !== null && (
                  <span>OI: {forecast.derivatives_sentiment.oi_change_1d >= 0 ? '+' : ''}{forecast.derivatives_sentiment.oi_change_1d.toFixed(2)}%</span>
                )}
              </div>
            </div>
            <div className="text-xs text-dark-300">
              {forecast.derivatives_sentiment.explanation || 'No explanation available'}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-dark-600 text-xs text-dark-400">
        <div>Date: {new Date(forecast.date).toLocaleDateString()}</div>
        <div className="mt-1">
          QuarterScore is a composite metric combining momentum, breadth, flows, earnings, valuation, sentiment, and macro factors.
        </div>
      </div>
    </div>
  );
}

export default DriverCard;

