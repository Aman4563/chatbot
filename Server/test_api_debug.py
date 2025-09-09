"""Test API with debugging."""

import asyncio
import httpx
import json


async def test_api():
    """Test the API with debugging."""
    base_url = "http://localhost:8000"
    
    payload = {
        "message": {
            "text": "Find restaurants near me"
        },
        "session_id": "test123",
        "stream": False  # Disable streaming to get JSON response
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Forwarded-For": "8.8.8.8"  # Test with Google's IP
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat",
                json=payload,
                headers=headers
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text[:500]}...")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print("✅ API Response received")
                    print(f"Response: {result.get('response', 'No response')[:200]}...")
                    
                    # Check metadata
                    metadata = result.get('metadata', {})
                    print(f"Metadata keys: {list(metadata.keys())}")
                    
                    if 'user_metadata' in metadata:
                        user_metadata = metadata['user_metadata']
                        print(f"User metadata keys: {list(user_metadata.keys())}")
                        
                        # Check for location data
                        if 'location' in user_metadata:
                            location = user_metadata['location']
                            print(f"✅ Location found: {location}")
                        else:
                            print("❌ No location data found")
                            
                        # Check for timezone data
                        if 'timezone' in user_metadata:
                            timezone = user_metadata['timezone']
                            print(f"✅ Timezone found: {timezone}")
                        else:
                            print("❌ No timezone data found")
                    else:
                        print("❌ No user metadata found")
                except Exception as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Raw response: {response.text}")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_api())
