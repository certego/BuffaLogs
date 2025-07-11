import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from elasticsearch import Elasticsearch
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.models import User


def read_config():
    with open(os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"), mode="r", encoding="utf-8") as f:
        config = json.load(f)
        config = config["elasticsearch"]
        config["url"] = "http://localhost:9200/"
    return config


class TestViewsElasticIngestion(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="test_user", id=1)

    def setUp(self):
        self.maxDiff = None
        self.client = Client()
        self.config = read_config()
        self.create_test_data()

    @patch("impossible_travel.ingestion.ingestion_factory.IngestionFactory.get_ingestion_class")
    @patch("django.utils.timezone.now")
    def test_get_all_logins(self, mock_now, mock_get_ingestion_class):
        mock_now.return_value = datetime(1970, 1, 1, 0, 0) + timedelta(days=10)
        mock_get_ingestion_class.return_value = ElasticsearchIngestion(ingestion_config=self.config, mapping=self.config["custom_mapping"])
        url = reverse("get_all_logins", kwargs={"pk_user": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.json())
        self.assertEqual(content, self.expected_logins)

    def generate_test_data(self):
        data = []

        test_data = {
            "@timestamp": "1970-01-01T00:00:00Z",
            "user": {"name": "test_user"},
            "source": {
                "geo": {"country_name": "Test Country", "location": {"lat": 12.34, "lon": 56.78}},
                "as": {"organization": {"name": "Test ISP"}},
                "ip": "192.168.1.1",
                "intelligence_category": "Test Category",
            },
            "user_agent": {"original": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0"},
            "event": {"type": "start", "category": "authentication", "outcome": "success"},
        }

        indicies = ["cloud", "fw-proxy"]
        for i, index in enumerate(indicies):
            index = f"{index}-test_data-1970-01-01"
            _id = f"test_id_{i + 1}"
            data.append((index, _id, test_data))
        return data

    def create_test_data(self):
        test_data = self.generate_test_data()
        es = Elasticsearch([self.config["url"]])
        expected_logins = []
        for item in test_data:
            index, _id, msg = item
            es.index(index=index, id=_id, body=msg, refresh="true")
            expected_logins.append(self.generate_expected_data(_id, index))
        self.expected_logins = expected_logins

    def generate_expected_data(self, _id, index):
        return {
            "timestamp": "1970-01-01T00:00:00Z",
            "id": _id,
            "index": "cloud" if index.startswith("cloud") else "fw-proxy",
            "username": self.user.username,
            "ip": "192.168.1.1",
            "agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0",
            "organization": "Test ISP",
            "country": "Test Country",
            "lat": 12.34,
            "lon": 56.78,
        }

    def tearDown(self):
        es = Elasticsearch([self.config["url"]])
        for i, index in enumerate(["cloud", "fw-proxy"]):
            index = f"{index}-test_data-1970-01-01"
            _id = f"test_id_{i + 1}"
            es.delete(index=index, id=_id)
