from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA
from app.config import CHROMA_DIR
import os
from app.logger import get_logger
logger = get_logger(__name__)

def get_vectorstore(file_path: str, user_id: int):
    try:
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)
        docs = loader.load()
        user_dir = os.path.join(CHROMA_DIR, f"user_{user_id}")
        logger.info(f"Loaded {len(docs)} documents for user {user_id} from {file_path}")
        return Chroma.from_documents(
            documents=docs,
            embedding=OpenAIEmbeddings(),
            persist_directory=user_dir
        )
    except Exception as e:
        logger.error(f"Error loading vectorstore for {file_path}: {e}")
        raise

def get_qa_chain(user_id: int):
    try:
        user_dir = os.path.join(CHROMA_DIR, f"user_{user_id}")
        vectordb = Chroma(persist_directory=user_dir, embedding_function=OpenAIEmbeddings())
        retriever = vectordb.as_retriever()
        logger.info(f"QA chain created for user {user_id}")
        return RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
    except Exception as e:
        logger.error(f"Error creating QA chain for user {user_id}: {e}")
        raise
