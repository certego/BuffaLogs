import json
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
from impossible_travel.models import Login, User
from impossible_travel.serializers import LoginSerializer


def get_user_logins(request, user_id):
    end_date = timezone.now()
    start_date = end_date + timedelta(days=-365)
    user_obj = User.objects.filter(id=user_id)
    username = user_obj[0].username
    ingestion = IngestionFactory().get_ingestion_class()
    user_logins = ingestion.process_user_logins(start_date, end_date, username)
    normalized_user_logins = ingestion.normalize_fields(user_logins)
    return JsonResponse(json.dumps(normalized_user_logins, default=str), safe=False)


def get_user_unique_logins(request, user_id):
    context = []
    logins = Login.objects.filter(user_id=user_id).order_by("-created")
    serialized_logins = LoginSerializer(logins)
    return JsonResponse(serialized_logins.json(), safe=False)


@require_http_methods(["GET", "POST"])
def login_api(request):
    """Filter logins."""
    if request.method == "GET":
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
        serialized_logins = LoginSerializer(logins)
        return JsonResponse(serialized_logins.json(), content_type="json", safe=False, json_dumps_params={"default": str})
