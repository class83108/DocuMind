# vectorstore.py
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from django.conf import settings
import os

# 初始化 OpenAI embeddings
embeddings = OpenAIEmbeddings(
    api_key=settings.OPENAI_API_KEY, model="text-embedding-3-large"
)

persist_directory = os.path.join(settings.BASE_DIR, "chroma_db")
vector_store = Chroma(
    persist_directory=persist_directory, embedding_function=embeddings
)


def get_vectorstore():
    return vector_store
