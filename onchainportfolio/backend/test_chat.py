# backend/test_chat.py

import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Sign in (CORRECT ENDPOINT)
print("🔐 Signing in...")
signin_response = requests.post(
    f"{BASE_URL}/auth/login",  # ✅ CORRECT: /auth/login
    json={
        "email": "j@gmail.com",
        "password": "Jaz1234"
    }
)

print(f"Status: {signin_response.status_code}")

if signin_response.status_code != 200:
    print(f"❌ Sign in failed!")
    print(f"Response: {signin_response.text}")
    exit()

# Step 2: Get token
response_data = signin_response.json()
print(f"\n✅ Signed in successfully!")
print(f"User: {response_data.get('user', {}).get('email')}")

token = response_data.get("access_token")
print(f"Token (first 50 chars): {token[:50]}...")

# Step 3: Test chat
print("\n💬 Testing chat endpoint...")
chat_response = requests.post(
    f"{BASE_URL}/v1/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "question": "How much SOL do I have?",
        "scope": "all"
    }
)

print(f"Chat Status: {chat_response.status_code}")

if chat_response.status_code == 200:
    print("✅ Chat successful!")
    chat_data = chat_response.json()
    print(f"\nAnswer: {chat_data.get('answer')}")
    print(f"\nWallet Results: {len(chat_data.get('wallet_results', []))} wallets")
    print(f"Portfolio Total: ${chat_data.get('portfolio', {}).get('total_usd_value', 0):.2f}")
else:
    print(f"❌ Chat failed!")
    print(f"Response: {chat_response.text}")