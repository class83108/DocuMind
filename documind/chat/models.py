from django.db import models


class Chat(models.Model):
    room_name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="owned_chats"
    )
    history = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.room_name
