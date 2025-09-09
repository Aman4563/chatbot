# Metadata System Documentation

## Overview

The Metadata System is a comprehensive solution for collecting, processing, and utilizing user metadata to enhance search results and provide contextual responses. It follows the hybrid approach recommended by GPT, combining browser-native signals with external APIs for optimal accuracy and performance.

## Architecture

### Core Components

1. **MetadataAgent** - Main orchestrator for metadata collection
2. **Metadata Tools** - Individual tools for specific metadata types
3. **Intelligent Routing** - Smart agent/tool selection based on query analysis
4. **Caching System** - Efficient storage and retrieval of metadata

### Metadata Tools

#### 1. TimezoneTool
- **Purpose**: Detect and convert timezone information
- **Sources**: Browser Intl API, IP geolocation, coordinates
- **Fallback**: UTC timezone
- **Cache TTL**: 24 hours for browser, 3 hours for IP

#### 2. LocationTool
- **Purpose**: Detect user location and perform geocoding
- **Sources**: Browser geolocation, IP geolocation, coordinates, address
- **APIs**: ip-api.com, Open-Meteo Geocoding
- **Cache TTL**: 3 hours

#### 3. DateTimeTool
- **Purpose**: Get current date and time information
- **Sources**: System clock with timezone awareness
- **Formats**: ISO, readable, timestamp
- **Features**: DST detection, day of week, week number

#### 4. UserAgentTool
- **Purpose**: Detect device and browser information
- **Sources**: User-Agent Client Hints (preferred), User-Agent string
- **Data**: Form factor, browser, OS, mobile detection
- **Confidence**: High for Client Hints, medium for UA string

## Data Flow

### 1. Query Analysis
```
User Query → ChatAgent → Analyze Intent → Determine Metadata Needs
```

### 2. Metadata Collection
```
MetadataAgent → Collect Tools → Cache Results → Return Unified Metadata
```

### 3. Query Enhancement
```
Original Query + Metadata → Enhanced Query → Web Search → Better Results
```

## API Integration

### Free APIs Used

#### Location Services
- **ip-api.com**: 45 requests/minute, no key required
- **Open-Meteo Geocoding**: Free, no key required
- **BigDataCloud**: Free tier available

#### Time Services
- **WorldTimeAPI**: Free, no key required
- **Python zoneinfo**: Built-in timezone support

### Data Accuracy

| Source | Location Accuracy | Time Accuracy | Cost | Reliability |
|--------|------------------|---------------|------|-------------|
| Browser Geolocation | High (GPS/WiFi) | N/A | Free | High |
| IP Geolocation | Medium (City level) | High | Free | Medium |
| Browser Intl API | N/A | High (99%) | Free | High |
| System Clock | N/A | High (99%) | Free | High |

## Usage Examples

### Basic Metadata Collection

```python
from agents.metadata_agent import MetadataAgent
from graphs.state import AgentState

# Create metadata agent
metadata_agent = MetadataAgent()

# Create state with user input
state = AgentState(
    user_input="Find restaurants near me",
    session_id="session_123",
    ip_address="8.8.8.8"
)

# Collect metadata
result_state = await metadata_agent.process(state)
metadata = result_state.get("metadata", {})
```

### Query Enhancement

```python
from agents.chat_agent import ChatAgent

# Create chat agent
chat_agent = ChatAgent()

# Enhance query with metadata
enhanced_query = await chat_agent._enhance_query_with_metadata(
    "Find restaurants near me",
    state_with_metadata
)
# Result: "Find restaurants near me in New York, United States"
```

### Individual Tool Usage

```python
from tools.metadata_tools import LocationTool

# Create location tool
location_tool = LocationTool()

# Get location from IP
result = await location_tool.execute(ip_address="8.8.8.8")
print(result["location"]["value"]["city"])  # "Mountain View"
```

## Configuration

### Agent Configuration

```python
# config/agents.py
"metadata_agent": {
    "name": "Metadata Agent",
    "description": "Specialized agent for collecting and providing user metadata",
    "capabilities": [
        "timezone_detection",
        "location_detection", 
        "datetime_processing",
        "device_detection",
        "user_context_analysis",
        "metadata_caching"
    ],
    "tools": [
        "timezone_tool",
        "location_tool", 
        "datetime_tool",
        "user_agent_tool"
    ],
    "default_model": "gemini-2.0-flash",
    "cache_ttl": 3600,
    "max_cache_size": 1000,
    "enabled": True,
    "priority": 2
}
```

### Tool Configuration

```python
# Individual tool settings
timezone_tool = TimezoneTool()
timezone_tool.cache_ttl = 3600  # 1 hour

location_tool = LocationTool()
location_tool.cache_ttl = 10800  # 3 hours
```

## Privacy and Security

### Data Handling
- **Consent First**: Explicit permission for precise location
- **Data Minimization**: Only collect necessary metadata
- **TTL-based Cleanup**: Automatic cache expiration
- **Source Attribution**: Track data provenance

### Privacy Controls
- **Granular Permissions**: Separate consent for location, timezone, device
- **Data Retention**: Configurable TTL for different data types
- **Anonymization**: Hash IP addresses in logs
- **Transparency**: Show users what data is used

## Performance Optimization

### Caching Strategy
- **Client-side**: Browser data cached in localStorage
- **Server-side**: Redis for API responses
- **Memory**: In-memory cache for frequently accessed data

### Fallback Mechanisms
- **Primary**: Browser-native signals (instant)
- **Secondary**: Free APIs (fast)
- **Tertiary**: Basic defaults (reliable)

### Rate Limiting
- **API Calls**: Respect provider limits
- **Cache Hits**: Minimize external requests
- **Batch Processing**: Collect multiple metadata in one call

## Error Handling

### Graceful Degradation
```python
try:
    # Try browser geolocation
    location = await browser_geolocation()
except PermissionDenied:
    # Fallback to IP geolocation
    location = await ip_geolocation()
except APIError:
    # Fallback to cached location
    location = await cached_location()
except Exception:
    # Final fallback to default
    location = {"city": "Unknown", "country": "Unknown"}
```

### Error Recovery
- **Retry Logic**: Exponential backoff for API failures
- **Circuit Breaker**: Stop calling failing APIs temporarily
- **Health Checks**: Monitor API availability
- **Fallback Chains**: Multiple fallback options

## Monitoring and Observability

### Metrics Tracked
- **Response Time**: Metadata collection latency
- **Cache Hit Rate**: Efficiency of caching
- **API Success Rate**: External service reliability
- **Error Rates**: Failure patterns

### Logging
```python
# Structured logging
logger.info("metadata_collected", {
    "session_id": session_id,
    "metadata_types": ["timezone", "location"],
    "sources": ["browser", "ip_api"],
    "response_time": 0.5,
    "cache_hit": True
})
```

## Testing

### Unit Tests
```python
# Test individual tools
async def test_timezone_tool():
    tool = TimezoneTool()
    result = await tool.execute(timezone_input="America/New_York")
    assert result["status"] == "success"
    assert result["timezone"]["value"] == "America/New_York"
```

### Integration Tests
```python
# Test full metadata collection
async def test_metadata_agent():
    agent = MetadataAgent()
    state = AgentState(user_input="Find restaurants near me")
    result = await agent.process(state)
    assert "metadata" in result
    assert "location" in result["metadata"]
```

### Demo Script
```bash
# Run the demo
python Server/examples/metadata_demo.py
```

## Future Enhancements

### Phase 2 Features
- **Weather Integration**: Open-Meteo weather data
- **Currency Detection**: Exchange rate information
- **Language Detection**: Browser language preferences
- **Device Capabilities**: Screen size, input methods

### Phase 3 Features
- **Machine Learning**: Improve location accuracy
- **Predictive Caching**: Pre-fetch likely metadata
- **Real-time Updates**: Live location tracking
- **Advanced Analytics**: Usage patterns and optimization

## Troubleshooting

### Common Issues

#### 1. Location Accuracy Issues
- **Problem**: IP geolocation shows wrong city
- **Solution**: Use browser geolocation with user consent
- **Fallback**: Multiple IP geolocation providers

#### 2. Timezone Detection Failures
- **Problem**: Browser timezone not detected
- **Solution**: Fallback to IP-based timezone
- **Fallback**: UTC timezone

#### 3. API Rate Limiting
- **Problem**: External APIs rate limited
- **Solution**: Implement caching and rate limiting
- **Fallback**: Use cached data or alternative providers

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger("metadata_agent").setLevel(logging.DEBUG)

# Check cache status
metadata_agent = MetadataAgent()
print(f"Cache size: {len(metadata_agent.metadata_cache)}")
```

## Contributing

### Adding New Metadata Types
1. Create new tool in `tools/metadata_tools.py`
2. Add tool to MetadataAgent
3. Update configuration in `config/agents.py`
4. Add tests and documentation

### Adding New APIs
1. Research free API options
2. Implement with proper error handling
3. Add rate limiting and caching
4. Update documentation

## License

This metadata system is part of the chatbot project and follows the same licensing terms.
