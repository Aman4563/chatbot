"""Test the final metadata system."""

import asyncio
from agents.chat_agent import ChatAgent
from graphs.state import ChatState


async def test():
    chat_agent = ChatAgent()
    state = ChatState(
        user_input='Find restaurants near me',
        current_agent='chat_agent',
        session_id='test123',
        ip_address='8.8.8.8',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        metadata={}
    )
    
    print('Testing final metadata system...')
    result = await chat_agent._collect_metadata(state)
    
    metadata = result.get('metadata', {}).get('user_metadata', {})
    print('✅ User metadata keys:', list(metadata.keys()))
    
    if 'location' in metadata:
        location = metadata['location']
        city = location.get('value', {}).get('city', 'Unknown')
        country = location.get('value', {}).get('country', 'Unknown')
        print(f'✅ Location: {city}, {country}')
    
    if 'timezone' in metadata:
        timezone = metadata['timezone']
        tz_value = timezone.get('value', 'Unknown')
        print(f'✅ Timezone: {tz_value}')
    
    # Test query enhancement
    enhanced = await chat_agent._enhance_query_with_metadata('Find restaurants near me', result)
    print(f'✅ Enhanced query: {enhanced}')


if __name__ == "__main__":
    asyncio.run(test())
