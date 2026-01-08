# backend/test_history.py - Test history endpoints

import requests
import json

BASE_URL = "http://localhost:8000"

def test_price_history():
    """Test GET /v1/history/prices/history/{symbol}"""
    print("\n" + "="*60)
    print("TEST 1: Price History for SOL (7 days)")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/v1/history/prices/history/SOL",
        params={"days": 7, "chain": "solana"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Symbol: {data['symbol']}")
        print(f"Current Price: ${data['current_price']}")
        print(f"24h Change: ${data['change_24h']} ({data['change_percent']}%)")
        print(f"Period Change: ${data['period_change']} ({data['period_change_percent']}%)")
        print(f"Data Points: {data['data_points']}")
        print(f"\nFirst 3 prices:")
        for price in data['prices'][:3]:
            from datetime import datetime
            dt = datetime.fromtimestamp(price['timestamp'])
            print(f"  {dt}: ${price['price']}")
    else:
        print(f"\n❌ FAILED!")
        print(f"Response: {response.text}")


def test_price_history_apt():
    """Test GET /v1/history/prices/history/APT"""
    print("\n" + "="*60)
    print("TEST 2: Price History for APT (30 days)")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/v1/history/prices/history/APT",
        params={"days": 30, "chain": "aptos"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Symbol: {data['symbol']}")
        print(f"Current Price: ${data['current_price']}")
        print(f"Period Change: ${data['period_change']} ({data['period_change_percent']}%)")
        print(f"Data Points: {data['data_points']}")
    else:
        print(f"\n❌ FAILED!")
        print(f"Response: {response.text}")


def test_price_history_24h():
    """Test 24h price history"""
    print("\n" + "="*60)
    print("TEST 3: Price History for SOL (24 hours)")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/v1/history/prices/history/SOL",
        params={"days": 1}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Data Points: {data['data_points']} (should be ~288 for 5-min intervals)")
        print(f"Period Change: ${data['period_change']} ({data['period_change_percent']}%)")
    else:
        print(f"\n❌ FAILED!")
        print(f"Response: {response.text}")


def test_portfolio_history():
    """Test POST /v1/history/portfolio/history"""
    print("\n" + "="*60)
    print("TEST 4: Portfolio History (requires auth)")
    print("="*60)
    
    # First, sign in
    print("Signing in...")
    signin_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "j@gmail.com", "password": "Jaz1234"}
    )
    
    if signin_response.status_code != 200:
        print(f"❌ Sign in failed: {signin_response.text}")
        return
    
    token = signin_response.json()["access_token"]
    print(f"✅ Signed in, got token")
    
    # Now test portfolio history
    response = requests.post(
        f"{BASE_URL}/v1/history/portfolio/history",
        params={"days": 7},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Current Value: ${data['current_value']}")
        print(f"Period Change: ${data['period_change']} ({data['period_change_percent']}%)")
        print(f"Data Points: {data['data_points']}")
        print(f"\nFirst 3 values:")
        for value in data['values'][:3]:
            from datetime import datetime
            dt = datetime.fromtimestamp(value['timestamp'])
            print(f"  {dt}: ${value['value']}")
    else:
        print(f"\n❌ FAILED!")
        print(f"Response: {response.text}")


def test_cache_validation():
    """Test that caching works"""
    print("\n" + "="*60)
    print("TEST 5: Cache Validation")
    print("="*60)
    
    import time
    
    print("First request (should hit CoinGecko)...")
    start = time.time()
    response1 = requests.get(f"{BASE_URL}/v1/history/prices/history/SOL?days=7")
    time1 = time.time() - start
    print(f"Time: {time1:.2f}s")
    
    print("\nSecond request (should hit cache)...")
    start = time.time()
    response2 = requests.get(f"{BASE_URL}/v1/history/prices/history/SOL?days=7")
    time2 = time.time() - start
    print(f"Time: {time2:.2f}s")
    
    if time2 < time1 * 0.5:  # Cache should be at least 2x faster
        print(f"\n✅ Cache working! Second request was {time1/time2:.1f}x faster")
    else:
        print(f"\n⚠️  Cache might not be working properly")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING HISTORY SERVICE")
    print("="*60)
    print("\nMake sure backend is running: uvicorn app.main:app --reload")
    input("Press Enter to start tests...")
    
    # Run all tests
    test_price_history()
    test_price_history_apt()
    test_price_history_24h()
    test_portfolio_history()
    test_cache_validation()
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Check backend logs for [HISTORY] messages")
    print("2. Verify cache is working (see TEST 5 results)")
    print("3. Ready to build frontend charts!")