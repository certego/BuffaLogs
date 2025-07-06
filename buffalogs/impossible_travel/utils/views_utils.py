import json
import os
from datetime import datetime, timedelta
from typing import Dict

from django.conf import settings
from impossible_travel.models import Alert


def load_dashboard_data(name: str) -> dict:
    """
    Load a dashboard JSON file from the 'impossible_travel/dashboard/' directory.

    :param name: Name of the dashboard file (without .json extension)
    :type name: str

    :return: Parsed JSON data as a dictionary
    :rtype: dict
    """
    path = os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/dashboard/", f"{name}.json")
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return data


def aggregate_alerts_interval(start_date: datetime, end_date: datetime, interval: timedelta, date_fmt: str) -> Dict[str, int]:
    """
    Aggregate alert counts over a time interval between start and end dates.

    :param start_date: The beginning of the time range
    :type start_date: datetime
    :param end_date: The end of the time range (exclusive)
    :type end_date: datetime
    :param interval: Time interval (e.g., 1 day, 1 hour) for aggregation
    :type interval: timedelta
    :param date_fmt: Format string for labeling each time bucket (e.g., '%Y-%m-%d')
    :type date_fmt: str

    :return: A dictionary where keys are formatted time buckets and values are alert counts
    :rtype: Dict[str, int]
    """
    current_date = start_date
    aggregated_data: Dict[str, int] = {}

    while current_date < end_date:
        next_date = current_date + interval
        count = Alert.objects.filter(login_raw_data__timestamp__range=(current_date.isoformat(), next_date.isoformat())).count()
        aggregated_data[current_date.strftime(date_fmt)] = count
        current_date = next_date

    return aggregated_data
