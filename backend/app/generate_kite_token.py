"""Helper script to generate Kite Connect access token from request token."""
import sys
import os
from kiteconnect import KiteConnect

def generate_access_token(request_token: str, api_key: str, api_secret: str):
    """
    Generate access token from request token.
    
    Usage:
        python -m app.generate_kite_token <request_token>
    
    Or set environment variables:
        KITE_API_KEY, KITE_API_SECRET, and pass request_token as argument
    """
    if not request_token:
        print("❌ Error: Request token required")
        print("\nTo get request token:")
        print("1. Visit: https://kite.trade/connect/login?api_key=j9cwrgsejy2vodgv&v=3")
        print("2. Login and authorize")
        print("3. Copy the request_token from the redirect URL")
        print("4. Run: python -m app.generate_kite_token <request_token>")
        sys.exit(1)
    
    # Get API credentials
    api_key = api_key or os.getenv('KITE_API_KEY')
    api_secret = api_secret or os.getenv('KITE_API_SECRET')
    
    if not api_key:
        print("❌ Error: KITE_API_KEY not set")
        sys.exit(1)
    
    if not api_secret:
        print("❌ Error: KITE_API_SECRET not set")
        sys.exit(1)
    
    try:
        kite = KiteConnect(api_key=api_key)
        
        # Generate session
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        print("\n✅ Access token generated successfully!")
        print(f"\nAccess Token: {access_token}")
        print(f"\nAdd this to your docker-compose.yml or .env file:")
        print(f"KITE_ACCESS_TOKEN={access_token}")
        
        # Test the token
        kite.set_access_token(access_token)
        profile = kite.profile()
        print(f"\n✅ Token verified! Connected as: {profile.get('user_name', 'N/A')}")
        
        return access_token
        
    except Exception as e:
        print(f"\n❌ Error generating access token: {type(e).__name__}: {str(e)}")
        if "Invalid" in str(e) or "expired" in str(e).lower():
            print("\n⚠️  The request token may be invalid or expired.")
            print("Please generate a new request token by visiting the login URL again.")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.generate_kite_token <request_token>")
        print("\nTo get request token:")
        print("1. Visit: https://kite.trade/connect/login?api_key=j9cwrgsejy2vodgv&v=3")
        print("2. Login and authorize")
        print("3. Copy the request_token from the redirect URL")
        sys.exit(1)
    
    request_token = sys.argv[1]
    generate_access_token(request_token, None, None)

