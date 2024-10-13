# articles/admin.py
from django.contrib import admin
from django.urls import path
from django.shortcuts import render

from .models import Chat


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("room_name", "owner", "created_at", "updated_at")
    search_fields = ("room_name", "history")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "create-room/",
                self.admin_site.admin_view(self.create_room_view),
                name="create_chat_room",
            ),
        ]
        return custom_urls + urls

    def create_room_view(self, request):
        context = dict(
            self.admin_site.each_context(request),
            room_name=request.user.username,
            title="New Chat Room",
        )
        if request.method == "GET":
            return render(request, "admin/chat_room.html", context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_create_chat_room"] = True
        return super().changelist_view(request, extra_context=extra_context)
