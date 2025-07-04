import unittest

from buffacli.models import Ingestion


class TestIngestionModel(unittest.TestCase):

    def setUp(self):
        self.active_ingestion_response = {
            "source": "elasticsearch",
            "fields": {"url": "http://elasticsearch:9200/", "username": "foobar", "password": "bar", "timeout": 90, "indexes": "cloud-*, fw-proxy-*"},
        }

        self.ingestion_source_response = {
            "source": "elasticsearch",
            "fields": {"url": "http://elasticsearch:9200/", "username": "foobar", "password": "bar", "timeout": 90, "indexes": "cloud-*, fw-proxy-*"},
        }
        self.ingestion_sources_response = [
            {"source": "elasticsearch", "fields": ["url", "username", "password", "timeout", "indexes"]},
            {"source": "opensearch", "fields": ["url", "username", "password", "timeout", "indexes"]},
            {"source": "splunk", "fields": ["host", "port", "scheme", "username", "password", "timeout", "indexes"]},
        ]

    def test_table_format(self):
        active_ingestion = Ingestion(self.active_ingestion_response)
        ingestion_source = Ingestion(self.ingestion_source_response)
        ingestion_sources = Ingestion(self.ingestion_sources_response)
        expected_source_format = {
            "fields": ["url", "username", "password", "timeout", "indexes"],
            "": ["http://elasticsearch:9200/", "foobar", "bar", 90, "cloud-*, fw-proxy-*"],
        }

        self.assertEqual(active_ingestion.table, expected_source_format)
        self.assertEqual(ingestion_source.table, expected_source_format)

        expected_sources_format = {
            "sources": ["elasticsearch", "opensearch", "splunk"],
            "fields": [
                ["url", "username", "password", "timeout", "indexes"],
                ["url", "username", "password", "timeout", "indexes"],
                ["host", "port", "scheme", "username", "password", "timeout", "indexes"],
            ],
        }

        self.assertEqual(expected_sources_format, ingestion_sources.table)
