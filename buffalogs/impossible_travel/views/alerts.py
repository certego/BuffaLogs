import csv
import json

from dateutil.parser import isoparse
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods

from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert, User
from impossible_travel.views.utils import get_config_read_write

read_config, write_config = get_config_read_write("alerting.json")


@require_http_methods(["GET"])
def get_export_alerts_csv(request):
    """Export alerts as CSV for a given ISO8601 start/end window."""
    start = request.GET.get("start")
    end = request.GET.get("end")
    if not start or not end:
        return HttpResponseBadRequest("Missing 'start' or 'end' parameter")

    try:
        start_dt = isoparse(start.replace(" ", "+"))
        end_dt = isoparse(end.replace(" ", "+"))
        if is_naive(start_dt):
            start_dt = make_aware(start_dt)
        if is_naive(end_dt):
            end_dt = make_aware(end_dt)
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Invalid date format")

    alerts = Alert.objects.filter(created__range=(start_dt, end_dt))
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
def get_list_alerts(request):
    """Filter all alerts by created datetime range."""
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if not start_date or not end_date:
        return HttpResponseBadRequest("Invalid or missing 'start'/'end' date")

    if is_naive(start_date):
        start_date = make_aware(start_date)
    if is_naive(end_date):
        end_date = make_aware(end_date)

    alerts_list = Alert.objects.filter(created__range=(start_date, end_date))
    result = []
    for alert in alerts_list:
        result.append({
            "timestamp": alert.login_raw_data.get("timestamp"),
            "username": alert.user.username,
            "rule_name": alert.name
        })
    return JsonResponse(result, safe=False)


def get_user_alerts(request):
    """Return all alerts detected for user."""
    result = []
    countries = read_config().get("countries_list", {})  # Adjust to your config structure
    alerts_data = Alert.objects.select_related("user").order_by("-created")

    for alert in alerts_data:
        user = alert.user
        country_code = alert.login_raw_data.get("country", "").lower()
        result.append({
            "timestamp": alert.login_raw_data.get("timestamp"),
            "created": alert.created,
            "notified": alert.notified_status,
            "triggered_by": user.username,
            "rule_name": alert.name,
            "rule_desc": alert.description,
            "is_vip": alert.is_vip,
            "country": countries.get(country_code, "Unknown"),
            "severity_type": getattr(user, "risk_score", "Unknown"),
        })

    return JsonResponse(result, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_recent_alerts(request):
    """Return the most recent 25 alerts."""
    alerts = Alert.objects.select_related("user").order_by("-created")[:25]
    result = [{
        "user": alert.user.username,
        "timestamp": alert.login_raw_data.get("timestamp"),
        "name": alert.name,
    } for alert in alerts]
    return JsonResponse(result, safe=False)


@require_http_methods(["GET"])
def get_alert_types(request):
    """Return all supported alert types."""
    types = [{"alert_type": a.value, "description": a.label} for a in AlertDetectionType]
    return JsonResponse(types, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_alerters_list(request):
    """Return a list of all available alerters (detection types)."""
    alerters = [{"type": a.value, "description": a.label} for a in AlertDetectionType]
    return JsonResponse(alerters, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_active_alerters(request):
    """Return all currently active alerters (for now, all types are active)."""
    active = [{
        "type": a.value,
        "description": a.label,
        "active": True
    } for a in AlertDetectionType]
    return JsonResponse(active, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_alerter_detail(request, type):
    """Return detailed info for a specific alerter (by type)."""
    try:
        alert_type = next(a for a in AlertDetectionType if a.value == type)
    except StopIteration:
        return HttpResponseNotFound(f"Alerter type '{type}' not found")

    detail = {
        "type": alert_type.value,
        "description": alert_type.label,
        "configurable": False,
    }
    return JsonResponse(detail, json_dumps_params={"default": str})
