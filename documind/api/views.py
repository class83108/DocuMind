from django.http import HttpResponse
from pdfminer.high_level import extract_text
from rest_framework import views, response, status
import io
import re


class PDFUploadView(views.APIView):
    def post(self, request):
        pdf_file = request.data.get("pdf_file")
        if not pdf_file:
            return response.Response(
                {"error": "No PDF file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pdf_content = pdf_file.read()
            text = extract_text(io.BytesIO(pdf_content))
            # 清理文本
            text = self.clean_text(text)

            # 直接返回文本内容，而不是字典
            return HttpResponse(text, content_type="text/plain")

        except Exception as e:
            return response.Response(
                {"error": "Error processing PDF file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def clean_text(self, text):
        # 删除特殊字符
        text = re.sub(r"[^\w\s\.\,\?\!]", "", text)

        # 將連續的換行符替換為單個換行符
        text = re.sub(r"\n+", "\n", text)

        # 删除行首和行尾的空白字符
        text = "\n".join(line.strip() for line in text.split("\n"))

        return text
