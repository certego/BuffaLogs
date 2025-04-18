import json
import os

from django.conf import settings

from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.ingestion.elasticsearch_ingestion import (
    ElasticsearchIngestion,
)
from impossible_travel.ingestion.opensearch_ingestion import (
    OpensearchIngestion,
)
from impossible_travel.ingestion.splunk_ingestion import (
    SplunkIngestion,
)


class IngestionFactory:
    """Factory to build the right ingestion class from config."""

    def __init__(self):
        config = self._read_config()
        active = config["active_ingestion"]
        self.active_ingestion = BaseIngestion.SupportedIngestionSources(active)
        self.ingestion_config = config[active]

        # pull in common mapping if referenced, otherwise use any override
        common_map = config.get(
            "common_custom_mapping",
            config["elasticsearch"]["custom_mapping"],
        )
        self.mapping = self.ingestion_config.get("custom_mapping", common_map)

    def _read_config(self) -> dict:
        """Load and validate ingestion.json, replace common mapping refs."""
        config_path = os.path.join(
            settings.CERTEGO_BUFFALOGS_CONFIG_PATH,
            "buffalogs",
            "ingestion.json",
        )
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Inline common mapping where requested
        common_map = config.get(
            "common_custom_mapping",
            config["elasticsearch"]["custom_mapping"],
        )
        for backend in ("elasticsearch", "opensearch", "splunk"):
            cm = config.get(backend, {}).get("custom_mapping")
            if cm == "${common_custom_mapping}":
                config[backend]["custom_mapping"] = common_map

        supported = [i.value for i in BaseIngestion.SupportedIngestionSources]
        src = config["active_ingestion"]
        if src not in supported:
            raise ValueError(f"Ingestion source '{src}' is not supported")

        if not config.get(src):
            raise ValueError(f"Configuration for '{src}' must be implemented")

        return config

    def get_ingestion_class(self):
        """Return the instantiated ingestion class for the active backend."""
        match self.active_ingestion:
            case BaseIngestion.SupportedIngestionSources.ELASTICSEARCH:
                return ElasticsearchIngestion(
                    self.ingestion_config,
                    self.mapping,
                )
            case BaseIngestion.SupportedIngestionSources.OPENSEARCH:
                return OpensearchIngestion(
                    self.ingestion_config,
                )
            case BaseIngestion.SupportedIngestionSources.SPLUNK:
                return SplunkIngestion(
                    self.ingestion_config,
                    self.mapping,
                )
            case _:
                raise ValueError(
                    f"Unsupported ingestion source: "
                    f"{self.active_ingestion}"
                )
