"""Test script to verify metadata integration works correctly."""

import asyncio
import json
from datetime import datetime
from agents.chat_agent import ChatAgent
from agents.metadata_agent import MetadataAgent
from graphs.state import ChatState
from tools.metadata_tools import LocationTool, TimezoneTool


async def test_metadata_integration():
    """Test that metadata system works with chat queries."""
    print("🧪 Testing Metadata Integration")
    print("=" * 50)
    
    # Test 1: MetadataAgent standalone
    print("\n1. Testing MetadataAgent standalone:")
    metadata_agent = MetadataAgent()
    
    test_state = ChatState(
        user_input="Find restaurants near me",
        current_agent="metadata_agent",
        session_id="test_session_123",
        ip_address="8.8.8.8",  # Google's IP for testing
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    try:
        result = await metadata_agent.process(test_state)
        metadata = result.get("metadata", {})
        print(f"✅ Metadata collected: {json.dumps(metadata, indent=2)}")
    except Exception as e:
        print(f"❌ MetadataAgent failed: {e}")
    
    # Test 2: ChatAgent with metadata tools
    print("\n2. Testing ChatAgent with metadata tools:")
    chat_agent = ChatAgent()
    
    # Check if metadata tools are available
    available_tools = chat_agent.get_available_tools()
    print(f"Available tools: {available_tools}")
    
    metadata_tools = ["timezone_tool", "location_tool", "datetime_tool", "user_agent_tool"]
    for tool in metadata_tools:
        if tool in available_tools:
            print(f"✅ {tool} is available")
        else:
            print(f"❌ {tool} is missing")
    
    # Test 3: Query enhancement
    print("\n3. Testing query enhancement:")
    test_queries = [
        "Find restaurants near me",
        "What's the weather today?",
        "Current time in my timezone",
        "Stores open now"
    ]
    
    # Mock state with metadata
    mock_state = {
        "metadata": {
            "user_metadata": {
                "location": {
                    "value": {
                        "city": "New York",
                        "country": "United States",
                        "lat": 40.7128,
                        "lon": -74.0060
                    }
                },
                "timezone": {
                    "value": "America/New_York"
                },
                "datetime": {
                    "value": "2024-01-15T14:30:00-05:00"
                }
            }
        }
    }
    
    for query in test_queries:
        try:
            enhanced_query = await chat_agent._enhance_query_with_metadata(query, mock_state)
            print(f"Original: {query}")
            print(f"Enhanced: {enhanced_query}")
            print()
        except Exception as e:
            print(f"❌ Query enhancement failed for '{query}': {e}")
    
    # Test 4: Individual metadata tools
    print("\n4. Testing individual metadata tools:")
    
    # Test LocationTool
    location_tool = LocationTool()
    try:
        location_result = await location_tool.execute(ip_address="8.8.8.8")
        print(f"✅ LocationTool result: {json.dumps(location_result, indent=2)}")
    except Exception as e:
        print(f"❌ LocationTool failed: {e}")
    
    # Test TimezoneTool
    timezone_tool = TimezoneTool()
    try:
        timezone_result = await timezone_tool.execute(ip_address="8.8.8.8")
        print(f"✅ TimezoneTool result: {json.dumps(timezone_result, indent=2)}")
    except Exception as e:
        print(f"❌ TimezoneTool failed: {e}")
    
    # Test 5: Full ChatAgent workflow
    print("\n5. Testing full ChatAgent workflow:")
    try:
        # Create a realistic state
        full_state = ChatState(
            user_input="Find restaurants near me",
            current_agent="chat_agent",
            session_id="test_session_full",
            ip_address="8.8.8.8",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            metadata={}
        )
        
        # Process through ChatAgent
        result = await chat_agent.process(full_state)
        
        print(f"✅ ChatAgent processed successfully")
        print(f"Final response: {result.get('final_response', 'No response')[:200]}...")
        
        # Check if metadata was collected
        metadata = result.get("metadata", {})
        if "user_metadata" in metadata:
            print(f"✅ Metadata was collected: {list(metadata['user_metadata'].keys())}")
        else:
            print(f"⚠️ No user metadata found in result")
            
        # Check if query was enhanced
        if "query_enhancement" in result:
            enhancement = result["query_enhancement"]
            print(f"✅ Query was enhanced:")
            print(f"  Original: {enhancement.get('original_query', 'N/A')}")
            print(f"  Enhanced: {enhancement.get('enhanced_query', 'N/A')}")
        else:
            print(f"⚠️ No query enhancement found")
            
    except Exception as e:
        print(f"❌ Full ChatAgent workflow failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Metadata Integration Test Complete")


async def test_specific_scenarios():
    """Test specific scenarios that should work with metadata."""
    print("\n🎯 Testing Specific Scenarios")
    print("=" * 50)
    
    chat_agent = ChatAgent()
    
    scenarios = [
        {
            "name": "Restaurant search with location",
            "query": "Find restaurants near me",
            "ip": "8.8.8.8",
            "expected_enhancement": "restaurants near me in"
        },
        {
            "name": "Weather query with location",
            "query": "What's the weather today?",
            "ip": "8.8.8.8", 
            "expected_enhancement": "weather today"
        },
        {
            "name": "Time query with timezone",
            "query": "What time is it?",
            "ip": "8.8.8.8",
            "expected_enhancement": "time"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        
        try:
            state = ChatState(
                user_input=scenario["query"],
                current_agent="metadata_agent",
                session_id=f"test_{scenario['name'].lower().replace(' ', '_')}",
                ip_address=scenario["ip"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                metadata={}
            )
            
            # Test metadata collection
            metadata_agent = MetadataAgent()
            metadata_result = await metadata_agent.process(state)
            
            if metadata_result.get("metadata"):
                print(f"✅ Metadata collected successfully")
                
                # Test query enhancement
                enhanced_query = await chat_agent._enhance_query_with_metadata(
                    scenario["query"], 
                    metadata_result
                )
                
                if enhanced_query != scenario["query"]:
                    print(f"✅ Query enhanced: {enhanced_query}")
                else:
                    print(f"⚠️ Query not enhanced (may be expected)")
                    
            else:
                print(f"❌ Failed to collect metadata")
                
        except Exception as e:
            print(f"❌ Scenario failed: {e}")


async def main():
    """Run all tests."""
    await test_metadata_integration()
    await test_specific_scenarios()
    
    print("\n🎉 All tests completed!")
    print("\nTo test with the actual API:")
    print("1. Start the server: python start_server.py")
    print("2. Send a POST request to /chat with:")
    print('   {"message": {"text": "Find restaurants near me"}, "session_id": "test123"}')
    print("3. Check the logs for metadata collection and query enhancement")


if __name__ == "__main__":
    asyncio.run(main())
