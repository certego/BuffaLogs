import json
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum


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
