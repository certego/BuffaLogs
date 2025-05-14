import csv
import json
import os
from collections import defaultdict
from datetime import timedelta

from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Count, Max
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods
from impossible_travel.dashboard.charts import (
    alerts_line_chart,
    user_device_usage_chart,
    user_geo_distribution_chart,
    user_login_frequency_chart,
    user_login_timeline_chart,
    user_time_of_day_chart,
    users_pie_chart,
    world_map_chart,
)
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
from impossible_travel.models import Alert, Login, User


def _load_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/dashboard/", name + ".json"), encoding="utf-8") as file:
        data = json.load(file)
    return data


def user_view(template_name):
    def view_decorator(func):
        def wrapper(request, pk_user):
            user = get_object_or_404(User, pk=pk_user)
            context = {"pk_user": pk_user, "user": user}
            extra_context = func(request, pk_user) if func else {}
            if extra_context:
                context.update(extra_context)
            return render(request, template_name, context)

        return wrapper

    return view_decorator


def homepage(request):
    end_str = timezone.now()
    start_str = end_str - timedelta(days=1)
    users_pie_context = None
    world_map_context = None
    alerts_line_context = None
    if request.method == "GET":
        now = timezone.now()
        # human-readable strings for display
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_str = start.strftime("%B %-d, %Y")
        end_str = now.strftime("%B %-d, %Y")

        # ISO strings for machine use (CSV export)
        iso_start = start.isoformat()
        iso_end = now.isoformat()

        users_pie_context = users_pie_chart(start, now)
        alerts_line_context = alerts_line_chart(start, now)
        world_map_context = world_map_chart(start, now)

        return render(
            request,
            "impossible_travel/homepage.html",
            {
                "startdate": start_str,
                "enddate": end_str,
                "iso_start": iso_start,
                "iso_end": iso_end,
                "users_pie_context": users_pie_context,
                "world_map_context": world_map_context,
                "alerts_line_context": alerts_line_context,
            },
        )

    elif request.method == "POST":
        date_range = json.loads(request.POST["date_range"])
        start = parse_datetime(date_range[0])
        start_str = start.strftime("%B %-d, %Y")
        end = parse_datetime(date_range[1])
        end_str = end.strftime("%B %-d, %Y")
        users_pie_context = users_pie_chart(start, end)
        alerts_line_context = alerts_line_chart(start, end)
        world_map_context = world_map_chart(start, end)

        return render(
            request,
            "impossible_travel/homepage.html",
            {
                # human-readable
                "startdate": start_str,
                "enddate": end_str,
                # ISO (for the CSV-export hidden inputs)
                "iso_start": iso_start,
                "iso_end": iso_end,
                "users_pie_context": users_pie_context,
                "world_map_context": world_map_context,
                "alerts_line_context": alerts_line_context,
            },
        )


def users(request):
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
            "frequency": user_login_frequency_chart(selected_user, start_date, end_date),
        }

    context = {
        "users": users_list,
        "selected_user": selected_user,
        "start_date": start_date.strftime("%B %-d, %Y"),
        "end_date": end_date.strftime("%B %-d, %Y"),
        "charts": {k: (v if isinstance(v, str) else v.render(is_unicode=True)) for k, v in charts.items()},
    }
    return render(request, "impossible_travel/users.html", context)


@user_view("impossible_travel/unique_logins.html")
def unique_logins(request, pk_user):
    return {}


@user_view("impossible_travel/all_logins.html")
def all_logins(request, pk_user):
    return {}


@user_view("impossible_travel/alerts.html")
def alerts(request, pk_user):
    return {}


def get_last_alerts(request):
    context = []
    alerts_list = Alert.objects.all()[:25]
    for alert in alerts_list:
        tmp = {
            "user": alert.user.username,
            "timestamp": alert.login_raw_data["timestamp"],
            "name": alert.name,
        }
        context.append(tmp)
    return JsonResponse(json.dumps(context, default=str), safe=False)


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


def get_alerts(request, pk_user):
    context = []
    alerts_data = Alert.objects.filter(user_id=pk_user).values()
    for raw in range(len(alerts_data) - 1, -1, -1):
        tmp = {
            "timestamp": alerts_data[raw]["login_raw_data"]["timestamp"],
            "rule_name": alerts_data[raw]["name"],
            "rule_desc": alerts_data[raw]["description"],
        }
        context.append(tmp)
    return JsonResponse(json.dumps(context, default=str), safe=False)


def get_users(request):
    context = []
    users_list = User.objects.all().annotate(
        login_count=Count("login", distinct=True), alert_count=Count("alert", distinct=True), last_login=Max("login__timestamp")
    )
    for user in users_list:
        tmp = {
            "id": user.id,
            "user": user.username,
            "last_login": user.last_login,
            "risk_score": user.risk_score,
        }
        tmp["logins_num"] = user.login_count
        tmp["alerts_num"] = user.alert_count
        context.append(tmp)
    return JsonResponse(json.dumps(context, default=str), safe=False)


def get_all_logins(request, pk_user):
    context = []
    count = 0
    end_date = timezone.now()
    start_date = end_date + timedelta(days=-365)
    user_obj = User.objects.filter(id=pk_user)
    username = user_obj[0].username
    ingestion = IngestionFactory().get_ingestion_class()
    user_logins = ingestion.process_user_logins(start_date, end_date, username)
    normalized_user_logins = ingestion.normalize_fields(user_logins)
    return JsonResponse(json.dumps(normalized_user_logins, default=str), safe=False)


@require_http_methods(["GET"])
def users_pie_chart_api(request):
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    result = {
        "no_risk": User.objects.filter(updated__range=(start_date, end_date), risk_score="No risk").count(),
        "low": User.objects.filter(updated__range=(start_date, end_date), risk_score="Low").count(),
        "medium": User.objects.filter(updated__range=(start_date, end_date), risk_score="Medium").count(),
        "high": User.objects.filter(updated__range=(start_date, end_date), risk_score="High").count(),
    }
    data = json.dumps(result)
    return HttpResponse(data, content_type="json")


@require_http_methods(["GET"])
def export_alerts_csv(request):
    """
    Export alerts as CSV for a given ISO8601 start/end window.
    """
    start = request.GET.get("start")
    end = request.GET.get("end")

    if not start or not end:
        return HttpResponseBadRequest("Missing 'start' or 'end' parameter")

    # Restore any "+" signs that URL-decoding may have turned into spaces
    start = start.replace(" ", "+")
    end = end.replace(" ", "+")

    try:
        start_dt = isoparse(start)
        end_dt = isoparse(end)

        if is_naive(start_dt):
            start_dt = make_aware(start_dt)
        if is_naive(end_dt):
            end_dt = make_aware(end_dt)

    except (ValueError, TypeError):
        return HttpResponseBadRequest("Invalid date format for 'start' or 'end'")

    alerts = Alert.objects.filter(created__range=(start_dt, end_dt))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="alerts.csv"'

    writer = csv.writer(response)
    writer.writerow(["timestamp", "username", "alert_name", "description", "is_filtered"])

    for alert in alerts:
        writer.writerow(
            [
                alert.login_raw_data.get("timestamp"),
                alert.user.username,
                alert.name,
                alert.description,
                getattr(alert, "is_filtered", False),
            ]
        )

    return response


@require_http_methods(["GET"])
def alerts_line_chart_api(request):
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    result = {}
    delta_timestamp = end_date - start_date
    if delta_timestamp.days < 1:
        result["Timeframe"] = "hour"
        result.update(aggregate_alerts_interval(start_date, end_date, timedelta(hours=1), "%Y-%m-%dT%H:%M:%SZ"))
    elif delta_timestamp.days <= 31:
        result["Timeframe"] = "day"
        result.update(aggregate_alerts_interval(start_date, end_date, timedelta(days=1), "%Y-%m-%d"))
    else:
        result["Timeframe"] = "month"
        result.update(aggregate_alerts_interval(start_date, end_date, relativedelta(months=1), "%Y-%m"))

    result = {key: value for key, value in result.items()}

    data = json.dumps(result)
    return HttpResponse(data, content_type="json")


def aggregate_alerts_interval(start_date, end_date, interval, date_fmt):
    """
    Helper function to aggregate alerts over an interval
    """
    current_date = start_date
    aggregated_data = {}

    while current_date < end_date:
        next_date = current_date + interval
        count = Alert.objects.filter(login_raw_data__timestamp__range=(current_date.isoformat(), next_date.isoformat())).count()
        aggregated_data[current_date.strftime(date_fmt)] = count
        current_date = next_date
    return aggregated_data


@require_http_methods(["GET"])
def world_map_chart_api(request):
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    countries = _load_data("countries")
    result = []
    tmp = []
    for key, value in countries.items():
        country_alerts = Alert.objects.filter(
            login_raw_data__timestamp__range=(start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
            login_raw_data__country=value,
        )
        if country_alerts:
            for alert in country_alerts:
                if [alert.login_raw_data["country"], alert.login_raw_data["lat"], alert.login_raw_data["lon"]] not in tmp:
                    tmp.append([alert.login_raw_data["country"], alert.login_raw_data["lat"], alert.login_raw_data["lon"]])
                    result.append(
                        {
                            "country": key,
                            "lat": alert.login_raw_data["lat"],
                            "lon": alert.login_raw_data["lon"],
                            "alerts": Alert.objects.filter(
                                login_raw_data__country=value, login_raw_data__lat=alert.login_raw_data["lat"], login_raw_data__lon=alert.login_raw_data["lon"]
                            ).count(),
                        }
                    )
    data = json.dumps(result)
    return HttpResponse(data, content_type="json")


@require_http_methods(["GET"])
def alerts_api(request):
    result = []
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    alerts_list = Alert.objects.filter(created__range=(start_date, end_date))
    for alert in alerts_list:
        tmp = {"timestamp": alert.login_raw_data["timestamp"], "username": User.objects.get(id=alert.user_id).username, "rule_name": alert.name}
        result.append(tmp)
    data = json.dumps(result)
    return HttpResponse(data, content_type="json")


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
def user_login_timeline_api(request, pk):
    """
    API endpoint to retrieve a timeline of user logins within a specified date range.

    Args:
        request: The HTTP request object containing GET parameters 'start' and 'end' for the date range.
        pk: The primary key of the user.

    Returns:
        JsonResponse: A JSON object containing a list of login timestamps for the user.
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

    logins = Login.objects.filter(user=user, timestamp__range=(start_date, end_date)).values_list("timestamp", flat=True)
    login_times = [login.isoformat() for login in logins]

    return JsonResponse({"logins": login_times})


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

    devices = Login.objects.filter(user=user, timestamp__range=(start_date, end_date)).values("user_agent").annotate(count=Count("id"))
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

    daily_logins = [{"date": date.isoformat(), "count": count} for date, count in daily_counts.items()]
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

    countries = _load_data("countries")
    name_to_code = {v.lower(): k for k, v in countries.items()}

    country_counts = {}
    for entry in country_data:
        country_name = entry["country"].lower()
        code = name_to_code.get(country_name)
        if code:
            country_counts[code] = entry["count"]

    return JsonResponse({"countries": country_counts})
