from django.urls import path
from .views import ArticleView, VectorSearchView, TaskResultView

urlpatterns = [
    path("", ArticleView.as_view(), name="article-view"),
    # path("search/", ArticleView.as_view(), name="article-search"),
    path("search/", VectorSearchView.as_view(), name="article-search"),
    path("task-result/<str:task_id>/", TaskResultView.as_view(), name="task_result"),
]
