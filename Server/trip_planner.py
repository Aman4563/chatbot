# trip_planner.py
from typing import List, Optional, Union
import os

from crewai import Agent, Crew, Process, Task
from crewai_tools import SerperDevTool, WebsiteSearchTool, ScrapeWebsiteTool
# Assuming CustomGeminiVisionTool is defined in your project; import accordingly
from custom_gemini_vision_tool import CustomGeminiVisionTool

# Environment setup
_GOOGLE_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not _GOOGLE_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY before running.")
os.environ.setdefault("GOOGLE_API_KEY", _GOOGLE_KEY)

if not os.getenv("SERPER_API_KEY"):
    raise RuntimeError("Set SERPER_API_KEY (for SerperDevTool) before running.")

# Embedchain config (unchanged from your crew.py)
EMBEDCHAIN_CONFIG = {
    "llm": {
        "provider": "google",
        "config": {
            "model": "gemini-1.5-flash",
            "temperature": 0.2,
        },
    },
    "embedder": {
        "provider": "google",
        "config": {
            "model": "models/text-embedding-004",
            "task_type": "RETRIEVAL_DOCUMENT",
        },
    },
}

def run_trip_planner(user_prompt: str, images: Optional[Union[str, List[str]]] = None) -> str:
    """
    Runs the CrewAI trip planner based on the user query and optional images.
    Returns the final trip plan as a string.
    """
    # Normalize images to a list if it's a single string
    if isinstance(images, str):
        images = [images]
    elif images is None:
        images = []

    # ─────────────
    # Tools
    # ─────────────
    vision_tool = CustomGeminiVisionTool()
    search_tool = SerperDevTool()  # requires SERPER_API_KEY
    website_search = WebsiteSearchTool(config=EMBEDCHAIN_CONFIG)  # uses GOOGLE_API_KEY from env
    scraper = ScrapeWebsiteTool()

    # ─────────────
    # Agents (unchanged from your crew.py)
    # ─────────────
    location_identifier = Agent(
        role="Travel Research & Sourcing Agent",
        goal=(
            "For any trip request, find the most relevant, bookable FLIGHT, HOTEL, and THINGS-TO-DO options. "
            "Infer the user's current origin city from the query, past context, timestamps, or web results. "
            "If you cannot determine origin, explicitly assume Gurugram, India. "
            "Return only options that are current, practical, and easy to book, each with a direct link."
        ),
        backstory=(
            "You’re an ex-concierge and deal hunter. You prioritize reliability, total travel time, and value. "
            "You prefer official sites (airlines), Google Flights searches, reputable OTAs, hotel official/Booking.com pages, "
            "and Google Maps links for places. You avoid fluff and keep lists tight."
        ),
        tools=[vision_tool, search_tool, website_search, scraper],
        verbose=True,
        allow_delegation=False,
    )

    query_analyzer = Agent(
        role="Itinerary & Logistics Synthesizer",
        goal=(
            "Turn the sourced options into the most helpful, concise trip answer possible. "
            "Include: top flight pick(s), 2–3 hotel options (with neighborhood), and 4–6 must-do items. "
            "ALWAYS include direct links (booking or maps). "
            "State any assumptions (dates, origin if inferred/assumed). "
            "Prefer bullet points; keep it short and to the point."
        ),
        backstory=(
            "You craft crisp trip briefs people can act on immediately. You surface only what matters, "
            "with links, quick reasons, and INR estimates when feasible."
        ),
        verbose=True,
    )

    reviewer = Agent(
        role="Response Quality & Link Reviewer",
        goal=(
            "Verify the final answer is accurate, link-rich, concise, and directly useful. "
            "Check that origin detection is stated (or the Gurugram fallback is explicit), "
            "and that there are booking/search links for flights and hotels plus Google Maps links for places. "
            "Trim any fluff; ensure scannability. If anything is missing, fix it."
        ),
        backstory=(
            "You’re a meticulous editor focused on usefulness-per-word. You enforce brevity and actionability."
        ),
        verbose=True,
    )

    # ─────────────
    # Tasks (adapted to use function inputs)
    # ─────────────
    analyze_image_task = Task(
        description=(
            f"RESEARCH the trip request from {user_prompt} (images {images} only if relevant). "
            "Infer ORIGIN city from the query/context/web; if not possible, set origin='Gurugram, India' and note this assumption. "
            "Gather: \n"
            "1) FLIGHTS: 2–4 viable options with airline, total duration, layovers, rough INR price if findable, and a direct link "
            "(prefer Google Flights search links or airline booking deep links). \n"
            "2) HOTELS: 2–3 options with neighborhood, brief why (walkability, transit, safety), rough INR/night if findable, "
            "and a direct booking link (official or Booking.com). \n"
            "3) THINGS TO DO: 4–6 highlights with one-line why and a Google Maps link. "
            "Favor recency and reliability; avoid filler."
        ),
        expected_output=(
            "A concise research bundle with:\n"
            "- origin_city (detected or 'Gurugram, India' if assumed)\n"
            "- flights: list of {title, reason/notes, link}\n"
            "- hotels: list of {title, area, reason, link}\n"
            "- activities: list of {title, why, maps_link}\n"
            "Keep text tight; every item must have a working link."
        ),
        agent=location_identifier,
    )

    query_analysis_task = Task(
        description=(
            f"SYNTHESIZE a short, highly helpful answer from the research and the query {user_prompt}. "
            "Format as markdown with the following sections (only if relevant):\n"
            "• Flights — 1–2 best picks with direct link(s)\n"
            "• Stay — 2–3 hotel picks (area + link)\n"
            "• Things to do — 4–6 items (each with a Google Maps link)\n"
            "• Essentials — assumptions (dates, origin), quick tips (weather, local transit), INR notes if available\n"
            "Rules: Be concise, no fluff, maximize usefulness, ensure links are present. "
            "If origin was assumed, state: 'Origin assumed: Gurugram, India'."
        ),
        expected_output=(
            "A concise, action-ready markdown response (ideally under ~220 words) with direct links for flights, hotels, and places. "
            "No extra commentary beyond what helps booking and planning."
        ),
        agent=query_analyzer,
        context=[analyze_image_task],
    )

    review_task = Task(
        description=(
            "QUALITY CHECK the final response against the brief: brevity, accuracy, clear assumptions, and working links. "
            "Ensure at least: one flight link, two hotel links, and maps links for all listed activities. "
            "If anything is missing or verbose, rewrite to fix it while preserving structure and links."
        ),
        expected_output=(
            "Either 'LGTM' with a one-line rationale OR a revised final response (markdown) meeting all requirements."
        ),
        agent=reviewer,
        context=[analyze_image_task, query_analysis_task],
        output_file="review_report.md",
    )

    # ─────────────
    # Crew
    # ─────────────
    crew = Crew(
        agents=[location_identifier, query_analyzer, reviewer],
        tasks=[analyze_image_task, query_analysis_task, review_task],
        process=Process.sequential,
        verbose=True,
        memory=False,  # keep off unless you configure embeddings explicitly
    )

    # Kickoff with inputs
    # inputs = {
    #     'user_prompt': user_prompt,
    #     'images': images  # Pass the list of image paths/URLs
    # }
    inputs = {
        'user_prompt': "what is this image about?",
        'images': r"C:\Users\HP\Desktop\alfa beta\chatbot project\Server\generated_image.png"  # Pass the list of image paths/URLs
    }
    result = crew.kickoff(inputs=inputs)
    return str(result)
