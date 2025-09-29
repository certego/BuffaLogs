import json
import os
from typing import Any

from django.conf import settings


def load_test_data(name: str) -> dict[str, Any]:
    """Utility for returning the data for tests in the tests/test_data folder"""
    with open(file=os.path.join(settings.CERTEGO_DJANGO_IMPOSSIBLE_TRAVEL_APP_DIR, "tests/test_data", name + ".json"), mode="r", encoding="UTF-8") as file:
        data = json.load(file)
    return data


def load_ingestion_config_data(section: str | None = None) -> dict[str, Any]:
    """
    Utility to load the ingestion config file.
    If `section` is provided, returns that subsection of the config.
    Example: section="elasticsearch" will return config["elasticsearch"]
    """
    with open(
        file=os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
        mode="r",
        encoding="utf-8",
    ) as f:
        config_ingestion = json.load(f)

    if section:
        config_ingestion = config_ingestion[section]

    return config_ingestion


def load_index_template(name: str) -> dict[str, Any]:
    """Utility to load the index template"""
    with open(file=os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "elasticsearch/", name + ".json"), mode="r", encoding="UTF-8") as file:
        data = json.load(file)
    return data
