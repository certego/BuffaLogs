import json
import os
from contextlib import contextmanager
from typing import Any, Optional
from unittest.mock import MagicMock, patch

from django.conf import settings


def load_test_data(name: str) -> dict[str, Any]:
    """Utility for returning the data for tests in the tests/test_data folder"""
    with open(
        file=os.path.join(
            settings.CERTEGO_DJANGO_IMPOSSIBLE_TRAVEL_APP_DIR,
            "tests/test_data",
            name + ".json",
        ),
        mode="r",
        encoding="UTF-8",
    ) as file:
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
    with open(
        file=os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "elasticsearch/", name + ".json"),
        mode="r",
        encoding="UTF-8",
    ) as file:
        data = json.load(file)
    return data


@contextmanager
def patched_components(
    patch_ingestion: bool = False,
    patch_detection: bool = False,
    patch_tasksettings: bool = False,
    users_return: Optional[list] = None,
    logins_return: Optional[list] = None,
    normalized_return: Optional[list] = None,
):
    """
    Dynamic/Flexible Patch flessibile for components used in the process_logs function.
        - Ingestion patch: patch_ingestion=True/False with optional return values: users_return, logins_return, normalized_return
        - Detection patch: patch_detection=True/False
        - TaskSettings patch: patch_tasksettings=True/False

    Return a tuple with mocks (or None):
        (ingestion_mock, detection_mock, tasksettings_mock)
    """
    patches = []
    ingestion_mock = None
    detection_mock = None
    tasksettings_mock = None

    if patch_ingestion:
        ingestion_mock = MagicMock()
        ingestion_mock.process_users.return_value = users_return or []
        ingestion_mock.process_user_logins.return_value = logins_return or []
        ingestion_mock.normalize_fields.return_value = normalized_return or []

        p_ing = patch("impossible_travel.tasks.IngestionFactory")

        patches.append(p_ing)

    if patch_detection:
        p_det = patch("impossible_travel.modules.detection.check_fields", autospec=True)
        patches.append(p_det)

    if patch_tasksettings:
        p_task = patch("impossible_travel.tasks.process_logs.TaskSettings.objects.get_or_create")
        patches.append(p_task)

    active_patches = [p.start() for p in patches]

    try:
        if patch_ingestion:
            ingestion_factory_mock = active_patches[0]
            ingestion_factory_mock.return_value.get_ingestion_class.return_value = ingestion_mock

        if patch_detection:
            detection_mock = active_patches[-1] if patch_ingestion else active_patches[0]

        if patch_tasksettings:
            tasksettings_mock = active_patches[-1]

        yield ingestion_mock, detection_mock, tasksettings_mock

    finally:
        for p in patches:
            p.stop()
