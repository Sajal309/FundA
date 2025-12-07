import { useQuery } from 'react-query';
import { api } from '../api/client';

interface AnalyticsWidgetProps {
  sectorId: string;
}

function AnalyticsWidget({ sectorId }: AnalyticsWidgetProps) {
  const { data: trends } = useQuery(
    ['trends-widget', sectorId],
    () => api.getSectorTrends(sectorId, 30),
    { enabled: !!sectorId }
  );

  const { data: flows } = useQuery(
    ['flows-widget', sectorId],
    () => api.getFlowsAnalysis(sectorId, 7),
    { enabled: !!sectorId }
  );

  const { data: sentiment } = useQuery(
    ['sentiment-widget', sectorId],
    () => api.getSentimentAnalysis(sectorId, 7),
    { enabled: !!sectorId }
  );

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-4 border border-dark-700">
      <h4 className="text-sm font-semibold mb-3 text-dark-100">
        {sectorId.replace('NIFTY_', '')} Analytics
      </h4>
      <div className="space-y-3">
        {trends && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-dark-400">Trend:</span>
            <span
              className={`font-medium ${
                trends.trend === 'uptrend'
                  ? 'text-green-400'
                  : trends.trend === 'downtrend'
                  ? 'text-red-400'
                  : 'text-yellow-400'
              }`}
            >
              {trends.trend}
            </span>
          </div>
        )}
        {flows && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-dark-400">FII (7d):</span>
            <span
              className={`font-medium ${
                flows.total_fii_net >= 0 ? 'text-green-400' : 'text-red-400'
              }`}
            >
              ₹{(flows.total_fii_net / 1000000).toFixed(2)} Cr
            </span>
          </div>
        )}
        {sentiment && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-dark-400">Sentiment:</span>
            <span
              className={`font-medium ${
                (sentiment.current_sentiment_7d || 0) >= 0
                  ? 'text-green-400'
                  : 'text-red-400'
              }`}
            >
              {sentiment.current_sentiment_7d !== null
                ? sentiment.current_sentiment_7d.toFixed(2)
                : 'N/A'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalyticsWidget;

