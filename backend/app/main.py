"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import sectors, forecasts, metrics, analytics, earnings, backtest, sector_rotation, screener, live_data, breadth
from app.db import models, database

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="SectorView API",
    description="API for Indian market sector analysis and forecasting",
    version="1.0.0"
)

# CORS middleware
# Allow all origins for development (including ngrok)
# In production, restrict to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for ngrok and local development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sectors.router, prefix="/api/v1", tags=["sectors"])
app.include_router(forecasts.router, prefix="/api/v1", tags=["forecasts"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(earnings.router, prefix="/api/v1", tags=["earnings"])
app.include_router(backtest.router, prefix="/api/v1", tags=["backtest"])
app.include_router(sector_rotation.router, prefix="/api/v1", tags=["sector-rotation"])
app.include_router(screener.router, prefix="/api/v1", tags=["screener"])
app.include_router(live_data.router, prefix="/api/v1", tags=["live-data"])
app.include_router(breadth.router, prefix="/api/v1", tags=["breadth"])


@app.get("/healthz")
def health_check():
    """Health check endpoint."""
    from sqlalchemy import text
    try:
        # Simple DB connectivity check
        db = next(database.get_db())
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "SectorView API",
        "version": "1.0.0",
        "docs": "/docs"
    }

