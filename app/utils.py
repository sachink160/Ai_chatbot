import os
import hashlib
from llama_index.core import (
            VectorStoreIndex, 
            SimpleDirectoryReader,
            load_index_from_storage,
            ServiceContext,
            Settings,
            StorageContext
        )

from llama_index.llms.langchain import LangChainLLM
from langchain_openai import ChatOpenAI
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.text_splitter import TokenTextSplitter
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
import pinecone

from dotenv import load_dotenv
load_dotenv()
from app.config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME_PREFIX

from app.logger import get_logger
logger = get_logger(__name__)


HR_UPLOAD_DIR = "hr_docs"
INDEX_BASE_DIR = "storage"

# Genral use 
def get_storage_path(user_id: int, document_id: int) -> str:
    path = os.path.join(INDEX_BASE_DIR, f"user_{user_id}", f"doc_{document_id}")
    logger.debug(f"Generated storage path: {path}")
    return path

def get_chat_storage_path(user_id: int, document_id: str) -> str:
    """Get storage path for chat documents"""
    path = os.path.join(INDEX_BASE_DIR, f"user_{user_id}", f"chat_doc_{document_id}")
    os.makedirs(path, exist_ok=True)
    logger.debug(f"Generated chat storage path: {path}")
    return path


def load_or_create_index(filepath: str, user_id: int, document_id: int) -> VectorStoreIndex:
    storage_dir = get_storage_path(user_id, document_id)

    # ✅ Use ChatOpenAI with LangchainLLM for better responses
    chat_llm = ChatOpenAI(
        model_name="gpt-4o-mini", 
        # model_name="gpt-3.5-turbo", 
        temperature=0, 
        max_tokens=1024
    )
    llama_llm = LangChainLLM(llm=chat_llm)

    if os.path.exists(storage_dir) and os.listdir(storage_dir):
        storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
        logger.info(f"Loading index from storage for user {user_id}, doc {document_id}")
        return load_index_from_storage(storage_context, llm=llama_llm)

    documents = SimpleDirectoryReader(input_files=[filepath]).load_data()
    index = VectorStoreIndex.from_documents(documents, llm=llama_llm)
    index.storage_context.persist(persist_dir=storage_dir)
    logger.info(f"Created and persisted new index for user {user_id}, doc {document_id}")
    return index

def load_or_create_chat_index(filepath: str, user_id: int, document_id: str) -> VectorStoreIndex:
    """Load or create index for chat documents using Pinecone"""
    
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not set in environment variables")
    
    # Initialize Pinecone (compatible with both old and new API)
    try:
        # Try new API (v3+) - serverless by default
        from pinecone import Pinecone as PineconeClient, ServerlessSpec
        pc = PineconeClient(api_key=PINECONE_API_KEY)
        # For new API, list_indexes() returns IndexList object
        def list_indexes():
            return [idx.name for idx in pc.list_indexes()]
        def create_index(name, dimension, metric):
            # Extract region from environment (e.g., "us-east-1-aws" -> "us-east-1")
            region = PINECONE_ENVIRONMENT
            if "-" in PINECONE_ENVIRONMENT:
                parts = PINECONE_ENVIRONMENT.split("-")
                if len(parts) >= 3:
                    region = f"{parts[0]}-{parts[1]}-{parts[2]}"
            # For serverless (new default), use spec parameter
            # Always include spec parameter for v3+ API
            return pc.create_index(
                name=name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud="aws", region=region)
            )
        list_indexes_method = list_indexes
        create_index_method = create_index
        get_index_method = lambda name: pc.Index(name)
        logger.info("Using Pinecone v3+ API")
    except (ImportError, AttributeError):
        # Fall back to old API (v2) - pod-based
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        list_indexes_method = pinecone.list_indexes
        def create_index(name, dimension, metric):
            return pinecone.create_index(
                name=name,
                dimension=dimension,
                metric=metric,
                environment=PINECONE_ENVIRONMENT
            )
        create_index_method = create_index
        get_index_method = pinecone.Index
        logger.info("Using Pinecone v2 API (pod-based)")
    
    # Create unique index name for each user-document combination
    # Pinecone index names must be lowercase, alphanumeric with hyphens/underscores, and max 45 chars
    # Use hash to create short unique identifier
    unique_id = f"{user_id}_{document_id}"
    hash_id = hashlib.md5(unique_id.encode()).hexdigest()[:12]  # 12 char hash
    prefix = PINECONE_INDEX_NAME_PREFIX[:20] if len(PINECONE_INDEX_NAME_PREFIX) > 20 else PINECONE_INDEX_NAME_PREFIX
    index_name = f"{prefix}-{hash_id}".lower()
    # Ensure it's max 45 characters and clean
    index_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '-' for c in index_name)
    if len(index_name) > 45:
        index_name = index_name[:45]
    # Remove trailing hyphens
    index_name = index_name.rstrip('-')
    
    # Check if index exists, create if not
    existing_indexes = list_indexes_method()
    if index_name not in existing_indexes:
        logger.info(f"Creating new Pinecone index: {index_name}")
        # Create index with dimension 1536 (OpenAI text-embedding-ada-002 default)
        try:
            create_index_method(
                name=index_name,
                dimension=1536,
                metric="cosine"
            )
            logger.info(f"Successfully created Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Error creating Pinecone index {index_name}: {e}")
            raise
    else:
        logger.info(f"Using existing Pinecone index: {index_name}")
    
    # Connect to the index
    pinecone_index = get_index_method(index_name)
    
    # Check if index already has vectors
    try:
        stats = pinecone_index.describe_index_stats()
        vector_count = stats.get('total_vector_count', 0) if isinstance(stats, dict) else stats.total_vector_count
        has_vectors = vector_count > 0
    except Exception as e:
        logger.warning(f"Could not get index stats for {index_name}: {e}")
        has_vectors = False
    
    # Setup LLM and embedding model
    chat_llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        # model_name="gpt-3.5-turbo",
        temperature=0,
        max_tokens=1024
    )
    llama_llm = LangChainLLM(llm=chat_llm)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
    
    # Create vector store
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    
    # Create storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # If index has vectors, create index wrapper without re-embedding
    if has_vectors:
        logger.info(f"Loading existing Pinecone index with {vector_count} vectors for user {user_id}, doc {document_id}")
        # Create index from existing vector store (no need to re-embed documents)
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            llm=llama_llm,
            embed_model=embed_model
        )
        return index
    else:
        # Index is empty, create new index with documents
        logger.info(f"Creating new Pinecone index for user {user_id}, doc {document_id}")
        documents = SimpleDirectoryReader(input_files=[filepath]).load_data()
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            llm=llama_llm,
            embed_model=embed_model
        )
        logger.info(f"Created and persisted new Pinecone index for user {user_id}, doc {document_id}")
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
            logger.debug(f"Extracted YouTube video ID: {match.group(1)} from URL: {url}")
            return match.group(1)
    logger.error(f"Invalid YouTube URL: {url}")
    raise ValueError("Invalid YouTube URL")

def get_youtube_title(video_id: str) -> str:
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    resp = requests.get(oembed_url)
    if resp.status_code == 200:
        title = resp.json().get("title", "")
        logger.info(f"Fetched YouTube title: {title} for video ID: {video_id}")
        return title
    logger.warning(f"Failed to fetch YouTube title for video ID: {video_id}")
    return ""

def get_youtube_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        logger.info(f"Fetched transcript for video ID: {video_id}")
        return " ".join([x['text'] for x in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        logger.warning(f"Transcript not available for video ID: {video_id}")
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
    logger.info("Summarized YouTube transcript with LLM.")
    return response.content.strip()


