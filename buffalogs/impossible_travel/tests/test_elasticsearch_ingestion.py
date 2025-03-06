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


def load_ingestion_config_data():
    file_path = settings.CERTEGO_BUFFALOGS_CONFIG_INGESTION_PATH
    with open(os.path.join(file_path, "ingestion.json"), encoding="utf-8") as f:
        config_ingestion = json.load(f)
    return config_ingestion


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
        self.elastic_test_url = "http://localhost:9200"
        self.ingestion_config = load_ingestion_config_data()
        self.list_to_be_added_cloud = load_test_data("elasticsearch_test_data_cloud")
        self.list_to_be_added_fw_proxy = load_test_data("elasticsearch_test_data_fw_proxy")
        self.es = elasticsearch.Elasticsearch(self.elastic_test_url)
        self.template = load_elastic_template("example_template")
        connections.create_connection(hosts=self.elastic_test_url, timeout=self.ingestion_config["elasticsearch"]["timeout"])
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

    def test_process_users_no_data(self):
        # test the function process_users with no data in that range time
        # set the correct url for the tests
        self.ingestion_config["elasticsearch"]["url"] = self.elastic_test_url
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion()
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor.process_users(start_date, end_date, elastic_ingestion_config=self.ingestion_config["elasticsearch"])
        self.assertEqual(0, len(returned_users))

    def test_process_users_data(self):
        # test the function process_users with data
        # set the correct url for the tests
        self.ingestion_config["elasticsearch"]["url"] = self.elastic_test_url
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion()
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor.process_users(start_date, end_date, elastic_ingestion_config=self.ingestion_config["elasticsearch"])
        self.assertEqual(4, len(returned_users))
        self.assertTrue(User.objects.filter(username="Stitch").exists())

    def test_process_user__elasticsearch(self):
        pass
        # testing the process_user function for the Elasticsearch ingestion source
        # @patch("impossible_travel.tasks.check_fields")
        # @patch.object(tasks.Search, "execute")
        # def test_process_user(self, mock_execute, mock_check_fields):
        #     data_elastic_sorted_dot_not = []
        #     imp_travel = impossible_travel.Impossible_Travel()
        #     data_elastic = load_test_data("test_data_process_user")
        #     data_elastic_sorted = sorted(data_elastic, key=lambda d: d["@timestamp"])
        #     for data in data_elastic_sorted:
        #         data_elastic_sorted_dot_not.append(DictStruct(kwargs=data))
        #     data_results = load_test_data("test_data_process_user_result")
        #     mock_execute.return_value = data_elastic_sorted_dot_not
        #     start_date = timezone.datetime(2023, 3, 8, 0, 0, 0)
        #     end_date = timezone.datetime(2023, 3, 8, 23, 59, 59)
        #     iso_start_date = imp_travel.validate_timestamp(start_date)
        #     iso_end_date = imp_travel.validate_timestamp(end_date)
        #     db_user = User.objects.get(username="Lorena Goldoni")
        #     tasks.process_user(db_user, iso_start_date, iso_end_date)
        #     mock_check_fields.assert_called_once_with(db_user, data_results)
