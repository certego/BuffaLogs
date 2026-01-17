from collections import defaultdict
from datetime import timedelta
from functools import wraps
import json

from dateutil.parser import isoparse
from django.db.models import Count, Max
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods
from impossible_travel.dashboard.charts import (
    user_device_usage_chart,
    user_geo_distribution_chart,
    user_login_frequency_chart,
    user_login_timeline_chart,
    user_time_of_day_chart,
)
from impossible_travel.models import Login, User
from impossible_travel.serializers import UserSerializer
from impossible_travel.views.utils import read_config


# Template Views
def unique_login_template_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "impossible_travel/unique_logins.html", {"user": user})


def all_login_template_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "impossible_travel/all_logins.html", {"user": user})


def users_template_view(request):
    users_list = User.objects.all()
    selected_user = None

    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        if user_id:
            selected_user = get_object_or_404(User, pk=user_id)

        if start_date_str:
            start_date = timezone.make_aware(isoparse(start_date_str))
        if end_date_str:
            end_date = timezone.make_aware(isoparse(end_date_str))

    charts = {}
    if selected_user:
        charts = {
            "timeline": user_login_timeline_chart(selected_user, start_date, end_date),
            "geo": user_geo_distribution_chart(selected_user, start_date, end_date),
            "device": user_device_usage_chart(selected_user, start_date, end_date),
            "time_of_day": user_time_of_day_chart(selected_user, start_date, end_date),
            "frequency": user_login_frequency_chart(
                selected_user, start_date, end_date
            ),
        }

    context = {
        "users": users_list,
        "selected_user": selected_user,
        "start_date": start_date.strftime("%B %-d, %Y"),
        "end_date": end_date.strftime("%B %-d, %Y"),
        "charts": {
            k: (v if isinstance(v, str) else v.render(is_unicode=True))
            for k, v in charts.items()
        },
    }
    return render(request, "impossible_travel/users.html", context)


def list_users(request):
    serialized_users = UserSerializer(User.objects)
    return JsonResponse(serialized_users.data, safe=False)


def user_details(request, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    serialized_user = UserSerializer(user)
    return JsonResponse(serialized_user.data, safe=False)


@require_http_methods(["GET"])
def risk_score_api(request):
    result = {}
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    user_risk_list = User.objects.filter(updated__range=(start_date, end_date)).values()
    for key in user_risk_list:
        result[key["username"]] = key["risk_score"]
    data = json.dumps(result)
    return HttpResponse(data, content_type="json")


@require_http_methods(["GET"])
def user_device_usage_api(request, pk):
    """
    API endpoint to retrieve the count of devices used by a user within a specified date range.

    Args:
        request: The HTTP request object containing GET parameters 'start' and 'end' for the date range.
        pk: The primary key of the user.

    Returns:
        JsonResponse: A JSON object containing device usage counts.
    """
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if not start_date or not end_date:
        return HttpResponseBadRequest("Missing start or end date")

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponseNotFound("User not found")

    devices = (
        Login.objects.filter(user=user, timestamp__range=(start_date, end_date))
        .values("user_agent")
        .annotate(count=Count("id"))
    )
    device_counts = {d["user_agent"]: d["count"] for d in devices}

    return JsonResponse({"devices": device_counts})


@require_http_methods(["GET"])
def user_login_frequency_api(request, pk):
    """
    API endpoint to retrieve the daily login frequency of a user within a specified date range.

    Args:
        request: The HTTP request object containing GET parameters 'start' and 'end' for the date range.
        pk: The primary key of the user.

    Returns:
        JsonResponse: A JSON object containing daily login counts.
    """
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if not start_date or not end_date:
        return HttpResponseBadRequest("Missing start or end date")

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponseNotFound("User not found")

    total_days = (end_date - start_date).days + 1
    days = [start_date + timedelta(days=i) for i in range(total_days)]
    daily_counts = {day.date(): 0 for day in days}

    logins = Login.objects.filter(user=user, timestamp__range=(start_date, end_date))
    for login in logins:
        login_day = login.timestamp.date()
        daily_counts[login_day] = daily_counts.get(login_day, 0) + 1

    daily_logins = [
        {"date": date.isoformat(), "count": count}
        for date, count in daily_counts.items()
    ]
    return JsonResponse({"daily_logins": daily_logins})


@require_http_methods(["GET"])
def user_time_of_day_api(request, pk):
    """
    API endpoint to retrieve the distribution of user logins by hour and weekday within a specified date range.

    Args:
        request: The HTTP request object containing GET parameters 'start' and 'end' for the date range.
        pk: The primary key of the user.

    Returns:
        JsonResponse: A JSON object containing hourly login counts grouped by weekday.
    """
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if not start_date or not end_date:
        return HttpResponseBadRequest("Missing start or end date")

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponseNotFound("User not found")

    counts = defaultdict(lambda: defaultdict(int))
    logins = Login.objects.filter(user=user, timestamp__range=(start_date, end_date))
    for login in logins:
        h = login.timestamp.hour
        w = login.timestamp.weekday()
        counts[h][w] += 1

    hourly_data = []
    for hour in range(24):
        weekdays = [counts[hour].get(weekday, 0) for weekday in range(7)]
        hourly_data.append({"hour": hour, "weekdays": weekdays})

    return JsonResponse({"hourly_logins": hourly_data})


@require_http_methods(["GET"])
def user_geo_distribution_api(request, pk):
    """
    API endpoint to retrieve the geographical distribution of user logins within a specified date range.

    Args:
        request: The HTTP request object containing GET parameters 'start' and 'end' for the date range.
        pk: The primary key of the user.

    Returns:
        JsonResponse: A JSON object containing login counts grouped by country.
    """
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if not start_date or not end_date:
        return HttpResponseBadRequest("Missing start or end date")

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return HttpResponseNotFound("User not found")

    logins = Login.objects.filter(user=user, timestamp__range=(start_date, end_date))
    country_data = logins.values("country").annotate(count=Count("id"))

    countries = read_config("countries_list.json")
    name_to_code = {v.lower(): k for k, v in countries.items()}

    country_counts = {}
    for entry in country_data:
        country_name = entry["country"].lower()
        code = name_to_code.get(country_name)
        if code:
            country_counts[code] = entry["count"]

    return JsonResponse({"countries": country_counts})
