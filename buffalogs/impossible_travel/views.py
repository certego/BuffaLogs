import calendar
import json
import os
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Count, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods
from impossible_travel.dashboard.charts import alerts_line_chart, users_pie_chart, world_map_chart
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
from impossible_travel.models import Alert, Login, User


def _load_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/dashboard/", name + ".json"), encoding="utf-8") as file:
        data = json.load(file)
    return data


def user_view(template_name):
    def view_decorator(func):
        def wrapper(request, pk_user):
            context = {"pk_user": pk_user}
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
        date_range = []
        now = timezone.now()
        end_str = now.strftime("%B %-d, %Y")
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_str = start.strftime("%B %-d, %Y")
        date_range.append(start)
        date_range.append(now)
        users_pie_context = users_pie_chart(start, now)
        alerts_line_context = alerts_line_chart(start, now)
        world_map_context = world_map_chart(start, now)

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
            "startdate": start_str,
            "enddate": end_str,
            "users_pie_context": users_pie_context,
            "world_map_context": world_map_context,
            "alerts_line_context": alerts_line_context,
        },
    )


def users(request):
    return render(request, "impossible_travel/users.html")


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
def alerts_line_chart_api(request):
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    date_range = []
    date_str = []
    result = {}
    delta_timestamp = end_date - start_date
    if delta_timestamp.days < 1:
        result["Timeframe"] = "hour"
        while start_date <= end_date:
            date_range.append(start_date)
            date_str.append(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            start_date = start_date + timedelta(minutes=59, seconds=59)
            date_range.append(start_date)
            start_date = start_date + timedelta(seconds=1)
        for i in range(0, len(date_str) - 1, 1):
            result[date_str[i]] = Alert.objects.filter(login_raw_data__timestamp__range=(date_str[i], date_str[i + 1])).count()
    elif delta_timestamp.days >= 1 and delta_timestamp.days <= 31:
        result["Timeframe"] = "day"
        while start_date.day < end_date.day:
            start_date = datetime(start_date.year, start_date.month, start_date.day, 0, 0)
            date_range.append(start_date)
            start_date = start_date + timedelta(hours=23, minutes=59, seconds=59)
            date_range.append(start_date)
            start_date = start_date + timedelta(seconds=1)
        start_date = datetime(start_date.year, start_date.month, start_date.day, 0, 0)
        date_range.append(start_date)
        date_range.append(end_date)
        for i in range(0, len(date_range) - 1, 2):
            date = str(date_range[i].year) + "-" + str(date_range[i].month) + "-" + str(date_range[i].day)
            result[date] = Alert.objects.filter(login_raw_data__timestamp__range=(date_range[i].isoformat(), date_range[i + 1].isoformat())).count()
    else:
        result["Timeframe"] = "month"
        start_date = timezone.datetime(start_date.year, start_date.month, 1)

        if is_naive(start_date):
            start_date = make_aware(start_date)

        while start_date <= end_date:
            date_range.append(datetime(start_date.year, start_date.month, 1))
            date_range.append(datetime(start_date.year, start_date.month, calendar.monthrange(start_date.year, start_date.month)[1]))
            date_str.append(start_date.strftime("%Y-%m"))
            start_date = start_date + relativedelta(months=1)
        for i in range(0, len(date_range) - 1, 2):
            date = str(date_range[i].year) + "-" + str(date_range[i].month)
            result[date] = Alert.objects.filter(login_raw_data__timestamp__range=(date_range[i].isoformat(), date_range[i + 1].isoformat())).count()
    data = json.dumps(result)
    return HttpResponse(data, content_type="json")


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
