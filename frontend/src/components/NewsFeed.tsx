import { useQuery } from 'react-query';
import { api } from '../api/client';

interface NewsFeedProps {
  sectorId?: string;
  limit?: number;
}

function NewsFeed({ sectorId, limit = 10 }: NewsFeedProps) {
  const { data, isLoading, error } = useQuery(
    ['news-feed', sectorId, limit],
    () => api.getLatestNews(sectorId, limit),
    { 
      refetchInterval: 300000,
      retry: 2,
      onError: (err) => console.error('News feed error:', err)
    }
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Latest News</h3>
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Latest News</h3>
        <div className="text-red-500">Error loading news: {String(error)}</div>
      </div>
    );
  }

  if (!data || !data.headlines || data.headlines.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Latest News</h3>
        <div className="text-gray-500">No headlines available</div>
      </div>
    );
  }

  const getSentimentColor = (score: number | null) => {
    if (score === null) return 'text-gray-500';
    if (score > 0.1) return 'text-green-600';
    if (score < -0.1) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSentimentLabel = (score: number | null) => {
    if (score === null) return 'Neutral';
    if (score > 0.1) return 'Positive';
    if (score < -0.1) return 'Negative';
    return 'Neutral';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">
        Latest News {sectorId && `(${sectorId.replace('NIFTY_', '')})`}
      </h3>
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {data.headlines.map((headline, idx) => (
          <div key={idx} className="border-b border-gray-200 pb-4 last:border-b-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-1">{headline.headline}</h4>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{headline.source}</span>
                  {headline.published_at && (
                    <span>{new Date(headline.published_at).toLocaleDateString()}</span>
                  )}
                  {headline.sector_tags && headline.sector_tags.length > 0 && (
                    <span className="text-blue-600">
                      {headline.sector_tags.map(t => t.replace('NIFTY_', '')).join(', ')}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                {headline.sentiment_score !== null && (
                  <div className={`text-sm font-medium ${getSentimentColor(headline.sentiment_score)}`}>
                    {getSentimentLabel(headline.sentiment_score)}
                  </div>
                )}
                {headline.url && (
                  <a
                    href={headline.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Read →
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NewsFeed;

