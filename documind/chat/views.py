from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()


def chat_view(request, user_name):
    try:
        user = User.objects.get(username=user_name)
    except User.DoesNotExist:
        return HttpRequest("User not found", status=404)
    room_name = user.username
    return render(request, "admin/chat_room.html", {"room_name": room_name})
