from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA
from app.config import CHROMA_DIR
import os

def get_vectorstore(file_path: str, user_id: int):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    docs = loader.load()
    user_dir = os.path.join(CHROMA_DIR, f"user_{user_id}")
    return Chroma.from_documents(
        documents=docs,
        embedding=OpenAIEmbeddings(),
        persist_directory=user_dir
    )

def get_qa_chain(user_id: int):
    user_dir = os.path.join(CHROMA_DIR, f"user_{user_id}")
    vectordb = Chroma(persist_directory=user_dir, embedding_function=OpenAIEmbeddings())
    retriever = vectordb.as_retriever()
    return RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)
