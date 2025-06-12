from datetime import datetime
from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from twilio.rest import Client
import requests
import os
from dotenv import load_dotenv
from typing import TypedDict, Dict, List

# === Load environment variables ===
load_dotenv()

# === Config ===
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TO_WHATSAPP = os.getenv("TO_WHATSAPP") or "whatsapp:+918460117496"
FROM_WHATSAPP = os.getenv("FROM_WHATSAPP") or "whatsapp:+14155238886"

CATEGORIES = ["technology", "business", "health", "science", "sports"]

# === LLM ===
llm = ChatOllama(model="llama3.2", temperature=0.7)
# llm = ChatOpenAI(model="gpt-4", temperature=0.7)



# === Type Definitions for LangGraph ===
class NewsState(TypedDict):
    headlines: Dict[str, List[str]]
    summary: str


# === Fetch News ===
def fetch_news():
    headlines = {}
    for cat in CATEGORIES:
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={cat}&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        articles = res.get("articles", [])[:3]  # top 3 headlines per category
        headlines[cat] = [a["title"] for a in articles if "title" in a]
    return headlines


# === Summarize News ===
def summarize_news(state: NewsState) -> NewsState:
    headlines_by_category = state["headlines"]
    summary = ""

    for cat, headlines in headlines_by_category.items():
        # Join headlines, but limit total chars here to reduce length for LLM prompt (optional)
        input_text = "\n".join(headlines)

        prompt = PromptTemplate.from_template("""
        🗞️ Summarize these {category} headlines in 1–2 short lines (⚡️ concise, no bullet points, clear key info, use emojis if helpful):

        {headlines}
        """)

        chain = prompt | llm
        result = chain.invoke({"category": cat, "headlines": input_text})
        cat_summary = result.content.strip()

        # Limit each category summary to max 300 chars (you can tune this)
        if len(cat_summary) > 300:
            cat_summary = cat_summary[:297] + "..."

        summary += f"\n📢 {cat.upper()}:\n{cat_summary}\n"

    state["summary"] = summary
    return state


# === Graph Workflow ===
def build_graph():
    builder = StateGraph(NewsState)
    builder.add_node("summarize", summarize_news)
    builder.set_entry_point("summarize")
    builder.add_edge("summarize", END)
    return builder.compile()


# === Save Locally ===
def save_to_file(summary):
    with open("hourly_news_summary.txt", "a", encoding="utf-8") as f:
        f.write(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(summary + "\n" + "=" * 60 + "\n")


# === Send to WhatsApp ===
def send_whatsapp_message(summary):
    # Ensure message length <= 1600 characters for WhatsApp
    if len(summary) > 1600:
        summary = summary[:1597] + "..."

    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        message = client.messages.create(
            from_=FROM_WHATSAPP,
            body=summary,
            to=TO_WHATSAPP,
        )
        print(f"✅ WhatsApp message sent. SID: {message.sid}")
    except Exception as e:
        print(f"❌ Error sending WhatsApp message: {e}")



# === Main Runner ===
def run_news_agent():
    print(f"\n🕒 Running News Agent at {datetime.now()}...\n")
    try:
        headlines = fetch_news()
        graph = build_graph()
        result = graph.invoke({"headlines": headlines, "summary": ""})
        summary = result["summary"].strip()

        save_to_file(summary)
        send_whatsapp_message(summary)

        print(summary)
    except Exception as e:
        print(f"❌ Agent failed: {e}")