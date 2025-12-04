import json
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum

from django.conf import settings


class BaseAlerting(ABC):
    """
    Abstract base class for query operations.
    """

    class SupportedAlerters(Enum):
        DUMMY = "dummy"
        SLACK = "slack"
        WEBHOOK = "webhooks"
        HTTPREQUEST = "http_request"
        TELEGRAM = "telegram"
        EMAIL = "email"
        PUSHOVER = "pushover"
        DISCORD = "discord"
        MICROSOFTTEAMS = "microsoftteams"
        ROCKETCHAT = "rocketchat"
        GOOGLECHAT = "googlechat"
        MATTERMOST = "mattermost"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def notify_alerts(self):
        """
        Execute the query operation.
        Must be implemented by concrete classes.
        """
        raise NotImplementedError

    @staticmethod
    def read_config(alerter_key: str):
        """
        Read the configuration for a specific alerter from alerting.json.
        """
        config_path = os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/alerting.json")
        with open(config_path, mode="r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get(alerter_key, {})
