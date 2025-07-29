import requests
from buffacli.config import get_buffalogs_url
from buffacli.exception_handlers import request_exception_handler

root_url = get_buffalogs_url()
alert_types_api = root_url / "api/alert_types"
ingestion_api = root_url / "api/ingestion"
alerters_api = root_url / "api/alerters"


@request_exception_handler
def send_request(url, *args, **kwargs):
    req = requests.get(url, *args, **kwargs)
    req.raise_for_status()
    return req


def get_alert_types():
    return send_request(alert_types_api).json()


def get_active_ingestion_source():
    return send_request(ingestion_api / "active_ingestion_source").json()


def get_ingestion_source(source: str):
    return send_request(ingestion_api / source).json()


def get_ingestion_sources():
    return send_request(ingestion_api / "sources").json()


def get_alerters():
    return send_request(alerters_api).json()


def get_active_alerter():
    return send_request(alerters_api / "active-alerter").json()


def get_alerter_config(alerter: str):
    return send_request(alerters_api / f"{alerter}").json()
