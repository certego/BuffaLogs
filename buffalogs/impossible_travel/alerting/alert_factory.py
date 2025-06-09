import json
import os

from django.conf import settings
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.discord_alerting import DiscordAlerting
from impossible_travel.alerting.dummy_alerting import DummyAlerting
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.alerting.googlechat_alerting import GoogleChatAlerting
from impossible_travel.alerting.http_request import HTTPRequestAlerting
from impossible_travel.alerting.microsoft_teams_alerter import MicrosoftTeamsAlerting
from impossible_travel.alerting.pushover_alerting import PushoverAlerting
from impossible_travel.alerting.rocketchat_alerting import RocketChatAlerting
from impossible_travel.alerting.slack_alerter import SlackAlerter
from impossible_travel.alerting.telegram_alerting import TelegramAlerting
from impossible_travel.alerting.webhook import WebHookAlerting


class AlertFactory:
    def __init__(self) -> None:
        config = self._read_config()
        self.active_alerter = BaseAlerting.SupportedAlerters(config["active_alerter"])
        self.alert_config = config[config["active_alerter"]]

    def _read_config(self) -> dict:
        """
        Read the configuration file.
        """
        with open(
            os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/alerting.json"),
            mode="r",
            encoding="utf-8",
        ) as f:
            config = json.load(f)
        if "active_alerter" not in config:
            raise ValueError("active_alerter not found in alerting.json")
        if config["active_alerter"] not in [e.value for e in BaseAlerting.SupportedAlerters]:
            raise ValueError(f"active_alerter {config['active_alerter']} not supported")
        if config[config["active_alerter"]] is None:
            raise ValueError(f"Configuration for {config['active_alerter']} not found")
        return config

    def get_alert_class(self) -> BaseAlerting:
        """Creates and return an alerter using the abstract factory"""

        match self.active_alerter:
            case BaseAlerting.SupportedAlerters.DUMMY:
                return DummyAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.SLACK:
                return SlackAlerter(self.alert_config)
            case BaseAlerting.SupportedAlerters.WEBHOOK:
                return WebHookAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.HTTPREQUEST:
                return HTTPRequestAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.TELEGRAM:
                return TelegramAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.EMAIL:
                return EmailAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.PUSHOVER:
                return PushoverAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.DISCORD:
                return DiscordAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.MICROSOFTTEAMS:
                return MicrosoftTeamsAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.ROCKETCHAT:
                return RocketChatAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.GOOGLECHAT:
                return GoogleChatAlerting(self.alert_config)
            case _:
                raise ValueError(f"Unsupported alerter: {self.active_alerter}")
