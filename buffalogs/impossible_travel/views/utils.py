import json
import os

from django.conf import settings
from impossible_travel.models import Alert


def load_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/dashboard/", name + ".json"), encoding="utf-8") as file:
        data = json.load(file)
    return data


def aggregate_alerts_interval(start_date, end_date, interval, date_fmt):
    """
    Helper function to aggregate alerts over an interval
    """
    current_date = start_date
    aggregated_data = {}

    while current_date < end_date:
        next_date = current_date + interval
        count = Alert.objects.filter(login_raw_data__timestamp__range=(current_date.isoformat(), next_date.isoformat())).count()
        aggregated_data[current_date.strftime(date_fmt)] = count
        current_date = next_date
    return aggregated_data
