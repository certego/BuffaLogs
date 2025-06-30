import json
import os
from typing import Dict

from django.conf import settings


def load_test_data(name: str) -> Dict:
    """
    Load a JSON test data file from the test_data directory.

    :param name: Name of the JSON file (without extension)
    :type name: str

    :raises FileNotFoundError: If the test data file does not exist
    :raises json.JSONDecodeError: If the file content is not valid JSON

    :return: Parsed JSON data as a dictionary
    :rtype: dict
    """
    path = os.path.join(settings.CERTEGO_DJANGO_IMPOSSIBLE_TRAVEL_APP_DIR, "tests/test_data/", f"{name}.json")
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Test data file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON format in file: {path}", e.doc, e.pos)
