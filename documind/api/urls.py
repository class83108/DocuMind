from django.urls import path
from .views import PDFUploadView

urlpatterns = [path("upload-pdf/", PDFUploadView.as_view(), name="upload-pdf")]
