from datetime import timedelta
import json

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
    alerts_line_chart,
    users_pie_chart,
    world_map_chart,
)
from impossible_travel.models import Alert, Login, User
from impossible_travel.views.utils import read_config


def aggregate_alerts_interval(start_date, end_date, interval, date_fmt):
    """
    Helper function to aggregate alerts over an interval
    """
    current_date = start_date
    aggregated_data = {}

    while current_date < end_date:
        next_date = current_date + interval
        count = Alert.objects.filter(
            login_raw_data__timestamp__range=(
                current_date.isoformat(),
                next_date.isoformat(),
            )
        ).count()
        aggregated_data[current_date.strftime(date_fmt)] = count
        current_date = next_date
    return aggregated_data


def homepage(request):
    def build_context(start, end):
        # Ensure timezone-aware datetimes
        if is_naive(start):
            start = make_aware(start)
        if is_naive(end):
            end = make_aware(end)

        return {
            "startdate": start.strftime("%B %-d, %Y"),
            "enddate": end.strftime("%B %-d, %Y"),
            "iso_start": start.isoformat(),
            "iso_end": end.isoformat(),
            "users_pie_context": users_pie_chart(start, end),
            "world_map_context": world_map_chart(start, end),
            "alerts_line_context": alerts_line_chart(start, end),
        }

    if request.method == "GET":
        now = timezone.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return render(
            request, "impossible_travel/homepage.html", build_context(start, now)
        )

    if request.method == "POST":
        # Validate POST payload
        try:
            date_range = json.loads(request.POST["date_range"])
            start = parse_datetime(date_range[0])
            end = parse_datetime(date_range[1])
        except Exception:
            return HttpResponseBadRequest("Invalid date range")

        return render(
            request, "impossible_travel/homepage.html", build_context(start, end)
        )

    return HttpResponseBadRequest("Unsupported method")


@require_http_methods(["GET"])
def users_pie_chart_api(request):
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    result = {
        "no_risk": User.objects.filter(
            updated__range=(start_date, end_date), risk_score="No risk"
        ).count(),
        "low": User.objects.filter(
            updated__range=(start_date, end_date), risk_score="Low"
        ).count(),
        "medium": User.objects.filter(
            updated__range=(start_date, end_date), risk_score="Medium"
        ).count(),
        "high": User.objects.filter(
            updated__range=(start_date, end_date), risk_score="High"
        ).count(),
    }
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

    countries = read_config("countries_list.json")
    result = []
    tmp = []
    for key, value in countries.items():
        country_alerts = Alert.objects.filter(
            login_raw_data__timestamp__range=(
                start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            ),
            login_raw_data__country__iexact=key,
        )
        if country_alerts:
            for alert in country_alerts:
                if [
                    alert.login_raw_data["country"],
                    alert.login_raw_data["lat"],
                    alert.login_raw_data["lon"],
                ] not in tmp:
                    tmp.append(
                        [
                            alert.login_raw_data["country"],
                            alert.login_raw_data["lat"],
                            alert.login_raw_data["lon"],
                        ]
                    )
                    result.append(
                        {
                            "country": value.lower(),
                            "lat": alert.login_raw_data["lat"],
                            "lon": alert.login_raw_data["lon"],
                            "alerts": Alert.objects.filter(
                                login_raw_data__country__iexact=key,
                                login_raw_data__lat=alert.login_raw_data["lat"],
                                login_raw_data__lon=alert.login_raw_data["lon"],
                            ).count(),
                        }
                    )
    return HttpResponse(json.dumps(result), content_type="application/json")


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
        result.update(
            aggregate_alerts_interval(
                start_date, end_date, timedelta(hours=1), "%Y-%m-%dT%H:%M:%SZ"
            )
        )
    elif delta_timestamp.days <= 31:
        result["Timeframe"] = "day"
        result.update(
            aggregate_alerts_interval(
                start_date, end_date, timedelta(days=1), "%Y-%m-%d"
            )
        )
    else:
        result["Timeframe"] = "month"
        result.update(
            aggregate_alerts_interval(
                start_date, end_date, relativedelta(months=1), "%Y-%m"
            )
        )

    result = {key: value for key, value in result.items()}

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

    logins = Login.objects.filter(
        user=user, timestamp__range=(start_date, end_date)
    ).values_list("timestamp", flat=True)
    login_times = [login.isoformat() for login in logins]

    return JsonResponse({"logins": login_times})
