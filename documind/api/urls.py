from django.urls import path
from .views import PDFUploadView, PDFUploadAndSave

urlpatterns = [
    path("upload-pdf/", PDFUploadView.as_view(), name="upload-pdf"),
    path(
        "upload-pdf-and-save/", PDFUploadAndSave.as_view(), name="upload-pdf-and-save"
    ),
]
