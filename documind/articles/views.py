from celery.result import AsyncResult
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from documind.vectorstore import get_vectorstore
from rest_framework import views, response, status

from .serializers import ArticleSerializer
from .tasks import search_documents_and_answer


class ArticleView(views.APIView):
    def post(self, request):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class VectorSearchView(View):
    def get(self, request):
        # 獲取 Chroma 向量存儲
        vectorstore = get_vectorstore()

        # 獲取並打印文檔數量
        doc_count = vectorstore._collection.count()
        print(f"Total documents in Chroma: {doc_count}")

        return JsonResponse({"message": "Use POST to search", "doc_count": doc_count})

    def post(self, request):

        # 解析請求數據
        query = request.POST.get("query")
        num_results = request.POST.get("num_results", 5)

        # 調用 Celery 任務
        task_result = search_documents_and_answer.apply_async((query, int(num_results)))

        # 不能直接返回 task_result，因為使用apply_async所以它是一個 AsyncResult 對象
        return JsonResponse({"task_id": task_result.id})


@method_decorator(csrf_exempt, name="dispatch")
class TaskResultView(View):
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        if task_result.ready():
            result = task_result.result
            return JsonResponse({"status": "completed", "result": result})
        else:
            return JsonResponse({"status": "pending"})
