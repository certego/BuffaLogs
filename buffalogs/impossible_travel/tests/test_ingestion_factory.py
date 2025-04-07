import json
import os

from django.conf import settings
from django.test import TestCase
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
from impossible_travel.ingestion.opensearch_ingestion import OpensearchIngestion


def load_test_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/tests/test_data/", name + ".json")) as file:
        data = json.load(file)
    return data


def load_ingestion_config_data():
    with open(
        os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
        mode="r",
        encoding="utf-8",
    ) as f:
        config_ingestion = json.load(f)
    return config_ingestion


class IngestionFactoryTestCase(TestCase):
    def setUp(self):
        # executed once per test (at the beginning)
        self.ingestion_config = load_ingestion_config_data()

    def test_initialization(self):
        # test correct class initialization
        factory = IngestionFactory()
        self.assertIsNotNone(factory.active_ingestion.value)
        self.assertIsNot({}, factory.ingestion_config)
        self.assertIsInstance(factory.ingestion_config, dict)
        self.assertEqual(self.ingestion_config["active_ingestion"], factory.active_ingestion.value)

    def test_read_config_valid(self):
        # test correct config loading
        factory = IngestionFactory()
        config = factory._read_config()
        self.assertIsInstance(config, dict)
        self.assertTrue("active_ingestion" in config)

    def test_get_ingestion_class_valid_default_Elasticsearch(self):
        # test default Elasticsearch ingestion source
        excpected_config = load_ingestion_config_data()
        factory = IngestionFactory()
        ingestion_class = factory.get_ingestion_class()
        self.assertIsInstance(ingestion_class, ElasticsearchIngestion)
        self.assertEqual(excpected_config["elasticsearch"], factory.ingestion_config)

    def test_normalize_fields_valid(self):
        # test _normalize_fields with an existing key value
        data = {"source": {"geo": {"location": {"lat": 51.0951, "lon": 10.2714}}}, "username": "bugs-bunny@organization.com"}
        key = "source.geo.location.lat"
        factory = IngestionFactory()
        result = factory._normalize_fields(data, key)
        self.assertEqual(51.0951, result)

    def test_normalize_fields_key_not_found(self):
        # test _normalize_fields with an unexisting key
        data = {"source": {"geo": {"location": {"lat": 51.0951}}}}
        key = "source.geo.location.lon"
        factory = IngestionFactory()
        result = factory._normalize_fields(data, key)
        self.assertEqual("", result)

    def test_normalize_fields_empty_dict(self):
        # test _normalize_fields with an empty login dict
        data = {}
        key = "username"
        factory = IngestionFactory()
        result = factory._normalize_fields(data, key)
        self.assertEqual("", result)
