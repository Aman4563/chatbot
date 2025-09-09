"""Demo script showing how the metadata system works."""

import asyncio
import json
from datetime import datetime
from agents.metadata_agent import MetadataAgent
from tools.metadata_tools import TimezoneTool, LocationTool, DateTimeTool, UserAgentTool
from graphs.state import AgentState


async def demo_metadata_tools():
    """Demonstrate individual metadata tools."""
    print("=== Metadata Tools Demo ===\n")
    
    # Test TimezoneTool
    print("1. Testing TimezoneTool:")
    timezone_tool = TimezoneTool()
    
    # Test with browser timezone
    result = await timezone_tool.execute(timezone_input="America/New_York")
    print(f"Browser timezone result: {json.dumps(result, indent=2)}\n")
    
    # Test with IP address
    result = await timezone_tool.execute(ip_address="8.8.8.8")
    print(f"IP timezone result: {json.dumps(result, indent=2)}\n")
    
    # Test LocationTool
    print("2. Testing LocationTool:")
    location_tool = LocationTool()
    
    # Test with IP address
    result = await location_tool.execute(ip_address="8.8.8.8")
    print(f"IP location result: {json.dumps(result, indent=2)}\n")
    
    # Test with coordinates
    result = await location_tool.execute(latitude=40.7128, longitude=-74.0060)
    print(f"Coordinates location result: {json.dumps(result, indent=2)}\n")
    
    # Test DateTimeTool
    print("3. Testing DateTimeTool:")
    datetime_tool = DateTimeTool()
    
    result = await datetime_tool.execute(timezone_str="America/New_York")
    print(f"DateTime result: {json.dumps(result, indent=2)}\n")
    
    # Test UserAgentTool
    print("4. Testing UserAgentTool:")
    user_agent_tool = UserAgentTool()
    
    result = await user_agent_tool.execute(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    print(f"UserAgent result: {json.dumps(result, indent=2)}\n")


async def demo_metadata_agent():
    """Demonstrate the MetadataAgent."""
    print("=== MetadataAgent Demo ===\n")
    
    # Create metadata agent
    metadata_agent = MetadataAgent()
    
    # Test different scenarios
    test_cases = [
        {
            "name": "Local search query",
            "state": AgentState(
                user_input="Find restaurants near me",
                session_id="test_session_1",
                ip_address="8.8.8.8",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        },
        {
            "name": "Time-based query",
            "state": AgentState(
                user_input="What's the current time?",
                session_id="test_session_2",
                timezone_input="America/New_York"
            )
        },
        {
            "name": "Location-based query",
            "state": AgentState(
                user_input="Weather in my area",
                session_id="test_session_3",
                latitude=40.7128,
                longitude=-74.0060
            )
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}:")
        print(f"Input: {test_case['state']['user_input']}")
        
        try:
            result_state = await metadata_agent.process(test_case['state'])
            metadata = result_state.get("metadata", {})
            print(f"Metadata collected: {json.dumps(metadata, indent=2)}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")


async def demo_query_enhancement():
    """Demonstrate query enhancement with metadata."""
    print("=== Query Enhancement Demo ===\n")
    
    # Simulate a chat agent with metadata
    from agents.chat_agent import ChatAgent
    
    chat_agent = ChatAgent()
    
    # Test query enhancement
    test_queries = [
        "Find restaurants near me",
        "What's the weather today?",
        "Current time in my timezone",
        "Stores open now"
    ]
    
    # Mock state with metadata
    mock_state = {
        "user_input": "",
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
        print(f"Original query: {query}")
        mock_state["user_input"] = query
        
        try:
            enhanced_query = await chat_agent._enhance_query_with_metadata(query, mock_state)
            print(f"Enhanced query: {enhanced_query}")
            
            enhancement_info = mock_state.get("query_enhancement", {})
            print(f"Enhancements applied: {enhancement_info.get('enhancements_applied', {})}")
            print()
        except Exception as e:
            print(f"Error enhancing query: {str(e)}\n")


async def main():
    """Run all demos."""
    print("Metadata System Demo")
    print("=" * 50)
    print()
    
    try:
        await demo_metadata_tools()
        await demo_metadata_agent()
        await demo_query_enhancement()
        
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"Demo failed with error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
