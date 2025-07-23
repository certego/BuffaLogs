import requests
from buffacli.config import get_buffalogs_url

root_url = get_buffalogs_url()
alert_types_api = root_url / "api/alert_types"
ingestion_api = root_url / "api/ingestion"
alerters_api = root_url / "api/alerters"


def get_alert_types():
    return requests.get(alert_types_api).json()


def get_active_ingestion_source():
    return requests.get(ingestion_api / "active_ingestion_source").json()


def get_ingestion_source(source: str):
    return requests.get(ingestion_api / source).json()


def get_ingestion_sources():
    return requests.get(ingestion_api / "sources").json()

def get_alerters():
    return requests.get(alerters_api).json()


def get_active_alerter():
    return requests.get(alerters_api / "active-alerter").json()


def get_alerter_config(alerter: str):
    return requests.get(alerters_api / f"{alerter}").json()