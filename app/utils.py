import os
from llama_index.core import (
            VectorStoreIndex, 
            SimpleDirectoryReader,
            load_index_from_storage,
            ServiceContext,
            Settings  
        )


from llama_index.core import StorageContext
from llama_index.llms.langchain import LangChainLLM
from langchain_openai import ChatOpenAI

from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.text_splitter import TokenTextSplitter
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding


from dotenv import load_dotenv
load_dotenv()


HR_UPLOAD_DIR = "hr_docs"
INDEX_BASE_DIR = "storage"

# Genral use 
def get_storage_path(user_id: int, document_id: int) -> str:
    return os.path.join(INDEX_BASE_DIR, f"user_{user_id}", f"doc_{document_id}")


def load_or_create_index(filepath: str, user_id: int, document_id: int) -> VectorStoreIndex:
    storage_dir = get_storage_path(user_id, document_id)

    # ✅ Use ChatOpenAI with LangchainLLM for better responses
    chat_llm = ChatOpenAI(
        model_name="gpt-3.5-turbo", 
        temperature=0, 
        max_tokens=1024
    )
    llama_llm = LangChainLLM(llm=chat_llm)

    if os.path.exists(storage_dir) and os.listdir(storage_dir):
        storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
        return load_index_from_storage(storage_context, llm=llama_llm)

    documents = SimpleDirectoryReader(input_files=[filepath]).load_data()
    index = VectorStoreIndex.from_documents(documents, llm=llama_llm)
    index.storage_context.persist(persist_dir=storage_dir)
    return index



# # Hr Rag Use

# Youtube tools

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from langchain_openai import ChatOpenAI

def get_youtube_video_id(url: str) -> str:
    import re
    patterns = [
        r"youtu\.be/([^\?&]+)",
        r"youtube\.com/watch\?v=([^\?&]+)",
        r"youtube\.com/embed/([^\?&]+)",
        r"youtube\.com/v/([^\?&]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def get_youtube_title(video_id: str) -> str:
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    resp = requests.get(oembed_url)
    if resp.status_code == 200:
        return resp.json().get("title", "")
    return ""

def get_youtube_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([x['text'] for x in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        return "Transcript not available for this video."

def summarize_text_with_llm(text: str) -> str:
    """
    Summarize the given text using LangChain's ChatOpenAI LLM.
    """
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    prompt = (
        "Summarize the following YouTube video transcript and provide key insights:\n\n"
        f"{text}\n\nSummary:"
    )
    response = llm.invoke(prompt)
    return response.content.strip()


