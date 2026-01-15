import sys
from datetime import datetime

import requests
from buffacli.config import get_buffalogs_url
from buffacli.exception_handlers import request_exception_handler
from buffacli.globals import vprint

root_url = get_buffalogs_url()
alert_types_api = root_url / "api/alert_types"
ingestion_api = root_url / "api/ingestion"
alerters_api = root_url / "api/alerters"
alerts_api = root_url / "alerts_api"  # "api/alerts"
login_api = root_url / "api/logins"


@request_exception_handler
def send_request(url, *args, **kwargs):
    vprint("info", f"Requesting: {url}...")
    req = requests.get(url, *args, **kwargs)
    vprint("debug", f"Request Headers: {req.request.headers}")
    vprint("info", f"Response Status Code: {req.status_code}")
    vprint("debug", f"Response Headers: {req.headers}")
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

    return send_request(alerts_api, params=query).json()


def get_logins(
    *,
    username: str = None,
    ip: str = None,
    country: str = None,
    user_agent: str = None,
    login_start_time: datetime = None,
    login_end_time: datetime = None,
    index: str = None,
):
    query = dict(user=username, ip=ip, country=country, user_agent=user_agent, login_start_time=login_start_time, login_end_time=login_end_time, index=index)

    return send_request(login_api, params=query).json()
