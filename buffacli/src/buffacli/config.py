import configparser
import json
import os
from importlib.resources import files
from pathlib import Path

from yarl import URL

project_dir = Path(__file__).parent
config_path: Path = files("buffacli") / "config.json"

DEFAULT_BUFFALOGS_URL = "http://127.0.0.1:8000"


def load_default_config() -> dict:
    config_path: Path = files("buffacli") / "config.json"
    with open(config_path, "r") as f:
        config_data = json.load(f)
    return config_data


def read_from_config(key):
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    custom_config_path = Path(os.path.expanduser(config["custom_config_path"]))
    if custom_config_path.is_file():
        with open(custom_config_path, "r") as f:
            # Add dummy section
            config_string = "[DUMMY]\n" + f.read()

        config_parser = configparser.ConfigParser(allow_no_value=True)
        custom_config = config_parser.read_string(config_string)
        config.update(dict(custom_config.items("DUMMY")))
    return config[key]


def write_to_config(key, value):
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    if key not in config:
        return
    config[key] = value
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=2)


def get_buffalogs_url():
    return URL(os.environ.get("BUFFALOGS_URL") or read_from_config("buffalogs_url"))
