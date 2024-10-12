import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from articles.tasks import search_documents_and_answer
from celery.result import AsyncResult
import time


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # 加入room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # 離開room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print(f"Received message: {message}")

        # 發送加載中消息到room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {"type": "chat.loading", "message": "正在處理您的請求..."},
        )

        # Start async task
        task = search_documents_and_answer.delay(message)

        # Start checking task result
        self.check_task_result(task.id)

    # Check task result
    def check_task_result(self, task_id):
        max_attempts = 60  # 最多等待60秒
        attempts = 0
        while attempts < max_attempts:
            task = AsyncResult(task_id)
            if task.ready():
                result = task.result
                # 發送消息到room group
                async_to_sync(self.channel_layer.group_send)(
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
                time.sleep(1)
                attempts += 1

        if attempts >= max_attempts:
            # 如果超過最大嘗試次數，則發送錯誤消息到room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "message": "抱歉，我們無法處理您的請求",
                    "query": "",
                    "results": [],
                },
            )

    # Receive loading message from room group
    def chat_loading(self, event):
        message = event["message"]
        # Send loading message to WebSocket
        self.send(text_data=json.dumps({"type": "loading", "message": message}))

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        query = event.get("query", "")
        results = event.get("results", [])

        # Send message to WebSocket
        self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": message,
                    "query": query,
                    "results": results,
                }
            )
        )
