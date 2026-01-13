import csv
import json

from dateutil.parser import isoparse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods
from impossible_travel.constants import AlertDetectionType
from buffalogs.impossible_travel.models import Alert, User
from buffalogs.impossible_travel.serializers import AlertSerializer
from impossible_travel.validators import validate_alert_query
from buffalogs.impossible_travel.views.utils import read_config, write_config


def alert_template_view(request, user_id=None):
    if user_id:
        user = get_object_or_404(User, pk=user_id)
        return render(request, "impossible_travel/alerts.html", {"user": user})
    return render(request, "impossible_travel/alerts.html")


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
def list_alerts(request):
    """Filter alerts by created datetime range."""
    query = validate_alert_query(request.GET)
    serialized_alerts = AlertSerializer(query=query)
    return JsonResponse(serialized_alerts.data, safe=False, json_dumps_params={"default": str})


def get_user_alerts(request):
    """Return all alerts detected for user."""
    context = []
    countries = read_config("countries_list.json")
    alerts_data = Alert.objects.select_related("user").all().order_by("-created")
    for alert in alerts_data:
        country_code = alert.login_raw_data.get("country", "").lower()
        country_name = countries.get(country_code, "Unknown")
        tmp = {
            "timestamp": alert.login_raw_data.get("timestamp"),
            "created": alert.created,
            "notified": False,  # alert.notified,  # alert.notified_status,
            "triggered_by": alert.user.username,
            "rule_name": alert.name,
            "rule_desc": alert.description,
            "is_vip": alert.is_vip,
            "country": country_name,
            "severity_type": alert.user.risk_score,
        }
        context.append(tmp)

    return JsonResponse(context, safe=False, json_dumps_params={"default": str})


def recent_alerts(request):
    """Return the last 25 alerts detected."""
    alerts_list = Alert.objects.all()[:25]
    serialized_alerts = AlertSerializer(instance=alerts_list)
    return JsonResponse(serialized_alerts.json(), safe=False)


@require_http_methods(["GET"])
def alert_types(request):
    """Return all supported alert types."""
    alert_types = [{"alert_type": alert.value, "description": alert.label} for alert in AlertDetectionType]
    return JsonResponse(alert_types, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_alerters(request):
    config = read_config("alerting.json")
    config.pop("active_alerters")
    alerters = [
        {"alerter": alerter, "fields": [field for field in config[alerter].keys() if field != "options"], "options": list(config[alerter].get("options", []))}
        for alerter in config.keys()
        if alerter != "dummy"
    ]
    return JsonResponse(alerters, safe=False, json_dumps_params={"default": str})


@require_http_methods(["GET"])
def get_active_alerter(request):
    alert_config = read_config("alerting.json")
    active_alerters = alert_config["active_alerters"]
    alerter_config = [{"alerter": alerter, "fields": alert_config[alerter]} for alerter in active_alerters]
    return JsonResponse(alerter_config, safe=False, json_dumps_params={"default": str})


def alerter_config(request, alerter):
    try:
        alerter_config = read_config("alerting.json", key=alerter)
    except KeyError:
        return JsonResponse({"message": f"Unsupported alerter - {alerter}"}, status=400)

    if request.method == "GET":
        content = {"alerter": alerter, "fields": dict((field, alerter_config[field]) for field in alerter_config.keys())}
        return JsonResponse(content, json_dumps_params={"default": str})

    if request.method == "POST":
        config_update = json.loads(request.body.decode("utf-8"))
        error_fields = [field for field in config_update.keys() if field not in alerter_config.keys()]
        if any(error_fields):
            return JsonResponse({"message": f"Unexpected configuration fields - {error_fields}"}, status=400)
        else:
            alerter_config.update(config_update)
            write_config("alerting.json", alerter, alerter_config)
            return JsonResponse({"message": "Update successful"}, status=200)
