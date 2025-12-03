import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SectorSummary {
  sector_id: string;
  name: string;
  latest_close: number;
  ret_1m: number;
  ret_1w: number;
  sparkline: number[];
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

export const api = {
  getSectors: async (): Promise<SectorSummary[]> => {
    const response = await client.get('/api/v1/sectors');
    return response.data;
  },

  getSectorForecast: async (sectorId: string): Promise<ForecastResponse> => {
    const response = await client.get(`/api/v1/sectors/${sectorId}/forecast`);
    return response.data;
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
    const response = await client.get('/api/v1/analytics/correlations', {
      params: { lookback_days: lookbackDays },
    });
    return response.data;
  },
};

export default client;

