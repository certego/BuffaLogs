import json
from unittest import mock

from django.urls import reverse
from rest_framework.test import APITestCase


def mock_write_ingestion_config(source_name, ingestion_config):
    # do nothing
    pass


class TestIngestionAPIViews(APITestCase):
    def test_get_ingestion_sources(self):
        expected = [
            {
                "source": "elasticsearch",
                "fields": ["url", "username", "password", "timeout", "indexes"],
            },
            {
                "source": "opensearch",
                "fields": ["url", "username", "password", "timeout", "indexes"],
            },
            {
                "source": "splunk",
                "fields": [
                    "host",
                    "port",
                    "scheme",
                    "username",
                    "password",
                    "timeout",
                    "indexes",
                ],
            },
        ]
        response = self.client.get(reverse("ingestion_sources_api"))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(expected, json.loads(response.content))

    def test_get_active_ingestion_source(self):
        expected = {
            "source": "elasticsearch",
            "fields": {
                "url": "http://elasticsearch:9200/",
                "username": "foobar",
                "password": "bar",
                "timeout": 90,
                "indexes": "cloud-*,fw-proxy-*",
            },
        }
        response = self.client.get(reverse("active_ingestion_source_api"))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected, json.loads(response.content))

    def test_get_unsupported_ingestion_source_config(self):
        response = self.client.get(reverse("ingestion_source_config_api", kwargs={"source": "UNKOWN"}))
        expected_error = {"message": "Unsupported ingestion source - UNKOWN"}
        self.assertEqual(response.status_code, 400)
        self.assertEqual(expected_error, json.loads(response.content))

    def test_get_supported_ingestion_source_config(self):
        expected = {
            "source": "elasticsearch",
            "fields": {
                "url": "http://elasticsearch:9200/",
                "username": "foobar",
                "password": "bar",
                "timeout": 90,
                "indexes": "cloud-*,fw-proxy-*",
            },
        }
        response = self.client.get(reverse("ingestion_source_config_api", kwargs={"source": "elasticsearch"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, json.loads(response.content))

    @mock.patch(
        "impossible_travel.views.ingestion.write_config",
        side_effect=mock_write_ingestion_config,
    )
    def test_update_ingestion_source_config(self, mock_writer):
        response = self.client.post(
            reverse("ingestion_source_config_api", kwargs={"source": "elasticsearch"}),
            {"url": "http://new_url", "username": "user2"},
            format="json",
        )
        expected = {"message": "Update successful"}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, json.loads(response.content))
