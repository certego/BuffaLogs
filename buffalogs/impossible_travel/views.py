import json
from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Max
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from elasticsearch_dsl import Search, connections
from impossible_travel.dashboard.charts import alerts_line_chart, users_pie_chart, world_map_chart
from impossible_travel.models import Alert, Login, User


def homepage(request):
    if request.method == "GET":
        date_range = []
        now = timezone.now()
        end_str = now.strftime("%B %-d, %Y")
        start = now + timedelta(hours=-now.hour, minutes=-now.minute, seconds=-now.second)
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


def unique_logins(request, pk_user):
    return render(request, "impossible_travel/unique_logins.html")


def all_logins(request, pk_user):
    return render(request, "impossible_travel/all_logins.html")


def alerts(request, pk_user):
    return render(request, "impossible_travel/alerts.html")


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
    alerts = Alert.objects.filter(user_id=pk_user).values()
    for raw in range(len(alerts) - 1, -1, -1):
        tmp = {"timestamp": alerts[raw]["login_raw_data"]["timestamp"], "rule_name": alerts[raw]["name"], "rule_desc": alerts[raw]["description"]}
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
    connections.create_connection(hosts=[settings.CERTEGO_ELASTICSEARCH], timeout=90)
    end_date = timezone.now()
    start_date = end_date + timedelta(days=-365)
    user_obj = User.objects.filter(id=pk_user)
    username = user_obj[0].username
    s = (
        Search(index=settings.CERTEGO_ELASTIC_INDEX)
        .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
        .query("match", **{"user.name": username})
        .exclude("match", **{"event.outcome": "failure"})
        .source(includes=["user.name", "@timestamp", "geoip.latitude", "geoip.longitude", "geoip.country_name", "user_agent.original"])
        .sort("-@timestamp")
        .extra(size=10000)
    )
    response = s.execute()
    for hit in response:
        count = count + 1
        tmp = {"timestamp": hit["@timestamp"]}

        if "geoip" in hit and "country_name" in hit["geoip"]:
            tmp["latitude"] = hit["geoip"]["latitude"]
            tmp["longitude"] = hit["geoip"]["longitude"]
            tmp["country"] = hit["geoip"]["country_name"]
        else:
            tmp["latitude"] = None
            tmp["longitude"] = None
            tmp["country"] = ""
        if "user_agent" in hit:
            tmp["user_agent"] = hit["user_agent"]["original"]
        else:
            tmp["user_agent"] = ""
        context.append(tmp)
    return JsonResponse(json.dumps(context, default=str), safe=False)
