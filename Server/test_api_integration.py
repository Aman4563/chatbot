"""Test the actual API integration with metadata."""

import asyncio
import json
import httpx
from datetime import datetime


async def test_api_with_metadata():
    """Test the API with metadata integration."""
    print("🌐 Testing API Integration with Metadata")
    print("=" * 50)
    
    # Test data
    test_queries = [
        "Find restaurants near me",
        "What's the weather today?",
        "Current time in my timezone",
        "Stores open now"
    ]
    
    base_url = "http://localhost:8000"
    
    for query in test_queries:
        print(f"\n📋 Testing query: '{query}'")
        
        try:
            # Create request payload
            payload = {
                "message": {
                    "text": query
                },
                "session_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "model_name": "gemini-2.0-flash",
                "stream": False
            }
            
            # Send request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{base_url}/chat",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ API Response received")
                    print(f"Response: {result.get('response', 'No response')[:200]}...")
                    
                    # Check metadata
                    metadata = result.get('metadata', {})
                    if metadata:
                        print(f"✅ Metadata found: {list(metadata.keys())}")
                        
                        # Check for user metadata
                        user_metadata = metadata.get('user_metadata', {})
                        if user_metadata:
                            print(f"✅ User metadata collected: {list(user_metadata.keys())}")
                            
                            # Check for location data
                            if 'location' in user_metadata:
                                location = user_metadata['location']
                                print(f"📍 Location: {location}")
                            
                            # Check for timezone data
                            if 'timezone' in user_metadata:
                                timezone = user_metadata['timezone']
                                print(f"🕐 Timezone: {timezone}")
                        else:
                            print(f"⚠️ No user metadata found")
                    else:
                        print(f"⚠️ No metadata found in response")
                        
                else:
                    print(f"❌ API Error: {response.status_code}")
                    print(f"Error: {response.text}")
                    
        except httpx.ConnectError:
            print(f"❌ Connection Error: Server not running at {base_url}")
            print("Please start the server with: python start_server.py")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 API Integration Test Complete")


async def test_metadata_agent_directly():
    """Test the metadata agent directly via API."""
    print("\n🔧 Testing MetadataAgent Directly")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        payload = {
            "message": "Find restaurants near me",
            "session_id": f"metadata_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/agents/metadata_agent",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ MetadataAgent Response received")
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ MetadataAgent Error: {response.status_code}")
                print(f"Error: {response.text}")
                
    except httpx.ConnectError:
        print(f"❌ Connection Error: Server not running at {base_url}")
        print("Please start the server with: python start_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all API tests."""
    print("🚀 Starting API Integration Tests")
    print("Make sure the server is running: python start_server.py")
    print()
    
    await test_api_with_metadata()
    await test_metadata_agent_directly()
    
    print("\n🎉 All API tests completed!")
    print("\nTo test manually:")
    print("1. Start server: python start_server.py")
    print("2. Send POST to http://localhost:8000/chat")
    print('3. Body: {"message": {"text": "Find restaurants near me"}, "session_id": "test123"}')


if __name__ == "__main__":
    asyncio.run(main())
