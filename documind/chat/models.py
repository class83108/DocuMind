from django.db import models


class Chat(models.Model):
    room_name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="owned_chats"
    )
    history = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_permanent = models.BooleanField(default=False)

    def __str__(self):
        return self.room_name


class PDFDocument(models.Model):
    chatroom = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="pdf_documents"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    text = models.TextField(default="")

    def __str__(self):
        return f"PDF for {self.chatroom.name}"
