import json
import os

from django.conf import settings


def load_test_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_IMPOSSIBLE_TRAVEL_APP_DIR, "tests/test_data", name + ".json")) as file:
        data = json.load(file)
    return data
