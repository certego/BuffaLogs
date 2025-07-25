import json
import os
from functools import partial
from pathlib import Path

from django.conf import settings

from impossible_travel.models import Alert


def load_data(name):
    with open(
        os.path.join(
            settings.CERTEGO_DJANGO_PROJ_BASE_DIR,
            "impossible_travel/dashboard/",
            name + ".json",
        ),
        encoding="utf-8",
    ) as file:
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
        count = Alert.objects.filter(
            login_raw_data__timestamp__range=(
                current_date.isoformat(),
                next_date.isoformat(),
            )
        ).count()
        aggregated_data[current_date.strftime(date_fmt)] = count
        current_date = next_date
    return aggregated_data


def read_config(filename: str, key: str | None = None):
    config_path = (
        Path(settings.CERTEGO_BUFFALOGS_CONFIG_PATH) / f"buffalogs/{filename}"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        if key:
            return config[key]
        return config


def write_config(filename, key: str, updates: dict[str, str]):
    config_path = (
        Path(settings.CERTEGO_BUFFALOGS_CONFIG_PATH) / f"buffalogs/{filename}"
    )
    config = read_config(filename)
    config[key] = updates
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(f, config, indent=2)


def get_config_read_write(config_filename):
    return (
        partial(read_config, filename=config_filename),
        partial(write_config, filename=config_filename),
    )
