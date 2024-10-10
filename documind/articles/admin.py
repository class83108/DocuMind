# articles/admin.py
from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from django.urls import path
from django.shortcuts import render, redirect

from .models import Article
from .tasks import process_and_store_article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("author", "created_at")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "create-with-pdf/",
                self.admin_site.admin_view(self.create_with_pdf_view),
                name="article_create_with_pdf",
            ),
        ]
        return custom_urls + urls

    def create_with_pdf_view(self, request):

        context = dict(
            self.admin_site.each_context(request),
            title="Create Article with PDF Upload",
        )
        if request.method == "GET":
            return render(request, "admin/article_create_with_pdf.html", context)
        if request.method == "POST":
            title = request.POST.get("title")
            content = request.POST.get("content")
            author = request.user

            article = Article.objects.create(
                title=title, content=content, author=author
            )
            try:
                process_and_store_article.apply_async((article.id,))
            except Exception as e:
                article.delete()
                context["error"] = str(e)
                return render(request, "admin/article_create_with_pdf.html", context)

            return redirect("admin:articles_article_changelist")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_create_with_pdf"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            process_and_store_article.apply_async((obj.id,))
        except Exception as e:
            print(f"Error processing article: {str(e)}")
            obj.delete()
            self.message_user(request, f"Error processing article: {str(e)}")

    def search_related_articles_and_find_answer(self, request):
        if request.method == "GET":
            pass
        if request.method == "POST":
            pass
