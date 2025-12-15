import httpx
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print(f"API Key loaded: {api_key[:10]}..." if api_key else "No API key found!")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

# Test with gemini-2.5-flash
model = "gemini-2.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

payload = {
    "contents": [
        {
            "parts": [
                {"text": "Say hello in one sentence"}
            ]
        }
    ]
}

try:
    with httpx.Client(timeout=30.0) as client:
        print(f"\n🔄 Testing Gemini API with model: {model}")
        print(f"URL: {url[:80]}...")
        
        response = client.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ Gemini API is working!")
            data = response.json()
            if "candidates" in data:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"AI Response: {text}")
        else:
            print(f"\n❌ Gemini API failed!")
            print(f"Error: {response.text}")
            
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()