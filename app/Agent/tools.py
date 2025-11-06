from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_community.tools import DuckDuckGoSearchRun, TavilySearchResults, WikipediaQueryRun # type: ignore
from langchain_community.utilities import WikipediaAPIWrapper # type: ignore
from dotenv import load_dotenv
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
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
import django # type: ignore
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # Replace with your Django 

django.setup()
load_dotenv()

api_key="a4d3a866d5e23fb6477575896d4043ee"

FOURSQUARE_API_KEY = ""

from app.logger import get_logger
logger = get_logger(__name__)


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


total_tool = [weather_search, google_search, wikipedia]

tool_node = ToolNode(total_tool)
# model = init_chat_model(model="openai:gpt-3.5-turbo")
model_4o = init_chat_model(model="openai:gpt-4o-mini")

model_with_tools = model_4o.bind_tools(total_tool)

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