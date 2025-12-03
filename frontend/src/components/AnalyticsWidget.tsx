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
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-sm font-semibold mb-3 text-gray-700">
        {sectorId.replace('NIFTY_', '')} Analytics
      </h4>
      <div className="space-y-3">
        {trends && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Trend:</span>
            <span
              className={`font-medium ${
                trends.trend === 'uptrend'
                  ? 'text-green-600'
                  : trends.trend === 'downtrend'
                  ? 'text-red-600'
                  : 'text-yellow-600'
              }`}
            >
              {trends.trend}
            </span>
          </div>
        )}
        {flows && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">FII (7d):</span>
            <span
              className={`font-medium ${
                flows.total_fii_net >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              ₹{(flows.total_fii_net / 1000000).toFixed(1)} Cr
            </span>
          </div>
        )}
        {sentiment && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Sentiment:</span>
            <span
              className={`font-medium ${
                (sentiment.current_sentiment_7d || 0) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
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

