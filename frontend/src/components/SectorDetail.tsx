import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { api, TimeseriesPoint, ForecastResponse } from '../api/client';
import PerformanceMetrics from './PerformanceMetrics';
import RiskMetrics from './RiskMetrics';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';

interface SectorDetailProps {
  sectorId: string;
  onClose: () => void;
}

function SectorDetail({ sectorId, onClose }: SectorDetailProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'options' | 'sentiment'>('overview');

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

  const { data: trends, isLoading: trendsLoading } = useQuery(
    ['trends', sectorId],
    () => api.getSectorTrends(sectorId, 30),
    { enabled: !!sectorId }
  );

  const { data: flows, isLoading: flowsLoading } = useQuery(
    ['flows', sectorId],
    () => api.getFlowsAnalysis(sectorId, 30),
    { enabled: !!sectorId }
  );

  const { data: sentiment, isLoading: sentimentLoading } = useQuery(
    ['sentiment', sectorId],
    () => api.getSentimentAnalysis(sectorId, 30),
    { enabled: !!sectorId }
  );

  // Map sector to underlying for options
  const underlyingMap: Record<string, string> = {
    'NIFTY_BANK': 'BANKNIFTY',
    'NIFTY_IT': 'NIFTY',
    'NIFTY_PHARMA': 'NIFTY',
    'NIFTY_FMCG': 'NIFTY',
    'NIFTY_AUTO': 'NIFTY',
  };
  const underlying = underlyingMap[sectorId] || 'NIFTY';

  const { data: options, isLoading: optionsLoading } = useQuery(
    ['options', underlying],
    () => api.getOptionsAnalysis(underlying, 30),
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
        volume: point.volume,
        ma20,
        ma50,
      };
    })
    .filter((d) => d.ma20 !== null) || [];

  // Prepare flows chart data
  const flowsChartData = flows?.flows_by_date
    ? Object.entries(flows.flows_by_date)
        .map(([date, data]) => ({
          date: date.split('T')[0],
          fii: data.fii / 1000000, // Convert to crores
          dii: data.dii / 1000000,
        }))
        .sort((a, b) => a.date.localeCompare(b.date))
    : [];

  // Prepare sentiment chart data
  const sentimentChartData = sentiment?.sentiment_by_date
    ? sentiment.sentiment_by_date.map((s) => ({
        date: s.date.split('T')[0],
        sentiment_1d: s.sentiment_1d || 0,
        sentiment_7d: s.sentiment_7d || 0,
        headlines: s.headline_count || 0,
      }))
    : [];

  // Prepare options chart data
  const optionsChartData = options?.options_by_date
    ? options.options_by_date.map((o) => ({
        date: o.date.split('T')[0],
        pcr: o.pcr_oi || 0,
        oi_change: o.oi_change_1d || 0,
        iv: o.iv_index || 0,
      }))
    : [];

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
          {/* Tabs */}
          <div className="mb-6 border-b border-gray-200">
            <nav className="flex space-x-8">
              {(['overview', 'analytics', 'options', 'sentiment', 'performance', 'risk'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
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

              {/* Trend Analysis */}
              {trends && (
                <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3">Trend Analysis</h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">Trend</div>
                      <div className={`text-lg font-bold ${
                        trends.trend === 'uptrend' ? 'text-green-600' :
                        trends.trend === 'downtrend' ? 'text-red-600' : 'text-yellow-600'
                      }`}>
                        {trends.trend}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Volatility</div>
                      <div className={`text-lg font-bold ${
                        trends.volatility_regime === 'high' ? 'text-red-600' :
                        trends.volatility_regime === 'low' ? 'text-green-600' : 'text-yellow-600'
                      }`}>
                        {trends.volatility_regime}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Price Change</div>
                      <div className={`text-lg font-bold ${
                        trends.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {trends.price_change_pct >= 0 ? '+' : ''}
                        {trends.price_change_pct.toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Current Vol</div>
                      <div className="text-lg font-bold">
                        {trends.current_volatility ? trends.current_volatility.toFixed(2) : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Avg Vol</div>
                      <div className="text-lg font-bold">
                        {trends.avg_volatility ? trends.avg_volatility.toFixed(2) : 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Price & Volume Chart */}
              {tsLoading ? (
                <div>Loading chart data...</div>
              ) : chartData.length > 0 ? (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Price & Volume</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <ComposedChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="close"
                        fill="#3b82f6"
                        stroke="#3b82f6"
                        name="Close Price"
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="ma20"
                        stroke="#10b981"
                        strokeWidth={1.5}
                        name="MA20"
                        dot={false}
                        strokeDasharray="5 5"
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="ma50"
                        stroke="#f59e0b"
                        strokeWidth={1.5}
                        name="MA50"
                        dot={false}
                        strokeDasharray="5 5"
                      />
                      <Bar
                        yAxisId="right"
                        dataKey="volume"
                        fill="#94a3b8"
                        name="Volume"
                        opacity={0.3}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div>No chart data available</div>
              )}
            </>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && flows && (
            <div>
              <h3 className="text-lg font-semibold mb-4">FII/DII Flows Analysis</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Total FII Net</div>
                  <div className={`text-xl font-bold ${
                    flows.total_fii_net >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ₹{(flows.total_fii_net / 1000000).toFixed(2)} Cr
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Total DII Net</div>
                  <div className={`text-xl font-bold ${
                    flows.total_dii_net >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ₹{(flows.total_dii_net / 1000000).toFixed(2)} Cr
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Avg Daily FII</div>
                  <div className={`text-lg font-bold ${
                    flows.avg_daily_fii >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ₹{(flows.avg_daily_fii / 1000000).toFixed(2)} Cr
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Avg Daily DII</div>
                  <div className={`text-lg font-bold ${
                    flows.avg_daily_dii >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    ₹{(flows.avg_daily_dii / 1000000).toFixed(2)} Cr
                  </div>
                </div>
              </div>
              {flowsChartData.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={flowsChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="fii" fill="#10b981" name="FII (Cr)" />
                    <Bar dataKey="dii" fill="#3b82f6" name="DII (Cr)" />
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>
          )}

          {/* Options Tab */}
          {activeTab === 'options' && options && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Options Analysis ({underlying})</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Current PCR</div>
                  <div className="text-xl font-bold">
                    {options.current_pcr ? options.current_pcr.toFixed(2) : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">
                    Avg: {options.avg_pcr ? options.avg_pcr.toFixed(2) : 'N/A'}
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">OI Change 1D</div>
                  <div className={`text-xl font-bold ${
                    (options.current_oi_change || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {options.current_oi_change ? (options.current_oi_change >= 0 ? '+' : '') + options.current_oi_change.toFixed(2) + '%' : 'N/A'}
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">IV Index</div>
                  <div className="text-xl font-bold">
                    {options.current_iv ? (options.current_iv * 100).toFixed(2) + '%' : 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">
                    Avg: {options.avg_iv ? (options.avg_iv * 100).toFixed(2) + '%' : 'N/A'}
                  </div>
                </div>
              </div>
              {optionsChartData.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={optionsChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="pcr" stroke="#8b5cf6" strokeWidth={2} name="PCR" />
                    <Bar yAxisId="right" dataKey="oi_change" fill="#f59e0b" name="OI Change %" />
                    <Line yAxisId="left" type="monotone" dataKey="iv" stroke="#ef4444" strokeWidth={2} name="IV %" />
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>
          )}

          {/* Sentiment Tab */}
          {activeTab === 'sentiment' && sentiment && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Sentiment Analysis</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Current (1D)</div>
                  <div className={`text-xl font-bold ${
                    (sentiment.current_sentiment_1d || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sentiment.current_sentiment_1d !== null ? sentiment.current_sentiment_1d.toFixed(2) : 'N/A'}
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Current (7D)</div>
                  <div className={`text-xl font-bold ${
                    (sentiment.current_sentiment_7d || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sentiment.current_sentiment_7d !== null ? sentiment.current_sentiment_7d.toFixed(2) : 'N/A'}
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Trend</div>
                  <div className={`text-xl font-bold ${
                    sentiment.sentiment_trend === 'improving' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sentiment.sentiment_trend}
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-sm text-gray-600">Avg (7D)</div>
                  <div className={`text-lg font-bold ${
                    (sentiment.avg_sentiment_7d || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {sentiment.avg_sentiment_7d !== null ? sentiment.avg_sentiment_7d.toFixed(2) : 'N/A'}
                  </div>
                </div>
              </div>
              {sentimentChartData.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={sentimentChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="sentiment_1d" stroke="#10b981" strokeWidth={2} name="Sentiment 1D" />
                    <Line yAxisId="left" type="monotone" dataKey="sentiment_7d" stroke="#3b82f6" strokeWidth={2} name="Sentiment 7D" />
                    <Bar yAxisId="right" dataKey="headlines" fill="#94a3b8" name="Headlines" opacity={0.5} />
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>
          )}

          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div>
              <PerformanceMetrics sectorId={sectorId} lookbackDays={252} />
            </div>
          )}

          {/* Risk Tab */}
          {activeTab === 'risk' && (
            <div>
              <RiskMetrics sectorId={sectorId} marketSectorId="NIFTY_50" lookbackDays={252} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SectorDetail;

