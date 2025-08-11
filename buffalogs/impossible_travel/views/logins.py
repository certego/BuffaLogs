import json
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
from impossible_travel.models import Login, User


def get_all_logins(request, pk_user):
    end_date = timezone.now()
    start_date = end_date + timedelta(days=-365)
    user_obj = User.objects.filter(id=pk_user)
    username = user_obj[0].username
    ingestion = IngestionFactory().get_ingestion_class()
    user_logins = ingestion.process_user_logins(start_date, end_date, username)
    normalized_user_logins = ingestion.normalize_fields(user_logins)
    return JsonResponse(json.dumps(normalized_user_logins, default=str), safe=False)


def get_unique_logins(request, pk_user):
    context = []
    logins_list = Login.objects.filter(user_id=pk_user).values()
    for raw in range(len(logins_list) - 1, -1, -1):
        tmp = {
            "timestamp": logins_list[raw]["timestamp"],
            "country": logins_list[raw]["country"],
            "user_agent": logins_list[raw]["user_agent"],
        }
        context.append(tmp)
    return JsonResponse(json.dumps(context, default=str), safe=False)


@require_http_methods(["GET"])
def login_api(request):
    """Filter logins."""
    result = []
    filters = dict(
        username=request.GET.get("user"),
        country=request.GET.get("country"),
        login_start_time=request.GET.get("login_start_date"),
        login_end_time=request.GET.get("login_end_date"),
        ip=request.GET.get("ip"),
        user_agent=request.GET.get("user_agent"),
    )
    logins = Login.apply_filters(**filters)
    data = [login.serialize() for login in logins]
    return JsonResponse(data, content_type="json", safe=False, json_dumps_params={"default": str})
