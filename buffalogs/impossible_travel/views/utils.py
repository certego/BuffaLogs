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


def get_country_validation_sets():
    """
    Loads country data from countries.json and returns a tuple:
    (VALID_COUNTRY_NAMES, VALID_COUNTRY_CODES)
    """
    try:
        data = load_data("countries")
        valid_country_names = set(data.keys())
        valid_country_codes = set(data.values())
        return valid_country_names, valid_country_codes
    except FileNotFoundError:
        return set(), set()
