import { useQuery } from 'react-query';
import { api } from '../api/client';

interface MarketSentimentData {
  date: string;
  india_vix: number | null;
  india_vix_percentile: number | null;
  index_pcr: number | null;
  breadth_nifty500_above_50dma: number | null;
  news_sentiment_score_7d: number | null;
  regime_label: string;
  vix_label: string;
  pcr_label: string;
  breadth_label: string;
  sentiment_label: string;
}

function MarketSentiment() {
  const { data, isLoading } = useQuery<MarketSentimentData>(
    'market-sentiment',
    async () => {
      // Use relative URL to go through Vite proxy
      const apiUrl = import.meta.env.VITE_API_URL && !import.meta.env.VITE_API_URL.includes('localhost')
        ? import.meta.env.VITE_API_URL
        : '';
      const response = await fetch(`${apiUrl}/api/v1/market-sentiment`);
      if (!response.ok) throw new Error('Failed to fetch market sentiment');
      return response.json();
    },
    { refetchInterval: 300000 }
  );

  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-4 border border-dark-700">
        <div className="text-dark-400">Loading market sentiment...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-dark-800 rounded-lg shadow-lg p-4 border border-dark-700">
        <div className="text-dark-400">No market sentiment data available</div>
      </div>
    );
  }

  const getRegimeColor = (regime: string): string => {
    if (regime === 'RISK-ON') return 'bg-green-900/20 text-green-400 border-green-600';
    if (regime === 'RISK-OFF') return 'bg-red-900/20 text-red-400 border-red-600';
    return 'bg-yellow-900/20 text-yellow-400 border-yellow-600';
  };

  const getVixColor = (vix: number | null): string => {
    if (vix === null) return 'text-dark-500';
    if (vix < 15) return 'text-green-400';
    if (vix < 20) return 'text-blue-400';
    if (vix < 25) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getPcrColor = (pcr: number | null): string => {
    if (pcr === null) return 'text-dark-500';
    if (pcr < 0.7) return 'text-green-400';
    if (pcr < 1.0) return 'text-blue-400';
    if (pcr < 1.3) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getBreadthColor = (breadth: number | null): string => {
    if (breadth === null) return 'text-dark-500';
    if (breadth >= 0.7) return 'text-green-400';
    if (breadth >= 0.5) return 'text-blue-400';
    if (breadth >= 0.3) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSentimentColor = (sentiment: number | null): string => {
    if (sentiment === null) return 'text-dark-500';
    if (sentiment >= 65) return 'text-green-400';
    if (sentiment >= 55) return 'text-blue-400';
    if (sentiment >= 45) return 'text-dark-400';
    if (sentiment >= 35) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-dark-800 rounded-lg shadow-lg p-4 border border-dark-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-100">Market Sentiment</h3>
        <span className="text-xs text-dark-400">{new Date(data.date).toLocaleDateString()}</span>
      </div>

      {/* Regime Label - Large Pill */}
      <div className="mb-4">
        <div className={`inline-flex items-center px-6 py-3 rounded-full border-2 font-bold text-lg ${getRegimeColor(data.regime_label)}`}>
          <span className="mr-2">
            {data.regime_label === 'RISK-ON' ? '📈' : data.regime_label === 'RISK-OFF' ? '📉' : '➡️'}
          </span>
          Market Regime: {data.regime_label}
        </div>
      </div>

      {/* Sentiment Indicators Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* VIX */}
        <div className="bg-dark-700 rounded-lg p-4 relative group">
          <div className="text-xs text-dark-400 mb-1 flex items-center">
            India VIX
            <span className="ml-1 text-dark-500 cursor-help" title="India VIX measures market volatility expectations. Lower values indicate calmer markets.">ℹ️</span>
          </div>
          <div className={`text-2xl font-bold ${getVixColor(data.india_vix)}`}>
            {data.india_vix !== null ? data.india_vix.toFixed(2) : 'N/A'}
          </div>
          <div className="text-xs text-dark-400 mt-1">
            {data.vix_label}
            {data.india_vix_percentile !== null && (
              <span className="ml-1">({(data.india_vix_percentile * 100).toFixed(2)}th %ile)</span>
            )}
          </div>
        </div>

        {/* PCR */}
        <div className="bg-dark-700 rounded-lg p-4 relative group">
          <div className="text-xs text-dark-400 mb-1 flex items-center">
            Put-Call Ratio
            <span className="ml-1 text-dark-500 cursor-help" title="Put-Call Ratio (PCR) measures options market sentiment. Lower values (&lt;0.7) indicate bullish sentiment, higher values (&gt;1.3) indicate bearish sentiment.">ℹ️</span>
          </div>
          <div className={`text-2xl font-bold ${getPcrColor(data.index_pcr)}`}>
            {data.index_pcr !== null ? data.index_pcr.toFixed(2) : 'N/A'}
          </div>
          <div className="text-xs text-dark-400 mt-1">{data.pcr_label}</div>
        </div>

        {/* Breadth */}
        <div className="bg-dark-700 rounded-lg p-4 relative group">
          <div className="text-xs text-dark-400 mb-1 flex items-center">
            Market Breadth
            <span className="ml-1 text-dark-500 cursor-help" title="Market Breadth measures how many stocks are participating in the trend. Higher values (&gt;60%) indicate broad market strength, lower values (&lt;40%) indicate narrow participation.">ℹ️</span>
          </div>
          <div className={`text-2xl font-bold ${getBreadthColor(data.breadth_nifty500_above_50dma)}`}>
            {data.breadth_nifty500_above_50dma !== null ? `${(data.breadth_nifty500_above_50dma * 100).toFixed(2)}%` : 'N/A'}
          </div>
          <div className="text-xs text-dark-400 mt-1">
            {data.breadth_label} (Nifty 500 above 50DMA)
          </div>
        </div>

        {/* News Sentiment */}
        <div className="bg-dark-700 rounded-lg p-4 relative group">
          <div className="text-xs text-dark-400 mb-1 flex items-center">
            News Sentiment
            <span className="ml-1 text-dark-500 cursor-help" title="News Sentiment measures the tone of financial news. Scores above 55 indicate positive sentiment, below 45 indicate negative sentiment. Based on 7-day rolling average.">ℹ️</span>
          </div>
          <div className={`text-2xl font-bold ${getSentimentColor(data.news_sentiment_score_7d)}`}>
            {data.news_sentiment_score_7d !== null ? data.news_sentiment_score_7d.toFixed(2) : 'N/A'}
          </div>
          <div className="text-xs text-dark-400 mt-1">
            {data.sentiment_label} (7-day avg)
          </div>
        </div>
      </div>

    </div>
  );
}

export default MarketSentiment;

