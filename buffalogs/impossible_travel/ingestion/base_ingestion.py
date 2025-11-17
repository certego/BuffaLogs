import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


def normalize_login_event(event):
    """
    Extends normalization to include failed/unknown login fields.
    """

    status = event.get("status", "success")
    failure_reason = event.get("failure_reason")

    return {
        "username": event.get("username", ""),
        "ip": event.get("ip", ""),
        "timestamp": event.get("@timestamp") or event.get("timestamp", ""),
        "country": event.get("country", ""),
        "index": event.get("index", ""),
        "event_id": event.get("event_id", ""),
        "user_agent": event.get("user_agent", ""),
        "lat": event.get("lat", ""),
        "lon": event.get("lon", ""),
        "status": status,
        "failure_reason": failure_reason,
    }


class BaseIngestion(ABC):
    """
    Abstract class for ingestion operations
    """

    class SupportedIngestionSources(Enum):
        """Types of possible data ingestion sources

        * ELASTICSEARCH
        * SPLUNK
        * OPENSEARCH
        """

        ELASTICSEARCH = "elasticsearch"
        SPLUNK = "splunk"
        OPENSEARCH = "opensearch"

    def __init__(self, ingestion_config, mapping):
        super().__init__()
        self.ingestion_config = ingestion_config
        self.mapping = mapping
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        raise NotImplementedError

    @abstractmethod
    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        raise NotImplementedError

    def normalize_fields(self, logins: list) -> list:
        normalized_logins = []
        for login in logins:
            normalized_login = self._normalize_fields(data=login)
            if normalized_login:
                normalized_logins.append(normalized_login)
        return normalized_logins

    def _normalize_fields(self, data: dict) -> dict:
        """
        Normalize each login including new fields (status + failure_reason).
        """

        # Step 1 — Apply existing ingestion mapping
        normalized_data = {}

        for ingestion_key, buffalogs_key in self.mapping.items():
            keys = ingestion_key.split(".")
            value = data

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    value = ""

            normalized_data[buffalogs_key] = value

        # Step 2 — Add extra fields (supports failed logins)
        extended = normalize_login_event(data)
        normalized_data.update(extended)

        # Step 3 — Basic validation
        # Only timestamp + IP required (allows failed logins without lat/lon)
        if not normalized_data.get("timestamp") or not normalized_data.get("ip"):
            return None

        return normalized_data
