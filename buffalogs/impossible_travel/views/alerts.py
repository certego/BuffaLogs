import csv
import json

from dateutil.parser import isoparse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.views.decorators.http import require_http_methods
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert, User
from impossible_travel.views.utils import read_config, write_config


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
    if start_date and is_naive(start_date):
        start_date = make_aware(start_date)
    if end_date and is_naive(end_date):
        end_date = make_aware(end_date)
    if request.GET.get("notified"):
        notified = True if request.GET.get("notified").lower() == "true" else False
    else:
        notified = None
    risk_score = request.GET.get("risk_score")
    min_risk_score = request.GET.get("min_risk_score")
    max_risk_score = request.GET.get("max_risk_score")
    if risk_score:
        risk_score = int(risk_score) if risk_score.isnumeric() else risk_score.title()
    if min_risk_score:
        min_risk_score = int(min_risk_score) if min_risk_score.isnumeric() else min_risk_score.title()
    if max_risk_score:
        max_risk_score = int(max_risk_score) if max_risk_score.isnumeric() else max_risk_score.title()
    filters = dict(
        start_date=start_date,
        end_date=end_date,
        notified=notified,
        name=request.GET.get("name"),
        username=request.GET.get("user"),
        is_vip=request.GET.get("is_vip"),
        country_code=request.GET.get("country_code"),
        login_start_time=request.GET.get("login_start_date"),
        login_end_time=request.GET.get("login_end_date"),
        ip=request.GET.get("ip"),
        user_agent=request.GET.get("user_agent"),
        risk_score=risk_score,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
    )
    alerts = Alert.apply_filters(**filters)
    data = [alert.serialize() for alert in alerts]
    return JsonResponse(data, content_type="json", safe=False, json_dumps_params={"default": str})


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
            "notified": alert.notified,  # alert.notified_status,
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
