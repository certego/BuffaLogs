import json
from collections import defaultdict
from datetime import timedelta

from dateutil.parser import isoparse
from django.db.models import Count, Max
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods

from impossible_travel.dashboard.charts import (
    user_login_timeline_chart,
)
from impossible_travel.models import Login, User
from impossible_travel.views.utils import load_data


@require_http_methods(["GET"])
def list_users(request):
    """
    GET /api/users/
    """
    context = []
    users_list = User.objects.all().annotate(
        login_count=Count("login", distinct=True),
        alert_count=Count("alert", distinct=True),
        last_login=Max("login__timestamp"),
    )

    for user in users_list:
        context.append(
            {
                "id": user.id,
                "user": user.username,
                "last_login": user.last_login,
                "risk_score": user.risk_score,
                "logins_num": user.login_count,
                "alerts_num": user.alert_count,
            }
        )
    return JsonResponse(json.dumps(context, default=str), safe=False)


@require_http_methods(["GET"])
def detail_user(request, id):
    """
    GET /api/users/<int:id>/
    """
    user = get_object_or_404(User, pk=id)
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "risk_score": user.risk_score,
        "last_login": user.last_login,
    }
    return JsonResponse(data)


@require_http_methods(["GET"])
def risk_score_api(request, id):
    """
    GET /api/users/<int:id>/risk-score/
    """
    user = get_object_or_404(User, pk=id)
    return JsonResponse(
        {"username": user.username, "risk_score": user.risk_score}
    )


@require_http_methods(["GET"])
def user_device_usage_api(request, id):
    start_date, end_date, error = _parse_date_range(request)
    if error:
        return error

    user = get_object_or_404(User, pk=id)

    devices = (
        Login.objects.filter(
            user=user, timestamp__range=(start_date, end_date)
        )
        .values("user_agent")
        .annotate(count=Count("id"))
    )

    return JsonResponse(
        {"devices": {d["user_agent"]: d["count"] for d in devices}}
    )


@require_http_methods(["GET"])
def user_login_frequency_api(request, id):
    start_date, end_date, error = _parse_date_range(request)
    if error:
        return error

    user = get_object_or_404(User, pk=id)
    total_days = (end_date - start_date).days + 1
    daily_counts = {
        (start_date + timedelta(days=i)).date(): 0 for i in range(total_days)
    }

    for login in Login.objects.filter(
        user=user, timestamp__range=(start_date, end_date)
    ):
        daily_counts[login.timestamp.date()] += 1

    return JsonResponse(
        {
            "daily_logins": [
                {"date": str(date), "count": count}
                for date, count in daily_counts.items()
            ]
        }
    )


@require_http_methods(["GET"])
def user_time_of_day_api(request, id):
    start_date, end_date, error = _parse_date_range(request)
    if error:
        return error

    user = get_object_or_404(User, pk=id)
    counts = defaultdict(lambda: defaultdict(int))

    for login in Login.objects.filter(
        user=user, timestamp__range=(start_date, end_date)
    ):
        counts[login.timestamp.hour][login.timestamp.weekday()] += 1

    hourly_data = [
        {"hour": h, "weekdays": [counts[h].get(d, 0) for d in range(7)]}
        for h in range(24)
    ]
    return JsonResponse({"hourly_logins": hourly_data})


@require_http_methods(["GET"])
def user_geo_distribution_api(request, id):
    start_date, end_date, error = _parse_date_range(request)
    if error:
        return error

    user = get_object_or_404(User, pk=id)
    logins = Login.objects.filter(
        user=user, timestamp__range=(start_date, end_date)
    )
    country_data = logins.values("country").annotate(count=Count("id"))

    countries = load_data("countries")
    name_to_code = {v.lower(): k for k, v in countries.items()}

    counts = {
        name_to_code.get(cd["country"].lower(), "unknown"): cd["count"]
        for cd in country_data
        if cd["country"]
    }
    return JsonResponse({"countries": counts})


@require_http_methods(["GET"])
def user_login_timeline_api(request, id):
    start_date, end_date, error = _parse_date_range(request)
    if error:
        return error

    user = get_object_or_404(User, pk=id)
    chart = user_login_timeline_chart(user, start_date, end_date)
    return JsonResponse(
        {
            "timeline": (
                chart
                if isinstance(chart, str)
                else chart.render(is_unicode=True)
            )
        }
    )


# NEW Template-rendering views (for frontend pages)


def all_logins_page(request, pk_user):
    """
    Renders the All Logins page (frontend).
    """
    return render(request, "users/all_logins.html", {"pk_user": pk_user})


def unique_logins_page(request, pk_user):
    """
    Renders the Unique Logins page (frontend).
    """
    return render(request, "users/unique_logins.html", {"pk_user": pk_user})


def user_alerts_page(request, pk_user):
    """
    Renders the User Alerts page (frontend).
    """
    return render(request, "users/alerts.html", {"pk_user": pk_user})


# Helper
def _parse_date_range(request):
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))
    if not start or not end:
        return None, None, HttpResponseBadRequest("Missing 'start' or 'end'")
    if is_naive(start):
        start = make_aware(start)
    if is_naive(end):
        end = make_aware(end)
    return start, end, None
