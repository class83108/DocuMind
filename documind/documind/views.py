from django.http import HttpResponse
from .tasks import add_number


def task_view(request):
    task_result = add_number.apply_async((1, 2))
    return HttpResponse(
        f"{task_result.id} is the task id<br />result status: {task_result.status}"
    )
