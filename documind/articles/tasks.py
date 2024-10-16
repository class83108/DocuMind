from celery import shared_task
from django.conf import settings
from langchain.prompts import PromptTemplate
from langchain.schema import Document, StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI


from documind.vectorstore import get_vectorstore
from .models import Article

import uuid


@shared_task
def process_and_store_article(article_id: int) -> None:
    try:
        article = Article.objects.get(id=article_id)
        # 獲取全局 Chroma 客戶端
        vectorstore = get_vectorstore()

        # 獲取該文章的所有現有文檔 ID
        all_docs = vectorstore.get(where={"article_id": article.id})
        if all_docs and all_docs.get("ids"):
            vectorstore.delete(ids=all_docs["ids"])

        # 文本準備
        text = article.content

        # 文本分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        # 轉換article.update_at為字符串
        updated_at = article.updated_at.strftime("%Y-%m-%d %H:%M:%S")

        # 創建 Document 對象列表
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "article_id": article.id,
                    "title": article.title,
                    "chunk_index": i,
                    "updated_at": updated_at,
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
def search_documents_and_answer(query: str, num_results: int = 5) -> dict:

    vectorstore = get_vectorstore()
    # 執行相似性搜索
    results = vectorstore.similarity_search_with_score(query, k=num_results)

    print(f"Found {len(results)} results")

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
