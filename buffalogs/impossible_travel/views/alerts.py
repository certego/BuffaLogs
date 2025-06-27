import csv
import json

from dateutil.parser import isoparse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods

from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert
from impossible_travel.views.utils import load_data


def _parse_datetime_param(param: str):
    try:
        dt = isoparse(param.replace(" ", "+"))
        return make_aware(dt) if is_naive(dt) else dt
    except (ValueError, TypeError):
        return None


@require_http_methods(["GET"])
def export_alerts_csv(request):
    """Export alerts as CSV for a given ISO8601 start/end window."""
    start = _parse_datetime_param(request.GET.get("start", ""))
    end = _parse_datetime_param(request.GET.get("end", ""))

    if not start or not end:
        return HttpResponseBadRequest("Invalid or missing 'start' or 'end' parameter")

    alerts = Alert.objects.filter(created__range=(start, end)).select_related("user")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="alerts.csv"'

    writer = csv.writer(response)
    writer.writerow(["timestamp", "username", "alert_name", "description", "is_filtered"])

    for alert in alerts:
        writer.writerow([
            alert.login_raw_data.get("timestamp"),
            alert.user.username,
            alert.name,
            alert.description,
            getattr(alert, "is_filtered", False),
        ])

    return response


@require_http_methods(["GET"])
def alerts_api(request):
    """Filter alerts by created datetime range."""
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))

    if not start or not end:
        return HttpResponseBadRequest("Missing or invalid 'start'/'end' datetime")

    start = make_aware(start) if is_naive(start) else start
    end = make_aware(end) if is_naive(end) else end

    alerts = Alert.objects.filter(created__range=(start, end)).select_related("user")

    result = [
        {
            "timestamp": alert.login_raw_data.get("timestamp"),
            "username": alert.user.username,
            "rule_name": alert.name,
        }
        for alert in alerts
    ]

    return JsonResponse(result, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_user_alerts(request):
    """Return all alerts detected for users."""
    countries = load_data("countries")
    alerts = Alert.objects.select_related("user").order_by("-created")

    result = []
    for alert in alerts:
        country_code = alert.login_raw_data.get("country", "").lower()
        result.append({
            "timestamp": alert.login_raw_data.get("timestamp"),
            "created": alert.created,
            "notified": alert.notified,
            "triggered_by": alert.user.username,
            "rule_name": alert.name,
            "rule_desc": alert.description,
            "is_vip": alert.is_vip,
            "country": countries.get(country_code, "Unknown"),
            "severity_type": alert.user.risk_score,
        })

    return JsonResponse(result, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_last_alerts(request):
    """Return the last 25 alerts detected."""
    alerts = Alert.objects.select_related("user").order_by("-created")[:25]

    result = [
        {
            "user": alert.user.username,
            "timestamp": alert.login_raw_data.get("timestamp"),
            "name": alert.name,
        }
        for alert in alerts
    ]

    return JsonResponse(result, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def alert_types(request):
    """Return all supported alert types."""
    types = [{"alert_type": t.value, "description": t.label} for t in AlertDetectionType]
    return JsonResponse(types, safe=False, json_dumps_params={"default": str})
