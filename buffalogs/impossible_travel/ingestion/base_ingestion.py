import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

from impossible_travel.models import User


class BaseIngestion(ABC):
    """
    Abstract class for ingestion operations
    """

    class SupportedIngestionSources(Enum):
        """Types of possible data ingestion sources

        * ELASTICSEARCH: The login data is extracted from Elasticsearch
        * OPENSEARCH: The login data is extracted from Opensearch
        """

        ELASTICSEARCH = "elasticsearch"
        OPENSEARCH = "opensearch"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        """Abstract method that implement the extraction of the users logged in between the time range considered defined by (start_date, end_date).
        This method will be different implemented based on the ingestion source used.

        :param start_date: the initial datetime from which the users are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the users are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: list of users strings that logged in the system
        :rtype: list
        """
        raise NotImplementedError

    @abstractmethod
    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        """Abstract method that implement the extraction of the logins of the given user in the time range defined by (start_date, end_date)
        This method will be different implemented based on the ingestion source used.

        :param username: username of the user that logged in
        :type username: str
        :param start_date: the initial datetime from which the logins of the user are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the logins of the user are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: list of logins of a user
        :rtype: list
        """
        raise NotImplementedError

    def _normalize_fields(self, logins: list, mapping: dict) -> list:
        """Concrete method that manage the mapping into the required BuffaLogs mapping.
        The mapping used is defined into the ingestion.json file "custom_mapping" if defined, otherwise it is used the default one

        :param logins: the logins to be normalized into the mapping fields
        :type logins: list
        :param mapping: the mapping fields into which fit the login data
        :type mapping: dict

        :return: the final normalized list of normalized logins
        :rtype: list
        """
        normalized_logins = []
        for login in logins:
            normalized_data = {}

            # Normalize each login based on the mapping
            for ingestion_key, buffalogs_key in mapping.items():
                # Split the key in case it's nested (ex. 'source.geo.location.lat')
                keys = ingestion_key.split(".")
                value = login

                # Traverse the nested keys to extract the correct value
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        value = ""  # Return empty string if the path doesn't exist

                # Add the value to the normalized data
                normalized_data[buffalogs_key] = value

                # Skip logins without timestamp, ip, country, latitude or longitude
                if (
                    normalized_data.get("timestamp")
                    and normalized_data.get("ip")
                    and normalized_data.get("country")
                    and normalized_data.get("lat")
                    and normalized_data.get("lon")
                ):
                    normalized_logins.append(normalized_data)

        return normalized_logins
