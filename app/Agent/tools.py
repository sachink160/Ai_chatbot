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
import requests
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # Replace with your Django 

django.setup()
load_dotenv()

api_key="a4d3a866d5e23fb6477575896d4043ee"

FOURSQUARE_API_KEY = ""

from app.logger import get_logger
logger = get_logger(__name__)

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
    Plans a trip for a given destination and date using live data.
    Input format: 'destination, date'
    """
    try:
        destination, date = [x.strip() for x in input.split(",")]
    except Exception:
        return "Please provide input as 'destination, date' (e.g., 'Paris, 2024-08-15')."

    # Dynamic search
    sights = search_places("tourist attraction", destination, "16000")  # Foursquare category for sights
    eats = search_places("restaurant", destination, "13065")            # Foursquare category for restaurants
    hotels = search_places("hotel", destination, "19014")               # Foursquare category for hotels

    plan = f"""Trip Plan for {destination} on {date}:

1. 🏞️ **Places to Visit:**
   - {chr(10).join(sights)}

2. 🍽️ **Eating:**
   - {chr(10).join(eats)}

3. 🏨 **Staying:**
   - {chr(10).join(hotels)}

*All results are live from Foursquare. Prices and reviews may vary.*
"""
    return plan


def smart_scrape_updates(
    urls: Annotated[List[str], "List of base URLs (e.g., website homepages)"],
    keywords: Annotated[List[str], "Keywords like blog, news, product to look for internally"]
) -> str:
    """
    Scrape the latest content updates from one or more websites based on relevant internal links.

    This tool searches each provided base URL for internal hyperlinks that contain specified keywords
    such as 'blog', 'news', or 'product'. It then visits those internal pages and extracts the title,
    the first <h1> tag, and a paragraph summary to provide quick, high-level insights.

    Parameters:
        urls (List[str]): A list of base website URLs to scan (e.g., 'https://www.simform.com').
        keywords (List[str]): A list of keyword strings to match internal links (e.g., ['blog', 'news']).

    Returns:
        str: A formatted text summary of the top matched pages per site, including the page URL,
                title, heading, and paragraph. If no matches are found or scraping fails, error messages are included.
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
                    updates.append(f"🔗 {link}\n📌 {title}\n📝 {h1.get_text(strip=True) if h1 else ''}\n📄 {p.get_text(strip=True) if p else ''}")
                except Exception as e:
                    updates.append(f"❌ Failed to scrape {link}: {e}")
        
        except Exception as e:
            updates.append(f"❌ Error accessing {base_url}: {e}")

    return "\n\n---\n\n".join(updates) if updates else "No updates found."


def youtube_search(url: str) -> str:
    """
    Retrieve information and insights from a specific YouTube video URL.

    Args:
        url (str): The full URL of the YouTube video to analyze, e.g. "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    Returns:
        str: A dictionary containing the video's title, transcript (if available),
            and a summary of the video's content.

    Usage:
        Use this function when you want to extract the title, transcript, and a summary
        from a specific YouTube video by providing its URL.
    """
    if url:
        video_id = get_youtube_video_id(url)
        title = get_youtube_title(video_id)
        transcript = get_youtube_transcript(video_id)
        if transcript and transcript != "Transcript not available for this video.":
            summary = summarize_text_with_llm(transcript)
        else:
            summary = "No transcript available to summarize."
        return {
            "title": title,
            "transcript": transcript,
            "summary": summary
        }
    else:
        return {"detail":"Plze enter youtube video url"}

def google_search(query: str) -> str:
    """
    Search Google for the provided query and return a summary of the most relevant results.

    Args:
        query (str): The search keywords or phrase to look up on Google.

    Returns:
        str: A summary or list of the top Google search results for the query.
    """
    
    search = TavilySearchResults(max_results=2)
    return search.invoke({"query": query})

def weather_search(location: str) -> str:
    """
    Retrieve the current weather information for a specified location.

    Args:
        location (str): The name of the city or location to get weather data for.

    Returns:
        str: A summary of the current weather conditions at the specified location.
    """
    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={location}"
    try:
        response = requests.get(url)
        data = response.json()
        if "current" in data:
            weather_desc = data["current"]["weather_descriptions"][0]
            temp = data["current"]["temperature"]
            feelslike = data["current"]["feelslike"]
            humidity = data["current"]["humidity"]
            return (
                f"Weather for {location}: {weather_desc}, {temp}°C "
                f"(feels like {feelslike}°C), Humidity: {humidity}%"
            )
        elif "error" in data:
            return f"Error: {data['error'].get('info', 'Unable to fetch weather data.')}"
        else:
            return "Unable to fetch weather data at this time."
    except Exception as e:
        return f"Error fetching weather: {e}"


def send_email(to: str, subject: str, body: str, meeting_time: str = None, meet_link: str = None) -> str:
    """
    Send an email with meeting details and a Google Meet link if it's a meeting.

    Args:
        to (str): Recipient email.
        subject (str): Email subject.
        body (str): Email body.
        meeting_time (str, optional): Meeting time in readable format.
        meet_link (str, optional): Google Meet link.

    Returns:
        str: Confirmation or error message.
    """
    try:
        # If it's a meeting and no link is provided, generate one
        if meeting_time and not meet_link:
            meet_link = generate_google_meet_link()
        
        full_body = body
        if meeting_time and meet_link:
            full_body += f"\n\n📅 Meeting Schedule:\nDate & Time: {meeting_time}\n\n🔗 Join Google Meet:\n{meet_link}\n"

        send_mail(
            subject,
            full_body,
            settings.DEFAULT_FROM_EMAIL,
            [to],
            fail_silently=False,
        )

        log_meeting(to, subject, meeting_time, meet_link)
        return f"✅ Email sent to {to} with subject '{subject}' and meeting scheduled at {meeting_time or 'N/A'}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"
    
# Optional: Simple meeting logger (can be DB or file-based)
def log_meeting(to, subject, meeting_time, meet_link):
    with open("meeting_logs.txt", "a") as log:
        log.write(f"{datetime.now()} | To: {to} | Subject: {subject} | Time: {meeting_time} | Link: {meet_link}\n")

def wikipedia(query: str) -> str:
    """
    Search Wikipedia for information related to the given query and return a concise summary.

    Args:
        query (str): The topic, keyword, or phrase to look up on Wikipedia.

    Returns:
        str: A summary or extract of the most relevant Wikipedia article for the query.

    Usage:
        Use this tool when the user asks for factual, encyclopedic, or background information
        about people, places, events, concepts, or general knowledge topics.
        Example queries: "Alan Turing", "Quantum Computing", "History of India"
    """
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    return wikipedia.run(query)



def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def sum(a: int, b: int) -> int:
    """Sum or Add two numbers."""
    return a + b



total_tool = [weather_search, sum, multiply, send_email, google_search, youtube_search, wikipedia, smart_scrape_updates, trip_planner_tool]

tool_node = ToolNode(total_tool)
model = init_chat_model(model="openai:gpt-3.5-turbo")
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