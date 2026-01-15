import json
import os

from django.conf import settings
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.discord_alerting import DiscordAlerting
from impossible_travel.alerting.dummy_alerting import DummyAlerting
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.alerting.googlechat_alerting import GoogleChatAlerting
from impossible_travel.alerting.http_request import HTTPRequestAlerting
from impossible_travel.alerting.mattermost_alerting import MattermostAlerting
from impossible_travel.alerting.microsoft_teams_alerting import MicrosoftTeamsAlerting
from impossible_travel.alerting.pushover_alerting import PushoverAlerting
from impossible_travel.alerting.rocketchat_alerting import RocketChatAlerting
from impossible_travel.alerting.slack_alerting import SlackAlerting
from impossible_travel.alerting.telegram_alerting import TelegramAlerting
from impossible_travel.alerting.webhook import WebHookAlerting


class AlertFactory:
    def __init__(self) -> None:
        config = self._read_config()
        alerters = config.get("active_alerters")
        self.active_alerters = []
        self.alert_configs = []
        for alerter in alerters:
            self.active_alerters.append(BaseAlerting.SupportedAlerters(alerter))
            self.alert_configs.append(config[alerter])

    def _read_config(self) -> dict:
        """
        Read the configuration file.
        """
        with open(
            os.path.join(
                settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/alerting.json"
            ),
            mode="r",
            encoding="utf-8",
        ) as f:
            config = json.load(f)
        if "active_alerters" not in config:
            raise ValueError("active_alerters not found in alerting.json")
        for active_alerter in config["active_alerters"]:
            if active_alerter not in [e.value for e in BaseAlerting.SupportedAlerters]:
                raise ValueError(f"active_alerter {active_alerter} not supported")
            if config[active_alerter] is None:
                raise ValueError(f"Configuration for {active_alerter} not found")
        return config

    def get_alert_classes(self) -> BaseAlerting:
        """Creates and return an alerter using the abstract factory"""

        alerter_map = {
            BaseAlerting.SupportedAlerters.DUMMY: DummyAlerting,
            BaseAlerting.SupportedAlerters.SLACK: SlackAlerting,
            BaseAlerting.SupportedAlerters.WEBHOOK: WebHookAlerting,
            BaseAlerting.SupportedAlerters.HTTPREQUEST: HTTPRequestAlerting,
            BaseAlerting.SupportedAlerters.TELEGRAM: TelegramAlerting,
            BaseAlerting.SupportedAlerters.EMAIL: EmailAlerting,
            BaseAlerting.SupportedAlerters.PUSHOVER: PushoverAlerting,
            BaseAlerting.SupportedAlerters.DISCORD: DiscordAlerting,
            BaseAlerting.SupportedAlerters.MICROSOFTTEAMS: MicrosoftTeamsAlerting,
            BaseAlerting.SupportedAlerters.ROCKETCHAT: RocketChatAlerting,
            BaseAlerting.SupportedAlerters.GOOGLECHAT: GoogleChatAlerting,
            BaseAlerting.SupportedAlerters.MATTERMOST: MattermostAlerting,
        }

        return [
            alerter_map[alerter](config)
            for alerter, config in zip(self.active_alerters, self.alert_configs)
        ]
