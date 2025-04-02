import json
import os

from django.conf import settings
from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.ingestion.opensearch_ingestion import OpensearchIngestion
from impossible_travel.ingestion.splunk_ingestion import SplunkIngestion


class IngestionFactory:
    def __init__(self):
        config = self._read_config()
        self.active_ingestion = BaseIngestion.SupportedIngestionSources(config["active_ingestion"])
        self.ingestion_config = config[config["active_ingestion"]]

    def _read_config(self) -> dict:
        """
        Read the ingestion configuration file

        :return : the configuration dict
        :rtype: dict
        """
        with open(
            os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
            mode="r",
            encoding="utf-8",
        ) as f:
            config = json.load(f)
        if config["active_ingestion"] not in [i.value for i in BaseIngestion.SupportedIngestionSources]:
            raise ValueError(f"The ingestion source: {config['active_ingestion']} is not supported")
        if not config.get(config["active_ingestion"]):
            raise ValueError(f"The configuration for the {config['active_ingestion']} must be implemented")
        return config

    def get_ingestion_class(self):
        """
        Return the ingestion class
        """
        match self.active_ingestion:
            case BaseIngestion.SupportedIngestionSources.ELASTICSEARCH:
                return ElasticsearchIngestion(self.ingestion_config)
            case BaseIngestion.SupportedIngestionSources.OPENSEARCH:
                return OpensearchIngestion(self.ingestion_config)
            case BaseIngestion.SupportedIngestionSources.SPLUNK:
                return SplunkIngestion(self.ingestion_config)
            case _:
                raise ValueError(f"Unsupported ingestionsource: {self.active_ingestion}")
