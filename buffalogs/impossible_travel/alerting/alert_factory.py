from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.dummy_alerting import DummyAlerting
import os
import json
from django.conf import settings

class AlertFactory:
    def __init__(self) -> None:
        config = self._read_config()
        self.active_alerter = BaseAlerting.SupportedAlerters(config["active_alerter"])
        self.alert_config = config[config["active_alerter"]]

    def _read_config(self) -> dict:
        with open(os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/alerting.json"), mode="r") as f:
            config = json.load(f)
        if "active_alerter" not in config:
            raise ValueError("active_alerter not found in alerting.json")
        if config["active_alerter"] not in [e.value for e in BaseAlerting.SupportedAlerters]:
            raise ValueError(f"active_alerter {config['active_alerter']} not supported")
        if config[config["active_alerter"]] is None:
            raise ValueError(f"Configuration for {config['active_alerter']} not found")
        return config

    def get_alert_class(self) -> BaseAlerting:
        if self.active_alerter == BaseAlerting.SupportedAlerters.DUMMY:
            return DummyAlerting(self.alert_config)
        elif self.active_alerter == BaseAlerting.SupportedAlerters.SLACK:
            from impossible_travel.alerting.slack_alerter import SlackAlerter
            return SlackAlerter(self.alert_config)
        else:
            raise ValueError(f"Unsupported alerter: {self.active_alerter}")