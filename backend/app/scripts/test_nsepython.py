"""Test script for nsepython service."""
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services import nsepython_service
from app.utils import logger


def main():
    """Test nsepython service functions."""
    print("="*80)
    print("🧪 TESTING NSEPYTHON SERVICE")
    print("="*80)
    
    if not nsepython_service.is_available():
        print("❌ nsepython not available. Install with: pip install nsepythonserver")
        return
    
    print("\n1. Testing Sector Data Fetch...")
    try:
        sector_data = nsepython_service.fetch_sector_data('NIFTY 50')
        if sector_data:
            print(f"   ✅ Fetched sector data for NIFTY 50")
            if 'data' in sector_data and sector_data['data']:
                print(f"   Records: {len(sector_data['data'])}")
                if len(sector_data['data']) > 0:
                    sample = sector_data['data'][0]
                    print(f"   Sample record keys: {list(sample.keys()) if isinstance(sample, dict) else 'N/A'}")
        else:
            print("   ⚠️  No data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Testing Stock Quote...")
    try:
        quote = nsepython_service.fetch_stock_quote('RELIANCE')
        if quote:
            print(f"   ✅ Fetched quote for RELIANCE")
            # Print some key fields
            if isinstance(quote, dict):
                print(f"   Quote keys: {list(quote.keys())[:10]}")
        else:
            print("   ⚠️  No quote returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. Testing FII/DII Data...")
    try:
        fii_dii = nsepython_service.fetch_fii_dii_data()
        if fii_dii:
            print(f"   ✅ Fetched FII/DII data")
            if isinstance(fii_dii, dict):
                print(f"   Data keys: {list(fii_dii.keys())}")
        else:
            print("   ⚠️  No FII/DII data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Testing Index Constituents...")
    try:
        constituents = nsepython_service.fetch_index_constituents('NIFTY 50')
        if constituents:
            print(f"   ✅ Fetched {len(constituents)} constituents for NIFTY 50")
        else:
            print("   ⚠️  No constituents returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n5. Testing Market Status...")
    try:
        status = nsepython_service.fetch_market_status()
        if status:
            print(f"   ✅ Fetched market status")
            if isinstance(status, dict):
                print(f"   Status keys: {list(status.keys())}")
        else:
            print("   ⚠️  No status returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("✅ Testing complete!")
    print("="*80)


if __name__ == "__main__":
    main()

