import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { api, TimeseriesPoint, ForecastResponse } from '../api/client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface SectorDetailProps {
  sectorId: string;
  onClose: () => void;
}

function SectorDetail({ sectorId, onClose }: SectorDetailProps) {
  const { data: timeseries, isLoading: tsLoading } = useQuery(
    ['timeseries', sectorId],
    () => api.getSectorTimeseries(sectorId),
    { enabled: !!sectorId }
  );

  const { data: forecast, isLoading: forecastLoading } = useQuery(
    ['forecast', sectorId],
    () => api.getSectorForecast(sectorId),
    { enabled: !!sectorId }
  );

  // Calculate MA20 and MA50 from timeseries
  const chartData = timeseries
    ?.map((point) => {
      const index = timeseries.indexOf(point);
      const closes = timeseries.slice(0, index + 1).map((p) => p.close);
      const ma20 =
        closes.length >= 20
          ? closes.slice(-20).reduce((a, b) => a + b, 0) / 20
          : null;
      const ma50 =
        closes.length >= 50
          ? closes.slice(-50).reduce((a, b) => a + b, 0) / 50
          : null;
      return {
        date: point.date,
        close: point.close,
        ma20,
        ma50,
      };
    })
    .filter((d) => d.ma20 !== null) || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            {sectorId.replace('NIFTY_', '')} Sector Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {/* Forecast Section */}
          {forecastLoading ? (
            <div className="mb-6">Loading forecast...</div>
          ) : forecast ? (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-3">3-Month Forecast</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <div className="text-sm text-gray-600">Forecast</div>
                  <div
                    className={`text-xl font-bold ${
                      forecast.forecast_3m_label === 'UP'
                        ? 'text-green-600'
                        : forecast.forecast_3m_label === 'DOWN'
                        ? 'text-red-600'
                        : 'text-yellow-600'
                    }`}
                  >
                    {forecast.forecast_3m_label}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Expected Return</div>
                  <div
                    className={`text-xl font-bold ${
                      forecast.expected_return_pct >= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {forecast.expected_return_pct >= 0 ? '+' : ''}
                    {forecast.expected_return_pct.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Prob. UP</div>
                  <div className="text-xl font-bold">
                    {(forecast.prob_up * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Prob. DOWN</div>
                  <div className="text-xl font-bold">
                    {(forecast.prob_down * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {forecast.top_drivers && forecast.top_drivers.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">Top Drivers</h4>
                  <ul className="space-y-1">
                    {forecast.top_drivers.map((driver, idx) => (
                      <li key={idx} className="text-sm">
                        <span
                          className={
                            driver.impact === 'positive'
                              ? 'text-green-600'
                              : driver.impact === 'negative'
                              ? 'text-red-600'
                              : 'text-gray-600'
                          }
                        >
                          {driver.impact === 'positive' ? '↑' : driver.impact === 'negative' ? '↓' : '→'}{' '}
                        </span>
                        {driver.driver}: {String(driver.value)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}

          {/* Timeseries Chart */}
          {tsLoading ? (
            <div>Loading chart data...</div>
          ) : chartData.length > 0 ? (
            <div>
              <h3 className="text-lg font-semibold mb-3">Price Chart with Moving Averages</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Close Price"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="ma20"
                    stroke="#10b981"
                    strokeWidth={1.5}
                    name="MA20"
                    dot={false}
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="ma50"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    name="MA50"
                    dot={false}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div>No chart data available</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SectorDetail;

