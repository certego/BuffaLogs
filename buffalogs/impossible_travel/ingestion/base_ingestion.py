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
        """

        ELASTICSEARCH = "elasticsearch"

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

    @abstractmethod
    def normalize_fields(self, logins_response) -> list:
        """Abstract method that implement the normalization of the fields returned by the ingestion source in order to be mapped into the field names used by BuffaLogs
        This method will be different implemented based on the ingestion source used.

        :param logins_response: user related logins
        :type logins_response: any, depending on the ingestion source

        :return: list of normalized logins
        :rtype: list
        """
        raise NotImplementedError
