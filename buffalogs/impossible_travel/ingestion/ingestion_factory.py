import json
import os

from django.conf import settings
from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.ingestion.opensearch_ingestion import OpensearchIngestion


class IngestionFactory:
    def __init__(self):
        config = self._read_config()
        self.active_ingestion = BaseIngestion.SupportedIngestionSources(config["active_ingestion"])
        self.ingestion_config = config[config["active_ingestion"]]
        # default mapping: Elasticsearch mapping
        self.mapping = self.ingestion_config.get("custom_mapping", config["elasticsearch"]["custom_mapping"])

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
            case _:
                raise ValueError(f"Unsupported ingestionsource: {self.active_ingestion}")

    def _normalize_fields(self, data: dict, key: str) -> dict:
        """Concrete method that manage the mapping into the required BuffaLogs mapping.
        The mapping used is defined into the ingestion.json file "custom_mapping" if defined, otherwise it is used the default one

        :param data: the login to be normalized into the mapping fields
        :type data: dict
        :param key: field name
        :type key: str

        :return: the final normalized dict with the login
        :rtype: dict

        """
        keys = key.split(".")  # divide the key in levels if nested
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]  # into the nested level
            else:
                return ""  # empty str if the path doesn't exist
        return data
