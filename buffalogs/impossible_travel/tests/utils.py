import json
import os

from django.conf import settings


def load_test_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_IMPOSSIBLE_TRAVEL_APP_DIR, "tests/test_data", name + ".json")) as file:
        data = json.load(file)
    return data


def load_ingestion_config_data():
    with open(
        os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
        mode="r",
        encoding="utf-8",
    ) as f:
        config_ingestion = json.load(f)
    return config_ingestion
