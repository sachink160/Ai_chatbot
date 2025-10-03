from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_community.tools import DuckDuckGoSearchRun, TavilySearchResults, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

from app.comman import generate_google_meet_link
from app.utils import get_youtube_title, get_youtube_transcript, get_youtube_video_id, summarize_text_with_llm

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from typing import Annotated, List
import os
import json
import re
import requests
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # Replace with your Django 

django.setup()
load_dotenv()

api_key="a4d3a866d5e23fb6477575896d4043ee"

FOURSQUARE_API_KEY = ""

from app.logger import get_logger
logger = get_logger(__name__)

from pydantic import BaseModel
class GitaResponse(BaseModel):
    shloka: str
    transliteration: str
    explanation: str
    scenario: str
    solution: str

def search_places(query, near, category):
    url = "https://api.foursquare.com/v3/places/search"
    headers = {"Authorization": FOURSQUARE_API_KEY}
    params = {
        "query": query,
        "near": near,
        "categories": category,
        "limit": 3
    }
    try:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for place in data.get("results", []):
            name = place.get("name")
            address = ", ".join(place.get("location", {}).get("formatted_address", []))
            rating = place.get("rating", "N/A")
            results.append(f"{name} ({address}) - Rating: {rating}")
        logger.info(f"Found {len(results)} places for {query} in {near}")
        return results
    except Exception as e:
        logger.error(f"API error for {query} in {near}: {e}")
        return [f"API error: {e}"]

def trip_planner_tool(input: str) -> str:
    """
    Create comprehensive travel itineraries with real-time recommendations for attractions, dining, and accommodations.
    
    This intelligent trip planning tool uses live data to suggest tourist attractions, restaurants, 
    and hotels for your destination. Perfect for planning vacations, business trips, or weekend getaways.

    Args:
        input (str): Destination and date in format "destination, date" 
                   (e.g., "Paris, 2024-08-15", "Tokyo, next Friday", "New York, 2024-12-25")

    Returns:
        str: Detailed trip plan with attractions, restaurants, hotels, and practical travel information
        
    Usage Examples:
        - "Plan a trip to Paris for August 15th, 2024"
        - "Create itinerary for Tokyo next weekend"
        - "Plan vacation to New York for Christmas"
    """
    try:
        destination, date = [x.strip() for x in input.split(",")]
    except Exception:
        return "Please provide input as 'destination, date' (e.g., 'Paris, 2024-08-15')."

    # Dynamic search
    sights = search_places("tourist attraction", destination, "16000")  # Foursquare category for sights
    eats = search_places("restaurant", destination, "13065")            # Foursquare category for restaurants
    hotels = search_places("hotel", destination, "19014")               # Foursquare category for hotels

    plan = f"""🗺️ **Trip Plan for {destination} on {date}**

🏞️ **Top Attractions:**
{chr(10).join(f"   • {sight}" for sight in sights)}

🍽️ **Recommended Restaurants:**
{chr(10).join(f"   • {eat}" for eat in eats)}

🏨 **Accommodation Options:**
{chr(10).join(f"   • {hotel}" for hotel in hotels)}

💡 **Travel Tips:**
• Check local weather and pack accordingly
• Book accommodations in advance for better rates
• Research local customs and etiquette
• Download offline maps for navigation

📱 **Live Data Source:** Foursquare API
⚠️ **Note:** Prices and availability may vary. Contact venues directly for current information.
"""
    return plan

 
def smart_scrape_updates(
    urls: Annotated[List[str], "List of base URLs (e.g., website homepages)"],
    keywords: Annotated[List[str], "Keywords like blog, news, product to look for internally"]
) -> str:
    """
    Intelligently scrape and analyze website content for the latest updates and relevant information.
    
    This advanced web scraping tool searches websites for specific content types (blogs, news, products)
    and extracts meaningful information including titles, headings, and summaries. Perfect for
    monitoring competitor websites, tracking industry updates, or researching specific topics.

    Parameters:
        urls (List[str]): Base website URLs to analyze (e.g., ['https://example.com', 'https://news-site.com'])
        keywords (List[str]): Content type keywords to search for (e.g., ['blog', 'news', 'product', 'update'])

    Returns:
        str: Formatted summary with extracted content, titles, headings, and key information from matched pages
        
    Usage Examples:
        - Monitor competitor blog posts and product updates
        - Track latest news from multiple sources
        - Research specific topics across websites
        - Analyze website content structure and updates
    """
    updates = []

    for base_url in urls:
        try:
            res = requests.get(base_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            # Step 1: Find matching internal links
            internal_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(base_url, href)
                if any(kw.lower() in href.lower() for kw in keywords):
                    internal_links.append(full_url)

            unique_links = list(set(internal_links))[:3]  # Limit to 3 per site

            # Step 2: Scrape title, h1, and paragraph from each matching page
            for link in unique_links:
                try:
                    r = requests.get(link, timeout=10)
                    r.raise_for_status()
                    page = BeautifulSoup(r.text, "html.parser")
                    title = page.title.string.strip() if page.title else "No title"
                    h1 = page.find("h1")
                    p = page.find("p")
                    
                    # Enhanced content extraction
                    meta_desc = page.find("meta", attrs={"name": "description"})
                    description = meta_desc.get("content", "") if meta_desc else ""
                    
                    # Format with better structure
                    content_summary = f"""
🔗 **URL:** {link}
📌 **Title:** {title}
📝 **Heading:** {h1.get_text(strip=True) if h1 else 'No heading found'}
📄 **Content:** {p.get_text(strip=True)[:200] + '...' if p and len(p.get_text(strip=True)) > 200 else p.get_text(strip=True) if p else 'No content found'}
📋 **Description:** {description[:150] + '...' if description and len(description) > 150 else description if description else 'No description'}
"""
                    updates.append(content_summary.strip())
                except Exception as e:
                    updates.append(f"❌ Failed to scrape {link}: {e}")
        
        except Exception as e:
            updates.append(f"❌ Error accessing {base_url}: {e}")

    return "\n\n---\n\n".join(updates) if updates else "No updates found."


def youtube_search(url: str) -> str:
    """
    Extract comprehensive insights and content from YouTube videos for analysis and summarization.
    
    This tool analyzes YouTube videos by extracting their title, transcript, and generating
    intelligent summaries. Perfect for educational content, tutorials, lectures, and informational videos.

    Args:
        url (str): Complete YouTube video URL (e.g., "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    Returns:
        dict: Structured data containing:
            - title: Video title
            - transcript: Full transcript text (if available)
            - summary: AI-generated summary of video content
            
    Usage Examples:
        - "Analyze this YouTube tutorial: https://www.youtube.com/watch?v=abc123"
        - "Summarize this educational video: https://youtu.be/xyz789"
        - "What does this YouTube video say about AI?"
    """
    if not url or not url.strip():
        return {"error": "Please provide a valid YouTube video URL"}
    
    try:
        video_id = get_youtube_video_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL format. Please provide a complete YouTube video URL."}
            
        title = get_youtube_title(video_id)
        transcript = get_youtube_transcript(video_id)
        
        if transcript and transcript != "Transcript not available for this video.":
            summary = summarize_text_with_llm(transcript)
        else:
            summary = "📝 Transcript not available for this video. The video may not have captions enabled or may be private."
            
        return {
            "title": f"📺 {title}",
            "transcript": transcript,
            "summary": f"📋 **Video Summary:**\n{summary}",
            "video_id": video_id,
            "url": url
        }
    except Exception as e:
        return {"error": f"Failed to process YouTube video: {str(e)}"}

def google_search(query: str) -> str:
    """
    Perform intelligent web search using Google to find the most relevant and up-to-date information.
    
    This tool searches the web for current information, news, facts, and data. It's perfect for
    finding recent developments, verifying facts, getting current statistics, or researching topics.

    Args:
        query (str): Search keywords, phrases, or questions (e.g., "latest AI developments 2024", 
                    "current stock prices", "recent news about climate change")

    Returns:
        str: Curated summary of the most relevant search results with sources and key information.
        
    Usage Examples:
        - "What are the latest developments in artificial intelligence?"
        - "Current news about renewable energy"
        - "Recent research on quantum computing"
        - "Today's weather forecast for New York"
    """
    
    search = TavilySearchResults(max_results=2)
    return search.invoke({"query": query})

def weather_search(location: str) -> str:
    """
    Get comprehensive current weather information for any location worldwide.
    
    This tool provides real-time weather data including temperature, conditions, 
    humidity, wind speed, and "feels like" temperature for accurate weather reporting.

    Args:
        location (str): City name, country, or coordinates (e.g., "New York", "London, UK", "40.7128,-74.0060")

    Returns:
        str: Detailed weather summary with temperature, conditions, humidity, and location confirmation.
        
    Usage Examples:
        - "What's the weather in Paris?"
        - "Current weather for Tokyo, Japan"
        - "Weather conditions in Mumbai"
    """
    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={location}"
    try:
        response = requests.get(url)
        data = response.json()
        if "current" in data:
            current = data["current"]
            location_name = data["location"]["name"] if "location" in data else location
            weather_desc = current["weather_descriptions"][0]
            temp = current["temperature"]
            feelslike = current["feelslike"]
            humidity = current["humidity"]
            wind_speed = current.get("wind_speed", "N/A")
            wind_dir = current.get("wind_dir", "N/A")
            pressure = current.get("pressure", "N/A")
            uv_index = current.get("uv_index", "N/A")
            
            return (
                f"🌤️ **Weather for {location_name}**\n"
                f"🌡️ Temperature: {temp}°C (feels like {feelslike}°C)\n"
                f"☁️ Conditions: {weather_desc}\n"
                f"💧 Humidity: {humidity}%\n"
                f"💨 Wind: {wind_speed} km/h {wind_dir}\n"
                f"📊 Pressure: {pressure} mb\n"
                f"☀️ UV Index: {uv_index}\n"
                f"🕐 Last updated: {current.get('observation_time', 'Recently')}"
            )
        elif "error" in data:
            return f"Error: {data['error'].get('info', 'Unable to fetch weather data.')}"
        else:
            return "Unable to fetch weather data at this time."
    except Exception as e:
        return f"Error fetching weather: {e}"


def send_email(to: str, subject: str, body: str, meeting_time: str = None, meet_link: str = None) -> str:
    """
    Send professional emails with intelligent meeting detection and Google Meet integration.
    
    This tool automatically detects meeting requests and generates Google Meet links.
    It formats emails professionally and logs meeting details for tracking.

    Args:
        to (str): Recipient email address (e.g., "john@example.com")
        subject (str): Email subject line
        body (str): Email content/message
        meeting_time (str, optional): Specific meeting time (e.g., "2:00 PM", "Tomorrow at 3 PM")
        meet_link (str, optional): Custom Google Meet link (if not provided, will be auto-generated)

    Returns:
        str: Confirmation message with meeting details if applicable
        
    Usage Examples:
        - "Send email to sarah@company.com about project update"
        - "Schedule meeting with team for tomorrow at 2 PM"
        - "Send follow-up email with meeting link"
    """
    try:
        # Enhanced meeting detection with more keywords
        meeting_keywords = ["meet", "meeting", "google meet", "zoom", "call", "conference", "schedule", "appointment", "discuss", "sync"]
        is_meeting = any(word in (subject + body).lower() for word in meeting_keywords)
        
        # Try to extract meeting time from body if not provided
        if not meeting_time and is_meeting:
            import re
            # More comprehensive time pattern matching
            time_patterns = [
                r'(\d{1,2}(:\d{2})?\s*(am|pm))',
                r'(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(\d{1,2}:\d{2})',
                r'(at \d{1,2}(:\d{2})?\s*(am|pm))'
            ]
            for pattern in time_patterns:
                match = re.search(pattern, body, re.IGNORECASE)
                if match:
                    meeting_time = match.group(0)
                    break
        
        # Always generate a meet link for meetings
        if is_meeting and not meet_link:
            meet_link = generate_google_meet_link()
            
        # Enhanced email formatting
        full_body = body
        if is_meeting and meet_link:
            full_body += f"\n\n📅 **Meeting Details:**\n"
            full_body += f"🕐 Time: {meeting_time or 'To be confirmed'}\n"
            full_body += f"🔗 Google Meet Link: {meet_link}\n"
            full_body += f"📧 Meeting ID: {meet_link.split('/')[-1] if '/' in meet_link else 'Generated'}\n"
            full_body += f"\n💡 **Meeting Tips:**\n"
            full_body += f"• Join 5 minutes early to test your connection\n"
            full_body += f"• Ensure you have a stable internet connection\n"
            full_body += f"• Mute your microphone when not speaking\n"
        send_mail(
            subject,
            full_body,
            settings.DEFAULT_FROM_EMAIL,
            [to],
            fail_silently=False,
        )
        log_meeting(to, subject, meeting_time, meet_link)
        
        if is_meeting:
            return f"✅ **Meeting Email Sent Successfully!**\n📧 To: {to}\n📝 Subject: {subject}\n🕐 Meeting Time: {meeting_time or 'To be confirmed'}\n🔗 Meet Link: {meet_link}\n📋 Meeting logged for tracking"
        else:
            return f"✅ **Email Sent Successfully!**\n📧 To: {to}\n📝 Subject: {subject}\n📄 Message delivered"
    except Exception as e:
        return f"❌ Failed to send email: {e}"
    
# Optional: Simple meeting logger (can be DB or file-based)
def log_meeting(to, subject, meeting_time, meet_link):
    with open("meeting_logs.txt", "a") as log:
        log.write(f"{datetime.now()} | To: {to} | Subject: {subject} | Time: {meeting_time} | Link: {meet_link}\n")

def wikipedia(query: str) -> str:
    """
    Access comprehensive Wikipedia knowledge for accurate, well-sourced information.
    
    This tool searches Wikipedia's vast database to provide detailed, factual information
    about people, places, events, concepts, and general knowledge topics with proper citations.

    Args:
        query (str): Topic, person, place, concept, or keyword to research
                   (e.g., "Albert Einstein", "Quantum Computing", "History of India")

    Returns:
        str: Detailed Wikipedia article summary with key facts, dates, and information
        
    Usage Examples:
        - "Tell me about Albert Einstein's contributions to physics"
        - "What is quantum computing and how does it work?"
        - "History of the Roman Empire"
        - "Information about renewable energy sources"
    """
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    return wikipedia.run(query)

def gita_expert(query: str) -> GitaResponse:
    """
    Provide spiritual guidance and life wisdom based on the timeless teachings of the Bhagavad Gita.
    
    This expert system analyzes life situations, problems, and questions to provide relevant
    shlokas (verses) from the Bhagavad Gita along with practical guidance and solutions.
    Perfect for seeking spiritual wisdom, moral guidance, and life direction.

    Args:
        query (str): Life question, problem, or situation seeking guidance
                   (e.g., "I'm feeling stressed about work", "How to deal with failure?", 
                   "What is the purpose of life?")

    Returns:
        GitaResponse: Structured response with Sanskrit shloka, transliteration, 
                     explanation, scenario, and practical solution
        
    Usage Examples:
        - "I'm struggling with anxiety and stress"
        - "How should I handle difficult relationships?"
        - "What does the Gita say about success and failure?"
        - "I need guidance on making important life decisions"
    """

    system_prompt = """
        You are a wise spiritual guide deeply versed in the Bhagavad Gita's timeless wisdom.
        Your role is to provide compassionate guidance by selecting the most relevant shloka
        for the user's life situation and offering practical, actionable advice.
        
        **CRITICAL:** Respond ONLY in valid JSON format. No additional text outside JSON.

        Required JSON Structure:
        {
            "shloka": "📖 Original Sanskrit verse with chapter and verse reference (e.g., 'Bhagavad Gita 2.47')",
            "transliteration": "🔤 Romanized Sanskrit text for pronunciation",
            "explanation": "✨ Clear, compassionate explanation in simple language that directly addresses the user's concern",
            "scenario": "🌿 A relatable real-life example or story that illustrates the teaching",
            "solution": "💡 Specific, actionable steps the user can take to apply this wisdom to their situation"
        }

        **Guidelines:**
        - Choose shlokas that directly relate to the user's emotional state or life challenge
        - Make explanations practical and immediately applicable
        - Use warm, supportive language that provides hope and direction
        - Ensure the solution offers concrete steps for improvement
        - Match the language tone to the user's query (formal/informal)
        """

    enhanced_query = f"""
    **User's Life Situation:** {query}
    
    **Your Task:** 
    1. Analyze the user's emotional state and life challenge
    2. Select the most appropriate Bhagavad Gita shloka that addresses their specific concern
    3. Provide compassionate, practical guidance that offers hope and direction
    4. Respond in the exact JSON format specified above
    
    **Remember:** Your response should feel like wise counsel from a caring spiritual mentor.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": enhanced_query}
    ]

    try:
        response = model_4o.invoke(messages)
        raw_output = response.content if hasattr(response, "content") else str(response)

        # Try parsing JSON
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            # Extract JSON if model wrapped it with extra text
            match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if not match:
                raise ValueError("No valid JSON found in model output")
            parsed = json.loads(match.group(0))

        # ✅ Validate using Pydantic
        return GitaResponse(**parsed)

    except Exception as error:
        return GitaResponse(
            shloka="Error",
            transliteration="Error",
            explanation=f"🕉️ Technical Error: {str(error)}",
            scenario="🙏 Suggestion: Please rephrase your question in simple words.",
            solution="The Gita has wisdom for every situation – let's try again!"
        )
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b

# def sum(a: int, b: int) -> int:
#     """Sum or Add two numbers."""
#     return a + b



total_tool = [gita_expert,weather_search, send_email, google_search, youtube_search, wikipedia, smart_scrape_updates, trip_planner_tool]

tool_node = ToolNode(total_tool)
model = init_chat_model(model="openai:gpt-3.5-turbo")
model_4o = init_chat_model(model="openai:gpt-4o-mini")
# model = init_chat_model(model="openai:gpt-4o")
model_with_tools = model.bind_tools(total_tool)

def should_continue(state: MessagesState):
    last_msg = state["messages"][-1]
    return "tools" if last_msg.tool_calls else END

def call_model(state: MessagesState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", should_continue, ["tools", END])
builder.add_edge("tools", "call_model")

memory = MemorySaver()  # ✅ Enables memory/summarization
# graph = builder.compile()
graph = builder.compile(checkpointer=memory)  