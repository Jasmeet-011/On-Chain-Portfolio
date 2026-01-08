# backend/debug_coingecko.py - Test CoinGecko API directly

import httpx
import json

def test_coingecko_direct():
    """Test CoinGecko API directly to see what's happening"""
    
    print("\n" + "="*60)
    print("🔍 TESTING COINGECKO API DIRECTLY")
    print("="*60)
    
    # Test 1: Simple price endpoint
    print("\nTest 1: Current price (simple endpoint)")
    print("-" * 60)
    
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "solana",
            "vs_currencies": "usd"
        }
        
        response = httpx.get(url, params=params, timeout=10.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Simple price API working!")
        else:
            print(f"❌ Failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Market chart endpoint (historical)
    print("\n\nTest 2: Historical prices (market_chart endpoint)")
    print("-" * 60)
    
    try:
        url = "https://api.coingecko.com/api/v3/coins/solana/market_chart"
        params = {
            "vs_currency": "usd",
            "days": 7,
            "interval": "hourly"
        }
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = httpx.get(url, params=params, timeout=15.0)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Historical data API working!")
            print(f"\nKeys in response: {list(data.keys())}")
            
            if 'prices' in data:
                prices = data['prices']
                print(f"Number of price points: {len(prices)}")
                print(f"\nFirst 3 prices:")
                for i, (timestamp, price) in enumerate(prices[:3]):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    print(f"  {i+1}. {dt}: ${price:.2f}")
            else:
                print("⚠️  No 'prices' key in response")
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"❌ Failed!")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check rate limits
    print("\n\nTest 3: Check rate limit headers")
    print("-" * 60)
    
    try:
        response = httpx.get(
            "https://api.coingecko.com/api/v3/ping",
            timeout=10.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"\nRate limit headers:")
        headers = dict(response.headers)
        for key, value in headers.items():
            if 'rate' in key.lower() or 'limit' in key.lower():
                print(f"  {key}: {value}")
        
        if response.status_code == 200:
            print("\n✅ CoinGecko API is reachable!")
        else:
            print(f"\n❌ Ping failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_coingecko_direct()
    
    print("\n" + "="*60)
    print("🎯 DIAGNOSIS")
    print("="*60)
    print("\nIf Test 1 works but Test 2 fails:")
    print("  → CoinGecko might need API key for historical data")
    print("  → Or rate limit exceeded")
    print("\nIf all tests fail:")
    print("  → Network/firewall issue")
    print("  → Try from different network")
    print("\nIf getting 429 errors:")
    print("  → Rate limited - wait a few minutes")