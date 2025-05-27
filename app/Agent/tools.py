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

import os
import requests
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # Replace with your Django 

django.setup()
load_dotenv()

api_key="a4d3a866d5e23fb6477575896d4043ee"

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

total_tool = [weather_search, sum, multiply, send_email, google_search, youtube_search, wikipedia]

tool_node = ToolNode(total_tool)

model = init_chat_model(model="openai:gpt-4o")
model_with_tools = model.bind_tools(total_tool)

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

def call_model(state: MessagesState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)

# Define the two nodes we will cycle between
builder.add_node("call_model", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", should_continue, ["tools", END])
builder.add_edge("tools", "call_model")

# memory = MemorySaver()
graph = builder.compile()
# memory = MemorySaver()
# graph = builder.compile(checkpointer=memory)
