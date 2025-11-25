import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class BaseIngestion(ABC):
    """
    Abstract class for ingestion operations.
    """

    class SupportedIngestionSources(Enum):
        """
        Types of possible data ingestion sources.

        * ELASTICSEARCH
        * SPLUNK
        * OPENSEARCH
        * CLOUDTRAIL
        """

        ELASTICSEARCH = "elasticsearch"
        SPLUNK = "splunk"
        OPENSEARCH = "opensearch"
        CLOUDTRAIL = "cloudtrail"

    def __init__(self, ingestion_config, mapping):
        super().__init__()
        self.ingestion_config = ingestion_config
        self.mapping = mapping
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def process_users(self, start_date: datetime, end_date: datetime):
        """
        Extract users logged in between the provided time range.

        :param start_date: start datetime (tzinfo must be UTC)
        :param end_date: end datetime (tzinfo must be UTC)
        """
        raise NotImplementedError

    @abstractmethod
    def process_user_logins(
        self,
        start_date: datetime,
        end_date: datetime,
        username: str,
    ):
        """
        Extract logins of a given user between the provided time range.

        :param username: the username to filter on
        :param start_date: start datetime (UTC)
        :param end_date: end datetime (UTC)
        """
        raise NotImplementedError

    def normalize_fields(self, logins: list) -> list:
        """
        Normalize logs using the mapping in ingestion.json.

        :param logins: list of raw login events
        :return: list of normalized events
        """
        normalized = []
        for login in logins:
            entry = self._normalize_fields(data=login)
            if entry:
                normalized.append(entry)
        return normalized

    def _normalize_fields(self, data: dict) -> dict:
        """
        Normalize a single login event using mapping rules.

        :param data: raw login event
        :return: normalized data or None
        """
        normalized = {}

        for source_key, target_key in self.mapping.items():
            keys = source_key.split(".")
            value = data

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    value = ""
                    break

            normalized[target_key] = value

        required = [
            "timestamp",
            "ip",
            "country",
            "lat",
            "lon",
        ]

        if all(normalized.get(field) for field in required):
            return normalized

        return None
