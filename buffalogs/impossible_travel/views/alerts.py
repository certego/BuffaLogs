import csv
import json
from dateutil.parser import isoparse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, HttpResponseNotFound
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods

from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert, User
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
    start = request.GET.get("start")
    end = request.GET.get("end")
    if not start or not end:
        return HttpResponseBadRequest("Missing 'start' or 'end' parameter")

    try:
        start_dt = isoparse(start.replace(" ", "+"))
        end_dt = isoparse(end.replace(" ", "+"))
        if is_naive(start_dt): start_dt = make_aware(start_dt)
        if is_naive(end_dt): end_dt = make_aware(end_dt)
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
def list_alerts(request):
    """Filter all alerts by created datetime range."""
    start_date = parse_datetime(request.GET.get("start", ""))
    end_date = parse_datetime(request.GET.get("end", ""))

    if is_naive(start_date): start_date = make_aware(start_date)
    if is_naive(end_date): end_date = make_aware(end_date)

    alerts = Alert.objects.filter(created__range=(start_date, end_date)).select_related("user")
    result = [{
        "timestamp": alert.login_raw_data.get("timestamp"),
        "username": alert.user.username,
        "rule_name": alert.name,
    } for alert in alerts]

    return JsonResponse(result, safe=False)


@require_http_methods(["GET"])
def user_alerts(request, id):
    """Return all alerts detected for a specific user."""
    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        return HttpResponseNotFound("User not found")

    countries = load_data("countries")
    alerts = Alert.objects.filter(user=user).order_by("-created")

    result = []
    for alert in alerts:
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
            "severity_type": user.risk_score,
        })

    return JsonResponse(result, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def recent_alerts(request):
    """Return the most recent 25 alerts."""
    alerts = Alert.objects.select_related("user").order_by("-created")[:25]
    result = [{
        "user": alert.user.username,
        "timestamp": alert.login_raw_data.get("timestamp"),
        "name": alert.name,
    } for alert in alerts]

    return JsonResponse(result, safe=False)


@require_http_methods(["GET"])
def alert_types(request):
    """Return all supported alert types."""
    types = [{"alert_type": a.value, "description": a.label} for a in AlertDetectionType]
    return JsonResponse(types, safe=False, json_dumps_params={"default": str})
