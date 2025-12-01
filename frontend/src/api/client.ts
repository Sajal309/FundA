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
};

export default client;

