import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "documind.settings")


# create a new Celery instance
app = Celery("documind", broker=settings.CELERY_BROKER_URL)

# Using a string here means the worker doesn't have to serialize
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
