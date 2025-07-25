import json
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods

from impossible_travel.dashboard.charts import (
    alerts_line_chart as compute_alerts_line_chart,
)
from impossible_travel.dashboard.charts import (
    users_pie_chart as compute_users_pie_chart,
)
from impossible_travel.dashboard.charts import (
    world_map_chart as compute_world_map_chart,
)
from impossible_travel.models import Alert, Login, User
from impossible_travel.views.utils import aggregate_alerts_interval, load_data


def homepage(request):
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now

    context = {
        "startdate": start.strftime("%B %-d, %Y"),
        "enddate": end.strftime("%B %-d, %Y"),
        "iso_start": start.isoformat(),
        "iso_end": end.isoformat(),
        "users_pie_context": compute_users_pie_chart(start, end),
        "alerts_line_context": compute_alerts_line_chart(start, end),
        "world_map_context": compute_world_map_chart(start, end),
    }

    if request.method == "POST":
        date_range = json.loads(request.POST["date_range"])
        start = parse_datetime(date_range[0])
        end = parse_datetime(date_range[1])
        context.update(
            {
                "startdate": start.strftime("%B %-d, %Y"),
                "enddate": end.strftime("%B %-d, %Y"),
                "iso_start": start.isoformat(),
                "iso_end": end.isoformat(),
                "users_pie_context": compute_users_pie_chart(start, end),
                "alerts_line_context": compute_alerts_line_chart(start, end),
                "world_map_context": compute_world_map_chart(start, end),
            }
        )

    return render(request, "impossible_travel/homepage.html", context)


@require_http_methods(["GET"])
def users_pie_chart(request):
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))

    if is_naive(start):
        start = make_aware(start)
    if is_naive(end):
        end = make_aware(end)

    result = {
        "no_risk": User.objects.filter(
            updated__range=(start, end), risk_score="No risk"
        ).count(),
        "low": User.objects.filter(
            updated__range=(start, end), risk_score="Low"
        ).count(),
        "medium": User.objects.filter(
            updated__range=(start, end), risk_score="Medium"
        ).count(),
        "high": User.objects.filter(
            updated__range=(start, end), risk_score="High"
        ).count(),
    }

    return JsonResponse(result)


@require_http_methods(["GET"])
def world_map(request):
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))

    if is_naive(start):
        start = make_aware(start)
    if is_naive(end):
        end = make_aware(end)

    countries = load_data("countries")
    result = []
    seen = set()

    for code, name in countries.items():
        alerts = Alert.objects.filter(
            login_raw_data__timestamp__range=(
                start.isoformat(),
                end.isoformat(),
            ),
            login_raw_data__country=name,
        )
        for alert in alerts:
            key = (
                alert.login_raw_data["country"],
                alert.login_raw_data["lat"],
                alert.login_raw_data["lon"],
            )
            if key not in seen:
                seen.add(key)
                result.append(
                    {
                        "country": code,
                        "lat": alert.login_raw_data["lat"],
                        "lon": alert.login_raw_data["lon"],
                        "alerts": Alert.objects.filter(
                            login_raw_data__country=name,
                            login_raw_data__lat=alert.login_raw_data["lat"],
                            login_raw_data__lon=alert.login_raw_data["lon"],
                        ).count(),
                    }
                )

    return JsonResponse(result, safe=False)


@require_http_methods(["GET"])
def alerts_line_chart(request):
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))

    if is_naive(start):
        start = make_aware(start)
    if is_naive(end):
        end = make_aware(end)

    delta = end - start
    result = {}

    if delta.days < 1:
        result["Timeframe"] = "hour"
        result.update(
            aggregate_alerts_interval(
                start, end, timedelta(hours=1), "%Y-%m-%dT%H:%M:%SZ"
            )
        )
    elif delta.days <= 31:
        result["Timeframe"] = "day"
        result.update(
            aggregate_alerts_interval(
                start, end, timedelta(days=1), "%Y-%m-%d"
            )
        )
    else:
        result["Timeframe"] = "month"
        result.update(
            aggregate_alerts_interval(
                start, end, relativedelta(months=1), "%Y-%m"
            )
        )

    return JsonResponse(result)


@require_http_methods(["GET"])
def user_login_timeline(request, id):
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))

    if not start or not end:
        return HttpResponseBadRequest("Missing start or end date")

    if is_naive(start):
        start = make_aware(start)
    if is_naive(end):
        end = make_aware(end)

    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        return HttpResponseNotFound("User not found")

    logins = Login.objects.filter(
        user=user, timestamp__range=(start, end)
    ).values_list("timestamp", flat=True)
    return JsonResponse({"logins": [ts.isoformat() for ts in logins]})
