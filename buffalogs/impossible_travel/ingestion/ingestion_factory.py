import json
import os

from django.conf import settings
from impossible_travel.ingestion.base_ingestion import (
    BaseIngestion,
)
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
    def __init__(self):
        config = self._read_config()

        self.active_ingestion = (
            BaseIngestion.SupportedIngestionSources(
                config["active_ingestion"]
            )
        )

        self.ingestion_config = config[config["active_ingestion"]]

        # Default mapping → Elasticsearch mapping
        self.mapping = self.ingestion_config.get(
            "custom_mapping",
            config["elasticsearch"]["custom_mapping"],
        )

    def _read_config(self) -> dict:
        """
        Read the ingestion configuration file.

        :return: configuration dictionary
        """
        path = os.path.join(
            settings.CERTEGO_BUFFALOGS_CONFIG_PATH,
            "buffalogs/ingestion.json",
        )

        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        valid_sources = [
            source.value
            for source in BaseIngestion.SupportedIngestionSources
        ]

        if config["active_ingestion"] not in valid_sources:
            raise ValueError(
                f"Ingestion source '{config['active_ingestion']}' "
                f"is not supported."
            )

        if not config.get(config["active_ingestion"]):
            raise ValueError(
                f"Configuration missing for "
                f"'{config['active_ingestion']}'."
            )

        return config

    def get_ingestion_class(self):
        """
        Return the ingestion class based on config.
        """
        src = self.active_ingestion

        if src == BaseIngestion.SupportedIngestionSources.ELASTICSEARCH:
            return ElasticsearchIngestion(
                self.ingestion_config,
                self.mapping,
            )

        if src == BaseIngestion.SupportedIngestionSources.OPENSEARCH:
            return OpensearchIngestion(
                self.ingestion_config,
                self.mapping,
            )

        if src == BaseIngestion.SupportedIngestionSources.SPLUNK:
            return SplunkIngestion(
                self.ingestion_config,
                self.mapping,
            )

        raise ValueError(
            f"Unsupported ingestion source: {self.active_ingestion}"
        )
