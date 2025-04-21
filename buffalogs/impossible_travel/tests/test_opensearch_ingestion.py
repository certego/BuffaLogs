import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from typing import List

import opensearchpy
from opensearchpy import OpenSearch
from django.conf import settings
from django.test import TestCase
from opensearchpy.helpers import bulk
from opensearchpy import connections
from opensearchpy import connections
from impossible_travel.ingestion.opensearch_ingestion import OpensearchIngestion


def load_ingestion_config_data():
    with open(
            os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
            mode="r",
            encoding="utf-8",
    ) as f:
        config_ingestion = json.load(f)
    return config_ingestion


def load_test_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/tests/test_data/",
                           name + ".json")) as file: data = json.load(file)
    return data


