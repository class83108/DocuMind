import time
from celery import shared_task


@shared_task(max_retries=3)
def add_number(x, y):
    time.sleep(10)
    return x + y
