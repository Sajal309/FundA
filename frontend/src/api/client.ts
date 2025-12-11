import axios from 'axios';

// API URL configuration:
// - If VITE_API_URL is set, use it (for local development: http://localhost:8000)
// - If not set, use empty string (relative URL) for ngrok setup (goes through Vite proxy)
const envApiUrl = import.meta.env.VITE_API_URL;
const API_URL = envApiUrl || ''; // Empty string = relative URL = uses Vite proxy for ngrok

console.log('API Client Config:', {
  VITE_API_URL: envApiUrl,
  API_URL: API_URL,
  isLocal: envApiUrl && envApiUrl.includes('localhost'),
  isNgrok: !envApiUrl || envApiUrl === ''
});

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for better error handling
client.interceptors.response.use(
  (response) => {
    console.log('API Response:', {
      url: response.config?.url,
      status: response.status,
      dataType: typeof response.data,
      isArray: Array.isArray(response.data),
      dataLength: Array.isArray(response.data) ? response.data.length : 'N/A',
    });
    return response;
  },
  (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

export interface SectorSummary {
  sector_id: string;
  name: string;
  latest_close: number;
  ret_1m: number;
  ret_1w: number;
  sparkline: number[];
  valuation_pe?: number | null;
  valuation_state?: 'cheap' | 'fair' | 'expensive' | null;
  sentiment_score_7d?: number | null;
}

export interface ForecastDriver {
  driver: string;
  value: any;
  impact: string;
}

export interface ForecastResponse {
  sector_id: string;
  date: string;
  forecast_3m_label: string;
  prob_up: number;
  prob_neutral: number;
  prob_down: number;
  expected_return_pct: number;
  top_drivers: ForecastDriver[];
  quarter_score?: number | null;
  drivers?: Record<string, { score: number; detail: string }> | null;
  derivatives_sentiment?: {
    label: string;
    pcr_oi: number | null;
    oi_change_1d: number | null;
    iv_index: number | null;
    explanation: string;
  } | null;
}

export interface QuarterOutlookSector {
  sector_id: string;
  name: string;
  quarter_score: number;
  label: string;  // "Strong", "Neutral", or "Weak"
  forecast_3m_label: string;
  expected_return_pct: number;
}

export interface QuarterOutlookResponse {
  as_of: string;
  sectors: QuarterOutlookSector[];
}

export interface TimeseriesPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SectorTrends {
  trend: string;
  trend_strength: number;
  volatility_regime: string;
  current_volatility: number | null;
  avg_volatility: number | null;
  price_change_pct: number;
}

export interface FlowsAnalysis {
  total_fii_net: number;
  total_dii_net: number;
  avg_daily_fii: number;
  avg_daily_dii: number;
  flows_by_date: Record<string, { fii: number; dii: number }>;
}

export interface OptionsAnalysis {
  current_pcr: number | null;
  avg_pcr: number | null;
  current_oi_change: number | null;
  avg_oi_change: number | null;
  current_iv: number | null;
  avg_iv: number | null;
  options_by_date: Array<{
    date: string;
    pcr_oi: number | null;
    oi_change_1d: number | null;
    iv_index: number | null;
  }>;
}

export interface SentimentAnalysis {
  current_sentiment_1d: number | null;
  current_sentiment_7d: number | null;
  avg_sentiment_1d: number | null;
  avg_sentiment_7d: number | null;
  sentiment_trend: string;
  sentiment_by_date: Array<{
    date: string;
    sentiment_1d: number | null;
    sentiment_7d: number | null;
    headline_count: number | null;
  }>;
}

export interface PerformanceMetrics {
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  current_rsi: number | null;
  total_return: number;
  avg_daily_return: number;
}

export interface SectorStrengthRanking {
  sector_id: string;
  total_return: number;
  momentum: number;
  volatility: number;
  strength_score: number;
}

export interface BetaMetrics {
  beta: number;
  correlation_to_market: number;
  alpha: number;
  market_return: number;
  sector_return: number;
}

export interface MacroSummary {
  usd_inr: number | null;
  usd_inr_change_pct: number | null;
  brent_crude: number | null;
  brent_change_pct: number | null;
  gold_price: number | null;
  gold_change_pct: number | null;
  us_10y_yield: number | null;
  us_10y_change: number | null;
  date: string | null;
}

export interface NewsHeadline {
  headline: string;
  source: string;
  published_at: string | null;
  sentiment_score: number | null;
  sector_tags: string[];
  url: string | null;
  sentiment_label?: string;
}

export interface ApiMetadata {
  last_updated?: string | null;
  fetched_at?: string | null;
  is_live?: boolean;
  [key: string]: any;
}

export interface ApiResponse<T> {
  data: T;
  metadata?: ApiMetadata;
}

export const api = {
  getSectors: async (): Promise<SectorSummary[]> => {
    const response = await client.get('/api/v1/sectors');
    // Handle both old format (array) and new format (object with sectors and metadata)
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data.sectors || [];
  },

  getSectorsWithMetadata: async (): Promise<ApiResponse<SectorSummary[]>> => {
    const response = await client.get('/api/v1/sectors');
    if (Array.isArray(response.data)) {
      return {
        data: response.data,
        metadata: {
          fetched_at: new Date().toISOString(),
          is_live: false,
        },
      };
    }
    return {
      data: response.data.sectors || [],
      metadata: response.data.metadata,
    };
  },

  getSectorForecast: async (sectorId: string): Promise<ForecastResponse> => {
    const response = await client.get(`/api/v1/sectors/${sectorId}/forecast`);
    // Handle both old format (ForecastResponse) and new format (object with forecast and metadata)
    if (response.data.forecast) {
      return response.data.forecast;
    }
    return response.data;
  },

  getSectorForecastWithMetadata: async (sectorId: string): Promise<ApiResponse<ForecastResponse>> => {
    const response = await client.get(`/api/v1/sectors/${sectorId}/forecast`);
    if (response.data.forecast) {
      return {
        data: response.data.forecast,
        metadata: response.data.metadata,
      };
    }
    return {
      data: response.data,
      metadata: {
        fetched_at: new Date().toISOString(),
        is_live: false,
      },
    };
  },

  getSectorTimeseries: async (
    sectorId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<TimeseriesPoint[]> => {
    const params: any = {};
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    const response = await client.get(`/api/v1/sectors/${sectorId}/timeseries`, { params });
    return response.data;
  },

  // Analytics endpoints
  getSectorTrends: async (sectorId: string, lookbackDays: number = 30): Promise<SectorTrends> => {
    const response = await client.get(`/api/v1/analytics/sectors/${sectorId}/trends`, {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getFlowsAnalysis: async (sectorId?: string, lookbackDays: number = 30): Promise<FlowsAnalysis> => {
    const params: any = { lookback_days: lookbackDays };
    if (sectorId) params.sector_id = sectorId;
    const response = await client.get('/api/v1/analytics/flows', { params });
    return response.data;
  },

  getOptionsAnalysis: async (underlying: string, lookbackDays: number = 30): Promise<OptionsAnalysis> => {
    const response = await client.get(`/api/v1/analytics/options/${underlying}`, {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getSentimentAnalysis: async (sectorId: string, lookbackDays: number = 30): Promise<SentimentAnalysis> => {
    const response = await client.get(`/api/v1/analytics/sectors/${sectorId}/sentiment`, {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getSectorCorrelations: async (lookbackDays: number = 30): Promise<{ correlations: Record<string, number> }> => {
    const response = await client.get(`/api/v1/analytics/correlations`, {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getTopCorrelations: async (lookbackDays: number = 30, topN: number = 5): Promise<{
    as_of: string;
    top_positive: Array<{ a: string; b: string; corr: number }>;
    top_negative: Array<{ a: string; b: string; corr: number }>;
  }> => {
    const response = await client.get(`/api/v1/sectors/top-correlations`, {
      params: { lookback_days: lookbackDays, top_n: topN },
    });
    return response.data;
  },

  getPerformanceMetrics: async (sectorId: string, lookbackDays: number = 252): Promise<PerformanceMetrics> => {
    const response = await client.get(`/api/v1/analytics/sectors/${sectorId}/performance`, {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getSectorStrengthRanking: async (lookbackDays: number = 30): Promise<{ rankings: SectorStrengthRanking[] }> => {
    const response = await client.get('/api/v1/analytics/sectors/strength-ranking', {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getBetaAndCorrelation: async (sectorId: string, marketSectorId: string = 'NIFTY_50', lookbackDays: number = 252): Promise<BetaMetrics> => {
    const response = await client.get(`/api/v1/analytics/sectors/${sectorId}/beta`, {
      params: { market_sector_id: marketSectorId, lookback_days: lookbackDays },
    });
    return response.data;
  },

  getMacroSummary: async (lookbackDays: number = 30): Promise<MacroSummary> => {
    const response = await client.get('/api/v1/analytics/macro/summary', {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },

  getLatestNews: async (sectorId?: string, limit: number = 10): Promise<{ headlines: NewsHeadline[] }> => {
    const params: any = { limit };
    if (sectorId) params.sector_id = sectorId;
    const response = await client.get('/api/v1/analytics/news/latest', { params });
    return response.data;
  },

  getQuarterOutlook: async (): Promise<QuarterOutlookResponse> => {
    const response = await client.get('/api/v1/sectors/quarter-outlook');
    return response.data;
  },

  // Sector Rotation APIs
  getSectorRotationAvailableDates: async (level: 'sector' | 'industry' = 'sector'): Promise<string[]> => {
    const response = await client.get('/api/v1/sector-rotation/available-dates', {
      params: { level },
    });
    return response.data;
  },

  getSectorRotationBreadth: async (
    level: 'sector' | 'industry',
    date: string,
    metricType: 'mcap' | 'count' = 'mcap'
  ): Promise<{
    date: string;
    level: string;
    metric_type: string;
    data: Array<{
      id: string;
      name: string;
      mcap: number;
      stocks: number;
      metrics: {
        pct_rs55_gt0: number;
        pct_rsi_gt50: number;
        pct_above_sma20: number;
        pct_above_sma50: number;
        pct_above_sma100: number;
      };
    }>;
    metadata?: ApiMetadata;
  }> => {
    const response = await client.get('/api/v1/sector-rotation/breadth', {
      params: { level, date, metric_type: metricType },
    });
    return response.data;
  },

  getSectorRotationScores: async (
    level: 'sector' | 'industry',
    date: string
  ): Promise<{
    date: string;
    level: string;
    data: Array<{
      id: string;
      name: string;
      mcap: number;
      stocks: number;
      score_1m: number;
      score_3m: number;
      score_6m: number;
    }>;
    metadata?: ApiMetadata;
  }> => {
    const response = await client.get('/api/v1/sector-rotation/scores', {
      params: { level, date },
    });
    return response.data;
  },

  getSectorRotationDeliveries: async (
    level: 'sector' | 'industry',
    date: string
  ): Promise<{
    date: string;
    level: string;
    data: Array<{
      id: string;
      name: string;
      stocks: number;
      mcap: number;
      mcap_change_abs: number;
      mcap_change_pct: number;
      traded_value: number;
      traded_value_avg: number;
      traded_value_multiple: number;
      delivery_value: number;
      delivery_value_avg: number;
      delivery_value_multiple: number;
    }>;
    metadata?: ApiMetadata;
  }> => {
    const response = await client.get('/api/v1/sector-rotation/deliveries', {
      params: { level, date },
    });
    return response.data;
  },

  getSectorRotationVWAP: async (
    level: 'sector' | 'industry',
    date: string
  ): Promise<{
    date: string;
    level: string;
    data: Array<{
      id: string;
      name: string;
      mcap: number;
      pct_mcap_price_above_vwap: number;
    }>;
    metadata?: ApiMetadata;
  }> => {
    const response = await client.get('/api/v1/sector-rotation/vwap', {
      params: { level, date },
    });
    return response.data;
  },

  // Stock Screener APIs
  getSectorScreener: async (
    sector: string,
    limit: number = 100
  ): Promise<{
    sector: string;
    label: string;
    columns: Array<{ field: string; label: string; tooltip?: string }>;
    rows: Array<Record<string, any>>;
    count: number;
    primarySort: { field: string; direction: string };
    secondarySort?: { field: string; direction: string };
    metadata?: ApiMetadata;
  }> => {
    const response = await client.get('/api/v1/sector-screener', {
      params: { sector, limit },
    });
    return response.data;
  },

  listSectorScreeners: async (): Promise<{
    screeners: Array<{ key: string; label: string; filterQuery: string }>;
    count: number;
  }> => {
    const response = await client.get('/api/v1/sector-screener/list');
    return response.data;
  },

  exportSectorScreener: async (sector: string, limit: number = 100): Promise<Blob> => {
    const response = await client.get('/api/v1/sector-screener/export', {
      params: { sector, limit },
      responseType: 'blob',
    });
    return response.data;
  },

  compareSectorScreeners: async (
    sectors: string[],
    limit: number = 50
  ): Promise<{
    as_of: string;
    sectors: Record<string, {
      label: string;
      count: number;
      top_5: Array<Record<string, any>>;
      primary_sort_field: string;
      error?: string;
    }>;
    count: number;
  }> => {
    const response = await client.get('/api/v1/sector-screener/compare', {
      params: { sectors: sectors.join(','), limit },
    });
    return response.data;
  },
};

export default client;

