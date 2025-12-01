# Monitoring Recommendations for SectorView

This document outlines recommended monitoring and observability setup for production deployment (not implemented in MVP).

## Metrics to Collect

### Application Metrics

#### Backend Metrics
- **Request Rate**: Requests per second by endpoint
- **Request Latency**: P50, P95, P99 latencies by endpoint
- **Error Rate**: 4xx and 5xx error rates
- **Database Connection Pool**: Active connections, pool size
- **Database Query Performance**: Slow query count, query duration

#### Data Pipeline Metrics
- **Ingestion Success Rate**: Percentage of successful EOD data ingestions
- **Feature Computation Duration**: Time to compute features for all sectors
- **Forecast Generation Duration**: Time to generate forecasts for all sectors
- **Data Freshness**: Time since last successful data update per sector

#### Business Metrics
- **Sector Coverage**: Number of sectors with data
- **Forecast Distribution**: Count of UP/NEUTRAL/DOWN forecasts
- **Data Completeness**: Percentage of sectors with complete feature sets

### Infrastructure Metrics
- **CPU Usage**: Per container/service
- **Memory Usage**: Per container/service
- **Disk I/O**: Database disk usage, I/O wait
- **Network**: Request/response sizes

## Prometheus Metrics

### Example Metric Definitions

```yaml
# Example Prometheus scrape config
scrape_configs:
  - job_name: 'sectorview-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Custom Metrics to Expose

```python
# Example FastAPI metrics endpoint
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# Business metrics
sectors_with_data = Gauge('sectors_with_data_total', 'Number of sectors with data')
forecast_up_count = Gauge('forecasts_up_total', 'Number of UP forecasts')
forecast_neutral_count = Gauge('forecasts_neutral_total', 'Number of NEUTRAL forecasts')
forecast_down_count = Gauge('forecasts_down_total', 'Number of DOWN forecasts')

# Data pipeline metrics
ingestion_duration = Histogram('ingestion_duration_seconds', 'Data ingestion duration')
feature_computation_duration = Histogram('feature_computation_duration_seconds', 'Feature computation duration')
forecast_generation_duration = Histogram('forecast_generation_duration_seconds', 'Forecast generation duration')
```

## Grafana Dashboards

### Recommended Dashboards

1. **Application Overview**
   - Request rate and latency
   - Error rates
   - Active database connections
   - Service health status

2. **Data Pipeline Health**
   - Ingestion success/failure rates
   - Last successful data update per sector
   - Feature computation status
   - Forecast generation status

3. **Business Metrics**
   - Sector coverage over time
   - Forecast distribution (UP/NEUTRAL/DOWN)
   - Expected returns distribution
   - Top drivers frequency

4. **Infrastructure**
   - CPU/Memory usage per service
   - Database performance
   - Disk usage
   - Network I/O

### Example Dashboard Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Average forecast expected return
avg(forecast_expected_return_pct)

# Sectors with stale data (>24 hours)
time() - last_successful_ingestion_timestamp > 86400
```

## Logging

### Log Levels
- **ERROR**: Ingestion failures, forecast generation errors, database connection issues
- **WARN**: Missing data for sectors, feature computation warnings
- **INFO**: Successful ingestion, forecast generation, API requests
- **DEBUG**: Detailed feature calculations, query execution details

### Structured Logging

```python
import structlog

logger = structlog.get_logger()
logger.info(
    "forecast_generated",
    sector_id="NIFTY_BANK",
    forecast_label="UP",
    expected_return=4.5,
    duration_seconds=0.12
)
```

## Alerts

### Critical Alerts
- **Database Down**: No database connectivity for >1 minute
- **Ingestion Failure**: No successful ingestion for >24 hours
- **High Error Rate**: Error rate >5% for >5 minutes
- **Service Down**: Health check failing for >2 minutes

### Warning Alerts
- **Stale Data**: Any sector without data for >48 hours
- **High Latency**: P95 latency >2 seconds for >10 minutes
- **Low Forecast Coverage**: <80% of sectors have forecasts

### Example Alert Rules

```yaml
groups:
  - name: sectorview_alerts
    rules:
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL database is down"
          
      - alert: IngestionFailure
        expr: time() - last_successful_ingestion_timestamp > 86400
        for: 5m
        annotations:
          summary: "No successful data ingestion for 24 hours"
          
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate exceeds 5%"
```

## APM (Application Performance Monitoring)

### Recommended Tools
- **Sentry**: Error tracking and performance monitoring
- **Datadog APM**: Distributed tracing
- **New Relic**: Full-stack observability

### Key Traces to Instrument
- End-to-end request tracing
- Database query tracing
- Feature computation tracing
- Forecast generation tracing

## Health Checks

### Liveness Probe
- Endpoint: `GET /healthz`
- Checks: Database connectivity
- Frequency: Every 30 seconds

### Readiness Probe
- Endpoint: `GET /healthz`
- Checks: Database connectivity, data availability
- Frequency: Every 10 seconds

## Implementation Notes

These monitoring recommendations are **not implemented in the MVP**. To implement:

1. Add Prometheus client library to backend
2. Expose `/metrics` endpoint
3. Set up Prometheus server
4. Configure Grafana with Prometheus data source
5. Create dashboards using queries above
6. Set up alerting rules
7. Configure log aggregation (ELK stack or similar)

For MVP, basic logging to stdout is sufficient. See `backend/app/utils.py` for current logging setup.

