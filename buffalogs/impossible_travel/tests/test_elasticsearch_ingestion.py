import json
import os
from datetime import datetime
from typing import List
from unittest.mock import patch

import elasticsearch
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
from impossible_travel.models import User
from impossible_travel.modules.ingestion_handler import ElasticsearchIngestion

ELASTICSEARCH_TEST_URL = "http://localhost:9200"


def load_ingestion_config(name):
    with open(os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_INGESTION_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


def load_test_data(name):
    DATA_PATH = "impossible_travel/tests/test_data"
    with open(os.path.join(DATA_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


def load_elastic_template(name):
    DATA_PATH = f"{settings.CERTEGO_BUFFALOGS_CONFIG_PATH}elasticsearch/"
    with open(os.path.join(DATA_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


class TestElasticsearchIngestion(TestCase):
    def setUp(self):
        self.ingestion_config = load_ingestion_config("ingestion")
        self.list_to_be_added_cloud = load_test_data("elasticsearch_test_data_cloud")
        self.list_to_be_added_fw_proxy = load_test_data("elasticsearch_test_data_fw_proxy")
        self.es = elasticsearch.Elasticsearch(ELASTICSEARCH_TEST_URL)
        self.template = load_elastic_template("example_template")
        connections.create_connection(hosts=ELASTICSEARCH_TEST_URL, timeout=self.ingestion_config["elasticsearch"]["timeout"])
        self._load_elastic_template_on_elastic(template_to_be_added=self.template)
        # load test data into the 2 indexes: cloud-* and fw-proxy-*
        self._load_test_data_on_elastic(data_to_be_added=self.list_to_be_added_cloud, index="cloud-")
        self._load_test_data_on_elastic(data_to_be_added=self.list_to_be_added_fw_proxy, index="fw-proxy-")

    def _load_elastic_template_on_elastic(self, template_to_be_added):
        response = self.es.indices.put_template("example_template", template_to_be_added)
        # check that the template has been uploaded correctly
        self.assertTrue(response["acknowledged"])

    def tearDown(self) -> None:
        self.es.indices.delete(index="cloud-", ignore=[404])
        self.es.indices.delete(index="fw-proxy-", ignore=[404])

    def _bulk_gendata(self, index: str, data_list: list):
        for single_data in data_list:
            yield {"_op_type": "index", "_index": index, "_source": single_data}

    def _load_test_data_on_elastic(self, data_to_be_added: List[dict], index: str):
        bulk(self.es, self._bulk_gendata(index, data_to_be_added), refresh="true")
        # check that the data on the Elastic index has been uploaded correctly
        count = self.es.count(index=index)["count"]
        self.assertTrue(count > 0)

    def test__exec_process_logs_no_data(self):
        # test the function _exec_process_logs with no data in that range time
        # set the correct url for the tests
        self.ingestion_config["elasticsearch"]["url"] = "http://localhost:9200"
        now = timezone.now()
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion()
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor._exec_process_logs(start_date, end_date, self.ingestion_config)
        self.assertEqual(0, len(returned_users))

    def test__exec_process_logs_data(self):
        # test the function _exec_process_logs with data
        # set the correct url for the tests
        self.ingestion_config["elasticsearch"]["url"] = "http://localhost:9200"
        now = timezone.now()
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion()
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor._exec_process_logs(start_date, end_date, self.ingestion_config)
        self.assertEqual(4, len(returned_users))
        self.assertTrue(User.objects.filter(username="Stitch").exists())
