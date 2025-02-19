from abc import ABC, abstractmethod
from enum import Enum
import os
import json
from django.conf import settings

class BaseAlerting(ABC):
    """
    Abstract base class for query operations.
    """
    
    class SupportedAlerters(Enum):
        DUMMY = "dummy"

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        config = self._read_config()

        self.active_alerter = config["active_alerter"]
        self.alert_config = config[self.active_alerter]

    def _read_config(self) -> dict:
        """
        Read the configuration file.
        """
        with open(os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "alerting.json")) as f:
            config = json.load(f)

        # Validate configuration
        if "active_alerter" not in config:
            raise ValueError("active_alerter not found in alerting.json")
        if config["active_alerter"] not in self.SupportedAlerters:
            raise ValueError(f"active_alerter {config['active_alerter']} not supported")
        if config[config["active_alerter"]] is None:
            raise ValueError(f"Configuration for {config['active_alerter']} not found")
        return config
    
    @abstractmethod
    def notify_alerts(self):
        """
        Execute the query operation.
        Must be implemented by concrete classes.
        """
        pass