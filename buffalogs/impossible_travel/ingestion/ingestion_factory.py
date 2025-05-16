import json
import os

from django.conf import settings
from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.ingestion.opensearch_ingestion import OpensearchIngestion
from impossible_travel.ingestion.splunk_ingestion import SplunkIngestion


class IngestionFactory:
    """Factory to build the right ingestion class from config."""

    def __init__(self):
        config = self._read_config()
        # enum whose .value matches the JSON key
        self.active_ingestion = BaseIngestion.SupportedIngestionSources(config["active_ingestion"])
        src_conf = config[self.active_ingestion.value]

        # resolve mapping: if placeholder, use common; else use specific dict
        raw_map = src_conf.get("custom_mapping")
        common = config.get("common_custom_mapping", {})
        # compute the actual mapping dict for our own use
        if isinstance(raw_map, str) and raw_map == "${common_custom_mapping}":
            self.mapping = common
        else:
            self.mapping = raw_map or common

        self.ingestion_config = src_conf

    def _read_config(self) -> dict:
        """Load and validate ingestion.json."""
        path = os.path.join(
            settings.CERTEGO_BUFFALOGS_CONFIG_PATH,
            "buffalogs",
            "ingestion.json",
        )
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        allowed = [s.value for s in BaseIngestion.SupportedIngestionSources]
        active = config.get("active_ingestion")
        if active not in allowed:
            raise ValueError(f"Ingestion source '{active}' is not supported")
        if not config.get(active):
            raise ValueError(f"Configuration for '{active}' must be implemented")

        return config

    def get_ingestion_class(self):
        """Return the instantiated ingestion class for the active backend."""
        cfg = self.ingestion_config
        mapping = self.mapping

        match self.active_ingestion:
            case BaseIngestion.SupportedIngestionSources.ELASTICSEARCH:
                return ElasticsearchIngestion(cfg, mapping)
            case BaseIngestion.SupportedIngestionSources.OPENSEARCH:
                return OpensearchIngestion(cfg, mapping)
            case BaseIngestion.SupportedIngestionSources.SPLUNK:
                return SplunkIngestion(cfg, mapping)
            case _:
                raise ValueError(f"Unsupported ingestion source: {self.active_ingestion}")
