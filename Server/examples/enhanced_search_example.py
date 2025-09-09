"""Example demonstrating enhanced web search with content extraction."""

import asyncio
import json
from tools.web_tools import WebSearchTool, URLFetcherTool, ContentSummarizerTool


async def demonstrate_enhanced_search():
    """Demonstrate enhanced search with content extraction."""
    
    # Initialize tools
    search_tool = WebSearchTool()
    url_fetcher = URLFetcherTool()
    summarizer_tool = ContentSummarizerTool()
    
    # Example queries
    queries = [
        "What's current date and time?",
        "Latest SBI stock prices",
        "When will Avengers Doomsday will release?"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"🔍 QUERY: {query}")
        print(f"{'='*60}")
        
        # Perform web search
        result = await search_tool.execute(
            query=query,
            num_results=3,
            search_provider="auto"
        )
        
        if result["status"] == "success":
            print(f"✅ Found {result['num_results']} results")
            
            for i, search_result in enumerate(result["results"], 1):
                print(f"\n📄 RESULT {i}:")
                print(f"Title: {search_result.get('title', 'N/A')}")
                print(f"URL: {search_result.get('url', 'N/A')}")
                print(f"Snippet: {search_result.get('snippet', 'N/A')[:200]}...")
                
                # Extract content from URL if available
                url = search_result.get("url", "")
                if url and url.startswith("http"):
                    print(f"\n🔗 Extracting content from: {url}")
                    content_result = await url_fetcher.execute(
                        url=url,
                        fetch_type="content"
                    )
                    
                    if content_result["status"] == "success":
                        extracted_content = content_result.get("content", "")
                        print(f"\n📝 EXTRACTED CONTENT ({len(extracted_content)} chars):")
                        print(f"{extracted_content[:300]}...")
                        
                        # Summarize the extracted content
                        summary_result = await summarizer_tool.execute(
                            content=extracted_content,
                            max_length=200,
                            focus_keywords=query.split()
                        )
                        
                        if summary_result["status"] == "success":
                            print(f"\n📋 SUMMARY:")
                            print(f"{summary_result['summary']}")
                            print(f"Compression ratio: {summary_result['compression_ratio']:.2f}")
                    else:
                        print(f"❌ Content extraction failed: {content_result.get('error', 'Unknown error')}")
                else:
                    print("❌ No valid URL for content extraction")
                    
                print(f"\n{'─'*40}")
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")


async def demonstrate_content_extraction_only():
    """Demonstrate content extraction from a specific URL."""
    
    print(f"\n{'='*60}")
    print("🔗 CONTENT EXTRACTION DEMO")
    print(f"{'='*60}")
    
    url_fetcher = URLFetcherTool()
    
    # Example URL
    test_url = "https://example.com"
    
    print(f"Extracting content from: {test_url}")
    
    # Extract content
    content_result = await url_fetcher.execute(
        url=test_url,
        fetch_type="content"
    )
    
    if content_result["status"] == "success":
        print("✅ Content extraction successful")
        print(f"Title: {content_result.get('title', 'N/A')}")
        print(f"Description: {content_result.get('description', 'N/A')}")
        print(f"Content length: {len(content_result.get('content', ''))}")
        print(f"Domain: {content_result.get('extraction_metadata', {}).get('domain', 'N/A')}")
        print(f"Language: {content_result.get('extraction_metadata', {}).get('language', 'N/A')}")
        
        # Show first 500 characters of content
        clean_text = content_result.get('content', '')
        if clean_text:
            print(f"\n📝 EXTRACTED CONTENT:")
            print(f"{clean_text[:500]}...")
    else:
        print(f"❌ Content extraction failed: {content_result.get('error', 'Unknown error')}")


def show_llm_context_example():
    """Show how extracted content would be provided to LLM."""
    
    print(f"\n{'='*60}")
    print("🤖 LLM CONTEXT EXAMPLE")
    print(f"{'='*60}")
    
    # Example of how content would be structured for LLM
    llm_context = {
        "user_query": "What's current date and time?",
        "search_results": [
            {
                "title": "Current Time - World Clock",
                "url": "https://time.is/",
                "snippet": "Current time in any time zone. Compare time between different locations and time zones.",
                "extracted_content": "The current date and time is December 19, 2024, 3:45 PM UTC. This information is updated in real-time and shows the current time across different time zones worldwide. You can compare times between different locations and see the current date and time for any timezone.",
                "metadata": {
                    "domain": "time.is",
                    "language": "en",
                    "publication_date": None,
                    "content_type": "web_page"
                }
            }
        ],
        "synthesized_information": "Based on the search results, the current date and time is December 19, 2024, 3:45 PM UTC. This information is provided by time.is, a reliable source for current time information across different time zones."
    }
    
    print("📋 LLM Context Structure:")
    print(json.dumps(llm_context, indent=2))
    
    print(f"\n💡 LLM Prompt Example:")
    print(f"User Query: {llm_context['user_query']}")
    print(f"\nContext from Web Search:")
    for result in llm_context['search_results']:
        print(f"- {result['title']}: {result['extracted_content']}")
    
    print(f"\nSynthesized Information: {llm_context['synthesized_information']}")


if __name__ == "__main__":
    print("🚀 Web Search with Content Extraction Demo (Consolidated Tools)")
    
    # Run demonstrations
    asyncio.run(demonstrate_enhanced_search())
    asyncio.run(demonstrate_content_extraction_only())
    show_llm_context_example()
    
    print(f"\n{'='*60}")
    print("✅ Demo completed!")
    print("Key Benefits:")
    print("1. ✅ Extracts full content from web pages with legal compliance")
    print("2. ✅ Cleans HTML and formats for LLM consumption")
    print("3. ✅ Provides rich metadata (domain, author, date)")
    print("4. ✅ Summarizes content for better context")
    print("5. ✅ Handles multiple search providers with fallback")
    print("6. ✅ Robots.txt compliance and blocked domain checking")
    print("7. ✅ Graceful fallback when extraction fails")
    print(f"{'='*60}")
