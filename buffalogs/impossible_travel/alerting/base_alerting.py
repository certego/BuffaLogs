import json
import logging
import os
import time
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

    @staticmethod
    def alert_message_formatter(alert):
        """
        Format the alert message for notification.
        """
        alert_title = f"BuffaLogs - Login Anomaly Alert: {alert.name} for user {alert.user.username}"
        alert_description = (
            f"Dear admin,\nAn unusual login activity has been detected:\n\n"
            f"User: {alert.user.username}\n"
            f"Alert type: {alert.name}\n"
            f"Alert description: {alert.description}\n\n"
            f"The raw data relating to the login that triggered the alert is:\n{alert.login_raw_data}\n\n"
            "Stay Safe,\nBuffalogs"
        )
        return alert_title, alert_description

    @staticmethod
    def send_with_exponential_backoff(send_func, max_retries=3, base_delay=1, *args, **kwargs):
        """
        Tries to send an alert using send_func, retries with exponential backoff if not successful.
        """
        logger = logging.getLogger(send_func.__module__)
        for attempt in range(max_retries):
            success = send_func(*args, **kwargs)
            if success:
                return True
            wait_time = base_delay * (2**attempt)
            logger.warning(f"Send attempt {attempt + 1} failed, retrying in {wait_time}s...")
            time.sleep(wait_time)
        logger.error(f"Failed to send alert after {max_retries} attempts.")
        return False
