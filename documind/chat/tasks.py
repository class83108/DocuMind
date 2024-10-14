from asgiref.sync import async_to_sync
from celery import shared_task
from django.core.cache import cache
from langchain.prompts import PromptTemplate
from langchain.schema import Document, StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI

from documind.vectorstore import get_vectorstore
from django.conf import settings
from .models import Chat, PDFDocument

import uuid


@shared_task
def save_chat_history(chat_id):
    history_key = f"chat_history_{chat_id}"

    # 從 channel_layer 獲取聊天記錄
    chat_history = cache.get(history_key) or []

    try:
        chat = Chat.objects.get(id=chat_id)

        if chat_history:
            # 更新數據庫中的聊天記錄
            chat.history.extend(chat_history)
            chat.save()

            # 清除 cache 中的臨時記錄
            cache.delete(history_key)

        return f"Chat history saved for room id: {chat_id}"
    except Chat.DoesNotExist:
        return f"Chat with id {chat_id} does not exist"


@shared_task
def store_pdf_vector(chat_id: int, pdf_id: int) -> None:
    try:
        pdf_document = PDFDocument.objects.get(id=pdf_id)
        # 獲取全局 Chroma 客戶端
        vectorstore = get_vectorstore()

        # 文本準備
        text = pdf_document.text

        # 文本分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        # 創建 Document 對象列表
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "chat_id": chat_id,
                    "chunk_index": i,
                },
            )
            for i, chunk in enumerate(chunks)
        ]
        # 生成唯一 ID
        uuids = [str(uuid.uuid4()) for _ in range(len(documents))]

        # 將文章添加到現有的向量存儲中
        vectorstore.add_documents(documents=documents, ids=uuids)

    except Exception as e:
        print(f"Error processing article: {str(e)}")
        raise e


@shared_task
def search_documents_and_answer(query: str, chat_id: int, num_results: int = 5) -> dict:
    vectorstore = get_vectorstore()

    # 執行相似性搜索，只搜索特定 chat_id 的文檔
    results = vectorstore.similarity_search_with_score(
        query,
        k=num_results,
        filter={"chat_id": chat_id},  # 添加 filter 參數來限制搜索範圍
    )

    print(f"Found {len(results)} results for chat_id: {chat_id}")

    if len(results) == 0:
        return {"query": query, "answer": "No results found", "results": []}

    # 格式化結果
    formatted_results = []
    context = ""
    for doc, score in results:
        formatted_results.append(
            {"content": doc.page_content, "metadata": doc.metadata, "score": score}
        )
        context += doc.page_content + "\n\n"

    # 初始化語言模型
    llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)

    # 創建提示模板
    prompt = PromptTemplate(
        input_variables=["context", "query"],
        template="根據以下信息回答問題：\n\n{context}\n\n問題: {query}\n\n答案:",
    )

    # 建立鏈 - 輸入提示，語言模型，輸出解析器
    chain = prompt | llm | StrOutputParser()

    # 調用鏈 - 將上下文和查詢作為輸入取代得答案
    answer = chain.invoke({"context": context, "query": query})

    return {
        "query": query,
        "answer": answer,
        "results": formatted_results,
    }
