from asgiref.sync import async_to_sync
from celery import shared_task
from django.core.cache import cache

from .models import Chat


@shared_task
def save_chat_history(chat_id, room_name):
    history_key = f"chat_history_{room_name}"

    # 從 channel_layer 獲取聊天記錄
    chat_history = cache.get(history_key) or []

    try:
        chat = Chat.objects.get(id=chat_id)

        if chat_history:
            # 更新數據庫中的聊天記錄
            chat.history.extend(chat_history)
            chat.save()

            # 清除 cache 中的臨時記錄
            cache.delete(history_key)

        return f"Chat history saved for room {room_name}"
    except Chat.DoesNotExist:
        return f"Chat with id {chat_id} does not exist"
