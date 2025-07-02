import requests
from buffacli.config import get_buffalogs_url

root_url = get_buffalogs_url()
alert_types_api = root_url / "api/alert_types"
ingestion_api = root_url / "api/ingestion"


def get_alert_types():
    return requests.get(alert_types_api).json()


def get_active_ingestion_source():
    return requests.get(ingestion_api / "active_ingestion_source").json()


def get_ingestion_source(source: str):
    return requests.get(ingestion_api / source).json()


def get_ingestion_sources():
    return requests.get(ingestion_api / "sources").json()
