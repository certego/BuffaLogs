import json
import os

from django.conf import settings
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.dummy_alerting import DummyAlerting
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.alerting.telegram_alerting import TelegramAlerting


class AlertFactory:

    def __init__(self) -> None:
        """pet_factory is our abstract factory.  We can set it at will."""

        config = self._read_config()

        self.active_alerter = BaseAlerting.SupportedAlerters(config["active_alerter"])
        self.alert_config = config[config["active_alerter"]]

    def _read_config(self) -> dict:
        """
        Read the configuration file.
        """
        with open(os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/alerting.json"), mode="r", encoding="utf-8") as f:
            config = json.load(f)

        # Validate configuration
        if "active_alerter" not in config:
            raise ValueError("active_alerter not found in alerting.json")
        if config["active_alerter"] not in BaseAlerting.SupportedAlerters:
            raise ValueError(f"active_alerter {config['active_alerter']} not supported")
        if config[config["active_alerter"]] is None:
            raise ValueError(f"Configuration for {config['active_alerter']} not found")
        return config

    def get_alert_class(self) -> BaseAlerting:
        """Creates and return an alerter using the abstract factory"""

        alerter_class = None
        match self.active_alerter:
            case BaseAlerting.SupportedAlerters.DUMMY:
                alerter_class = DummyAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.TELEGRAM:
                alerter_class = TelegramAlerting(self.alert_config)
            case BaseAlerting.SupportedAlerters.EMAIL:
                alerter_class = EmailAlerting(self.alert_config)
            case _:
                raise ValueError(f"Unsupported alerter: {self.active_alerter}")
        return alerter_class
