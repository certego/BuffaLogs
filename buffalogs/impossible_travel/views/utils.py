from functools import partial
import json
import os

from django.conf import settings


def read_config(filename: str, key: str | None = None):
    config_path = os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs", filename)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        if key:
            return config[key]
        return config


def write_config(filename, key: str, updates: dict[str, str]):
    config_path = os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs", filename)
    config = read_config(filename)
    config[key] = updates
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(f, config, indent=2)


def get_config_read_write(config_filename):
    return (
        partial(read_config, filename=config_filename),
        partial(write_config, filename=config_filename),
    )
