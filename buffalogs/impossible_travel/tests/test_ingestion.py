import json
import os

from django.conf import settings
from django.test import TestCase
from impossible_travel.modules.ingestion_handler import ElasticsearchIngestion, Ingestion


def load_ingestion_config_data():
    file_path = settings.CERTEGO_BUFFALOGS_CONFIG_INGESTION_PATH
    with open(os.path.join(file_path, "ingestion.json"), encoding="utf-8") as f:
        config_ingestion = json.load(f)
    return config_ingestion


class IngestionTestCase(TestCase):
    config_ingestion = load_ingestion_config_data()

    def test_str_to_class(self):
        # Test the str_to_class static method
        active_ingestion_sources = self.config_ingestion["active_ingestion_sources"]
        for active_source in active_ingestion_sources:
            # each class_name of the active source has to be implemented and the abstrach methods too
            assert Ingestion.str_to_class(self.config_ingestion[active_source]["class_name"])

    def test_ingestion_config_file_classes(self):
        # Test the presence of necessary fields in the config file
        active_ingestion_sources = self.config_ingestion["active_ingestion_sources"]
        self.assertEqual(list, type(active_ingestion_sources))
        # check the presence of necessary fields in the ingestion configs for each source
        for source in active_ingestion_sources:
            self.assertIsNotNone(self.config_ingestion[source])
            self.assertTrue(source in self.config_ingestion.keys())
            self.assertTrue("class_name" in self.config_ingestion[source])
            self.assertTrue("url" in self.config_ingestion[source])
            self.assertTrue("username" in self.config_ingestion[source])
            self.assertTrue("password" in self.config_ingestion[source])
            self.assertTrue("custom_mapping" in self.config_ingestion[source])

    def test_get_ingestion_sources_generic(self):
        ingestion_source_received = Ingestion.get_ingestion_sources()
        self.assertEqual(len(self.config_ingestion["active_ingestion_sources"]), len(ingestion_source_received))

    def test_get_ingestion_sources__elasticsearch(self):
        # Tests for the ingestion source: Elasticsearch
        active_ingestion_sources = self.config_ingestion["active_ingestion_sources"]
        # "elasticsearch" is always active and its config must exist
        self.assertTrue("elasticsearch" in active_ingestion_sources)
        self.assertTrue("elasticsearch" in self.config_ingestion.keys())
        self.assertIn("ElasticsearchIngestion", self.config_ingestion["elasticsearch"].values())
        self.assertIsInstance(Ingestion.str_to_class("ElasticsearchIngestion"), ElasticsearchIngestion.__class__)
