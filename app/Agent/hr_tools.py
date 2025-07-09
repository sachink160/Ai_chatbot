import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.text_splitter import TokenTextSplitter
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.langchain import LangChainLLM
from langchain_openai import ChatOpenAI
# from llama_index import Settings  # New usage
from llama_index.core.settings import Settings

load_dotenv()

HR_UPLOAD_DIR = "hr_docs"

def get_hr_storage_path(user_id: str, document_id: str) -> str:
    return os.path.join(HR_UPLOAD_DIR, f"user_{user_id}", f"doc_{document_id}")

def load_or_create_hr_index(filepath: str, user_id: str, document_id: str) -> VectorStoreIndex:
    storage_dir = get_hr_storage_path(user_id, document_id)

    # Define the LLM and embedding models
    chat_llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0,
        max_tokens=1024
    )
    llama_llm = LangChainLLM(llm=chat_llm)
    embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

    # Register default settings (only required once per app lifecycle)
    Settings.llm = llama_llm
    Settings.embed_model = embed_model

    if os.path.exists(storage_dir) and os.listdir(storage_dir):
        storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
        return load_index_from_storage(storage_context)

    # Load and parse documents
    raw_docs = SimpleDirectoryReader(input_files=[filepath]).load_data()

    index = VectorStoreIndex.from_documents(
        documents=raw_docs
    )
    index.storage_context.persist(persist_dir=storage_dir)
    return index
