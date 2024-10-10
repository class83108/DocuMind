from rest_framework import serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "content", "author", "created_at", "updated_at"]
        read_only_fields = ["author", "created_at", "updated_at"]
