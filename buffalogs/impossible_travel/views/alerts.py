import csv
import json

from dateutil.parser import isoparse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert, User
from impossible_travel.views.utils import load_data


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
def alerts_api(request):
    """Filter alerts by created datetime range."""
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


def get_user_alerts(request):
    """Return all alerts detected for user."""
    context = []
    countries = load_data("countries")
    alerts_data = Alert.objects.select_related("user").all().order_by("-created")
    for alert in alerts_data:
        country_code = alert.login_raw_data.get("country", "").lower()
        country_name = countries.get(country_code, "Unknown")
        tmp = {
            "timestamp": alert.login_raw_data.get("timestamp"),
            "created": alert.created,
            "notified": alert.notified,
            "triggered_by": alert.user.username,
            "rule_name": alert.name,
            "rule_desc": alert.description,
            "is_vip": alert.is_vip,
            "country": country_name,
            "severity_type": alert.user.risk_score,
        }
        context.append(tmp)

    return JsonResponse(context, safe=False, json_dumps_params={"default": str})


def get_last_alerts(request):
    """Return the last 25 alerts detected."""
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


@require_http_methods(["GET"])
def alert_types(request):
    """Return all supported alert types."""
    alert_types = [{"alert_type": alert.value, "description": alert.label} for alert in AlertDetectionType]
    return JsonResponse(alert_types, safe=False, json_dumps_params={"default": str})
