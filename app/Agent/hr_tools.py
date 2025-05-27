import os

from llama_index.core import StorageContext
from llama_index.llms.langchain import LangChainLLM
from langchain_openai import ChatOpenAI

from llama_index.core import (
            VectorStoreIndex, 
            SimpleDirectoryReader,
            load_index_from_storage,
            ServiceContext,
        )

from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.text_splitter import TokenTextSplitter
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

from dotenv import load_dotenv
load_dotenv()

HR_UPLOAD_DIR = "hr_docs"


def get_hr_storage_path(user_id: str, document_id: str) -> str:
    return os.path.join(HR_UPLOAD_DIR, f"user_{user_id}", f"doc_{document_id}")

def load_or_create_hr_index(filepath: str, user_id: str, document_id: str) -> VectorStoreIndex:
    storage_dir = get_hr_storage_path(user_id, document_id)

    chat_llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0,
        max_tokens=1024
    )
    llama_llm = LangChainLLM(llm=chat_llm)

    embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

    if os.path.exists(storage_dir) and os.listdir(storage_dir):
        storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
        return load_index_from_storage(storage_context, llm=llama_llm)

    # Load and split document into nodes
    raw_docs = SimpleDirectoryReader(input_files=[filepath]).load_data()

    # Use TokenTextSplitter with SimpleNodeParser (apply splitter separately)
    text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=50)
    parser = SimpleNodeParser()
    nodes = parser.get_nodes_from_documents(raw_docs, text_splitter=text_splitter)

    service_context = ServiceContext.from_defaults(
        llm=llama_llm,
        embed_model=embed_model
    )

    index = VectorStoreIndex.from_nodes(
        nodes=nodes,
        service_context=service_context
    )

    index.storage_context.persist(persist_dir=storage_dir)
    return index