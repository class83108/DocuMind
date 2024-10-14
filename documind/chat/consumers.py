from asgiref.sync import sync_to_async
from celery.result import AsyncResult
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache


# from articles.tasks import search_documents_and_answer
from .tasks import search_documents_and_answer
from .tasks import save_chat_history
from .models import Chat


import asyncio
import json
import time


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # 加入room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # 建立或獲取聊天室
        self.chat = await self.get_or_create_chat(self.scope["user"])

        # 加載聊天歷史記錄
        await self.load_chat_history()

    async def disconnect(self, close_code):
        # 離開room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # 保存聊天歷史記錄
        await self.save_chat_history_async()

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # 將消息添加到聊天歷史記錄
        await self.add_to_chat_history(
            sender=self.scope["user"].username, message=message
        )

        # 發送加載中消息到room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.loading", "message": "正在處理您的請求..."},
        )

        # Start async task
        task = await sync_to_async(search_documents_and_answer.delay)(
            query=message, chat_id=self.chat.id
        )

        # Start checking task result
        await self.check_task_result(task.id)

    # Check task result
    async def check_task_result(self, task_id):
        max_attempts = 60  # 最多等待60秒
        attempts = 0
        while attempts < max_attempts:
            task = AsyncResult(task_id)
            if await sync_to_async(task.ready)():
                result = await sync_to_async(lambda: task.result)()
                # 發送消息到room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "message": result["answer"],
                        "query": result["query"],
                        "results": result["results"],
                    },
                )
                break
            else:
                # Task not ready, wait for 1 second before checking again
                await asyncio.sleep(1)
                attempts += 1

        if attempts >= max_attempts:
            # 如果超過最大嘗試次數，則發送錯誤消息到room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "message": "抱歉，我們無法處理您的請求",
                    "query": "",
                    "results": [],
                },
            )

    # Receive loading message from room group
    async def chat_loading(self, event):
        message = event["message"]
        # Send loading message to WebSocket
        await self.send(text_data=json.dumps({"type": "loading", "message": message}))

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        query = event.get("query", "")
        results = event.get("results", [])

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": message,
                    "query": query,
                    "results": results,
                }
            )
        )

        # 將消息添加到聊天歷史記錄
        await self.add_to_chat_history(sender="DocuMind", message=message)

    @database_sync_to_async
    def get_or_create_chat(self, user):
        chat, _ = Chat.objects.get_or_create(room_name=self.room_name, owner=user)
        return chat

    @database_sync_to_async
    def get_chat_history(self):
        return list(self.chat.history)

    async def load_chat_history(self):
        history = await self.get_chat_history()
        # 將整個歷史記錄作為一個批次發送
        await self.send(text_data=json.dumps({"type": "history", "messages": history}))

    @database_sync_to_async
    def add_to_chat_history(self, sender, message):
        history_key = f"chat_history_{self.chat.id}"
        history = cache.get(history_key) or []
        history.append({"sender": sender, "message": message})
        cache.set(history_key, history, timeout=None)

    async def save_chat_history_async(self):
        save_chat_history.delay(self.chat.id)
