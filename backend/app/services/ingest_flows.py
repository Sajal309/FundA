"""FII/DII flow data ingestion service."""
import pandas as pd
import sys
import argparse
from pathlib import Path
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.db import crud, schemas, database
from app.utils import logger


def ingest_flows_from_csv(file_path: str, db: Session) -> int:
    """
    Ingest FII/DII flow data from CSV file.
    
    Expected CSV format:
    date,source,ticker,fii_buy,fii_sell,dii_buy,dii_sell
    
    Args:
        file_path: Path to CSV file
        db: Database session
        
    Returns:
        Number of records ingested
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_cols = ['date']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Fill optional columns with None if missing
        for col in ['source', 'ticker', 'fii_buy', 'fii_sell', 'dii_buy', 'dii_sell']:
            if col not in df.columns:
                df[col] = None
        
        count = 0
        for _, row in df.iterrows():
            try:
                flow_data = schemas.FIIDIIDailyCreate(
                    date=row['date'],
                    source=str(row.get('source', 'NSE')),
                    ticker=row.get('ticker') if pd.notna(row.get('ticker')) else None,
                    fii_buy=int(row['fii_buy']) if pd.notna(row.get('fii_buy')) else None,
                    fii_sell=int(row['fii_sell']) if pd.notna(row.get('fii_sell')) else None,
                    dii_buy=int(row['dii_buy']) if pd.notna(row.get('dii_buy')) else None,
                    dii_sell=int(row['dii_sell']) if pd.notna(row.get('dii_sell')) else None,
                )
                crud.create_fii_dii_daily(db, flow_data)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest flow row {row.get('date', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully ingested {count} flow records from {file_path}")
        return count
        
    except Exception as e:
        logger.error(f"Error ingesting flows from CSV {file_path}: {e}")
        raise


def aggregate_flows_by_sector(db: Session, target_date: Optional[date] = None) -> int:
    """
    Aggregate FII/DII flows by sector using constituent weights.
    
    Args:
        db: Database session
        target_date: Date to aggregate for (defaults to latest)
        
    Returns:
        Number of sector flow records created/updated
    """
    from app.db import models
    
    # Get all sectors
    sectors = crud.get_all_sectors(db)
    
    # Get flows for the target date
    if target_date:
        flows = crud.get_fii_dii_daily(db, date=target_date)
    else:
        # Get latest date with flows
        latest_flow = db.query(models.FIIDIIDaily).order_by(
            models.FIIDIIDaily.date.desc()
        ).first()
        if not latest_flow:
            logger.warning("No flow data found to aggregate")
            return 0
        target_date = latest_flow.date
        flows = crud.get_fii_dii_daily(db, date=target_date)
    
    if not flows:
        logger.warning(f"No flow data found for date {target_date}")
        return 0
    
    # Get constituents for all sectors
    constituents_by_sector = {}
    for sector_id in sectors:
        consts = crud.get_sector_constituents(db, sector_id, limit=1000)
        constituents_by_sector[sector_id] = {c.ticker: c.weight_pct for c in consts}
    
    count = 0
    for sector_id in sectors:
        try:
            # Aggregate flows by sector using constituent weights
            fii_net = 0
            dii_net = 0
            fii_gross = 0
            dii_gross = 0
            
            sector_consts = constituents_by_sector.get(sector_id, {})
            
            for flow in flows:
                if flow.ticker and flow.ticker in sector_consts:
                    weight = sector_consts[flow.ticker] / 100.0  # Convert % to decimal
                    
                    if flow.fii_buy and flow.fii_sell:
                        fii_net += int((flow.fii_buy - flow.fii_sell) * weight)
                        fii_gross += int((flow.fii_buy + flow.fii_sell) * weight)
                    
                    if flow.dii_buy and flow.dii_sell:
                        dii_net += int((flow.dii_buy - flow.dii_sell) * weight)
                        dii_gross += int((flow.dii_buy + flow.dii_sell) * weight)
            
            # Also include aggregate flows (ticker=None) if available
            for flow in flows:
                if flow.ticker is None:
                    if flow.fii_buy and flow.fii_sell:
                        # For aggregate, we can use a simple average across sectors
                        # or skip if we have ticker-level data
                        if not sector_consts:  # Only use aggregate if no constituents
                            fii_net = (flow.fii_buy - flow.fii_sell) if flow.fii_buy and flow.fii_sell else 0
                            fii_gross = (flow.fii_buy + flow.fii_sell) if flow.fii_buy and flow.fii_sell else 0
                    
                    if flow.dii_buy and flow.dii_sell:
                        if not sector_consts:
                            dii_net = (flow.dii_buy - flow.dii_sell) if flow.dii_buy and flow.dii_sell else 0
                            dii_gross = (flow.dii_buy + flow.dii_sell) if flow.dii_buy and flow.dii_sell else 0
            
            # Create or update sector flows
            sector_flow = schemas.SectorFlowsDailyCreate(
                date=target_date,
                sector_id=sector_id,
                fii_net_inr=fii_net if fii_net != 0 else None,
                dii_net_inr=dii_net if dii_net != 0 else None,
                fii_gross=fii_gross if fii_gross != 0 else None,
                dii_gross=dii_gross if dii_gross != 0 else None,
            )
            crud.create_or_update_sector_flows_daily(db, sector_flow)
            count += 1
            
        except Exception as e:
            logger.error(f"Failed to aggregate flows for {sector_id}: {e}")
            continue
    
    logger.info(f"Aggregated flows for {count} sectors on {target_date}")
    return count


def fetch_flows_from_nse(target_date: date) -> dict:
    """
    Fetch FII/DII flows from NSE (placeholder for production implementation).
    
    Args:
        target_date: Trading date
        
    Returns:
        Dictionary with flow data
    """
    # TODO: Implement actual NSE API integration
    # NSE provides FII/DII reports at: https://www.nseindia.com/reports/fii-dii
    logger.warning(f"fetch_flows_from_nse not implemented yet for {target_date}")
    return {}


def main():
    """CLI entrypoint for flow ingestion."""
    parser = argparse.ArgumentParser(description='Ingest FII/DII flow data')
    parser.add_argument('--source', required=True, help='Path to CSV file or source identifier')
    parser.add_argument('--aggregate', action='store_true', help='Aggregate flows by sector after ingestion')
    parser.add_argument('--date', help='Specific date to aggregate for (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    db = next(database.get_db())
    
    try:
        if args.source.endswith('.csv'):
            count = ingest_flows_from_csv(args.source, db)
            print(f"Ingested {count} flow records")
            
            if args.aggregate:
                target_date = None
                if args.date:
                    target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
                agg_count = aggregate_flows_by_sector(db, target_date)
                print(f"Aggregated flows for {agg_count} sectors")
        else:
            logger.error(f"Unsupported source: {args.source}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Flow ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

