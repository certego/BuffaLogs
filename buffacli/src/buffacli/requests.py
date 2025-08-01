import sys
from datetime import datetime

import requests
from buffacli.config import get_buffalogs_url

root_url = get_buffalogs_url()
alert_types_api = root_url / "api/alert_types"
ingestion_api = root_url / "api/ingestion"
alerters_api = root_url / "api/alerters"
alerts_api = root_url / "alerts_api"  # "api/alerts"


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


def get_alerts(
    *,
    start_date: datetime = None,
    end_date: datetime = None,
    name: str = None,
    username: str = None,
    ip: str = None,
    country: str = None,
    is_vip: bool = None,
    notified: bool = None,
    filtered: bool = None,
    min_risk_score: int = None,
    max_risk_score: int = None,
    risk_score: int = None,
    user_agent: str = None,
    login_start_time: datetime = None,
    login_end_time: datetime = None,
):
    query = dict(
        start_date=start_date,
        end_date=end_date,
        name=name,
        user=username,
        ip=ip,
        country=country,
        is_vip=is_vip,
        notified=notified,
        filtered=filtered,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        risk_score=risk_score,
        user_agent=user_agent,
        login_start_time=login_start_time,
        login_end_time=login_end_time,
    )

    return requests.get(alerts_api, params=query).json()
