import json
import os
from datetime import datetime, timezone
from typing import List

import elasticsearch
from django.conf import settings
from django.test import TestCase
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
from elasticsearch_dsl.response import Hit
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion


def load_ingestion_config_data():
    with open(
        os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
        mode="r",
        encoding="utf-8",
    ) as f:
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


class ElasticsearchIngestionTestCase(TestCase):
    def setUp(self):
        self.ingestion_config = load_ingestion_config_data()
        self.elastic_config = self.ingestion_config["elasticsearch"]
        self.elastic_config["url"] = "http://localhost:9200"
        self.list_to_be_added_cloud = load_test_data("test_data_elasticsearch_cloud")
        self.list_to_be_added_fw_proxy = load_test_data("test_data_elasticsearch_fw_proxy")
        self.es = elasticsearch.Elasticsearch(self.elastic_config["url"])
        self.template = load_elastic_template("example_template")
        connections.create_connection(hosts=self.elastic_config["url"], timeout=self.ingestion_config["elasticsearch"]["timeout"])
        self._load_elastic_template_on_elastic(template_to_be_added=self.template)
        # load test data into the 2 indexes: cloud-* and fw-proxy-*
        self._load_test_data_on_elastic(data_to_be_added=self.list_to_be_added_cloud, index="cloud-test_data")
        self._load_test_data_on_elastic(data_to_be_added=self.list_to_be_added_fw_proxy, index="fw-proxy-test_data")

    def _load_elastic_template_on_elastic(self, template_to_be_added):
        response = self.es.indices.put_template("example_template", template_to_be_added)
        # check that the template has been uploaded correctly
        self.assertTrue(response["acknowledged"])

    def tearDown(self) -> None:
        self.es.indices.delete(index="cloud-test_data", ignore=[404])
        self.es.indices.delete(index="fw-proxy-test_data", ignore=[404])

    def _bulk_gendata(self, index: str, data_list: list):
        for single_data in data_list:
            yield {"_op_type": "index", "_index": index, "_source": single_data}

    def _load_test_data_on_elastic(self, data_to_be_added: List[dict], index: str):
        bulk(self.es, self._bulk_gendata(index, data_to_be_added), refresh="true")
        # check that the data on the Elastic index has been uploaded correctly
        count = self.es.count(index=index)["count"]
        self.assertTrue(count > 0)

    def test_process_users_ConnectionError(self):
        # test the function process_users with the exception ConnectionError
        self.elastic_config["url"] = "unexisting-url"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_users(start_date, end_date)

    def test_process_users_TimeoutError(self):
        # test the function process_users with the exception TimeoutError
        self.elastic_config["timeout"] = 0.001
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_users(start_date, end_date)

    def test_process_users_Exception(self):
        # test the function process_users with a generic exception (e.g. for wrong indexes)
        self.elastic_config["indexes"] = "unexisting-index"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_users(start_date, end_date)

    def test_process_users_no_data(self):
        # test the function process_users with no data in that range time
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor.process_users(start_date, end_date)
        self.assertEqual(0, len(returned_users))
        self.assertListEqual([], returned_users)

    def test_process_users_data(self):
        # test the function process_users with data on Elasticsearch
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor.process_users(start_date, end_date)
        self.assertEqual(4, len(returned_users))
        self.assertCountEqual(["Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com", "bugs.bunny"], returned_users)

    def test_process_user_logins_ConnectionError(self):
        # test the function process_user_logins with the exception ConnectionError
        self.elastic_config["url"] = "unexisting-url"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")

    def test_process_user_logins_TimeoutError(self):
        # test the function process_user_logins with the exception TimeoutError
        self.elastic_config["timeout"] = 0.001
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")

    def test_process_user_logins_Exception(self):
        # test the function process_user_logins with a generic exception (e.g. for wrong indexes)
        self.elastic_config["indexes"] = "unexisting-index"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")

    def test_process_user_logins_data_out_of_date(self):
        # test the function process_user_logins with some data on Elasticsearch but not in the specific datetime range
        start_date = datetime(2025, 2, 26, 8, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 10, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        user1_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")
        self.assertEqual(0, len(user1_logins))
        user2_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="scooby.doo@gmail.com")
        self.assertEqual(0, len(user2_logins))
        user3_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs-bunny@organization.com")
        self.assertEqual(0, len(user3_logins))
        user4_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny")
        self.assertEqual(0, len(user4_logins))
        user5_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny2")
        self.assertEqual(0, len(user5_logins))

    def test_process_user_logins_data_out_of_date_some(self):
        # test the function process_user_logins with some data on Elasticsearch in the specific datetime range
        expected_return_user1 = load_test_data("test_data_elasticsearch_returned_logins_user1")
        expected_return_user2 = load_test_data("test_data_elasticsearch_returned_logins_user2")
        expected_return_user3 = load_test_data("test_data_elasticsearch_returned_logins_user3")
        expected_return_user4 = load_test_data("test_data_elasticsearch_returned_logins_user4")
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        user1_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")
        self.assertEqual(2, len(user1_logins))
        self.assertDictEqual(expected_return_user1[0], user1_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user1[1], user1_logins.hits.hits[1]["_source"].to_dict())
        user2_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="scooby.doo@gmail.com")
        self.assertEqual(4, len(user2_logins))
        self.assertDictEqual(expected_return_user2[0], user2_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user2[1], user2_logins.hits.hits[1]["_source"].to_dict())
        self.assertDictEqual(expected_return_user2[2], user2_logins.hits.hits[2]["_source"].to_dict())
        self.assertDictEqual(expected_return_user2[3], user2_logins.hits.hits[3]["_source"].to_dict())
        user3_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs-bunny@organization.com")
        self.assertEqual(4, len(user3_logins))
        self.assertDictEqual(expected_return_user3[0], user3_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user3[1], user3_logins.hits.hits[1]["_source"].to_dict())
        self.assertDictEqual(expected_return_user3[2], user3_logins.hits.hits[2]["_source"].to_dict())
        self.assertDictEqual(expected_return_user3[3], user3_logins.hits.hits[3]["_source"].to_dict())
        user4_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny")
        self.assertEqual(1, len(user4_logins))
        self.assertDictEqual(expected_return_user4[0], user4_logins.hits.hits[0]["_source"].to_dict())
        user5_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny2")
        self.assertEqual(0, len(user5_logins))

    def test_process_user_logins_data_all(self):
        # test the function process_user_logins with all data on Elasticsearch in the specific datetime range
        expected_return_user1 = load_test_data("test_data_elasticsearch_returned_logins_user1")
        expected_return_user2 = load_test_data("test_data_elasticsearch_returned_logins_user2")
        expected_return_user3 = load_test_data("test_data_elasticsearch_returned_logins_user3")
        expected_return_user4 = load_test_data("test_data_elasticsearch_returned_logins_user4")
        expected_return_user5 = load_test_data("test_data_elasticsearch_returned_logins_user5")
        start_date = datetime(2025, 2, 26, 10, 40, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 18, 10, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        user1_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")
        self.assertEqual(2, len(user1_logins))
        self.assertDictEqual(expected_return_user1[0], user1_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user1[1], user1_logins.hits.hits[1]["_source"].to_dict())
        user2_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="scooby.doo@gmail.com")
        self.assertEqual(4, len(user2_logins))
        self.assertDictEqual(expected_return_user2[0], user2_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user2[1], user2_logins.hits.hits[1]["_source"].to_dict())
        self.assertDictEqual(expected_return_user2[2], user2_logins.hits.hits[2]["_source"].to_dict())
        self.assertDictEqual(expected_return_user2[3], user2_logins.hits.hits[3]["_source"].to_dict())
        user3_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs-bunny@organization.com")
        self.assertEqual(4, len(user3_logins))
        self.assertDictEqual(expected_return_user3[0], user3_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user3[1], user3_logins.hits.hits[1]["_source"].to_dict())
        self.assertDictEqual(expected_return_user3[2], user3_logins.hits.hits[2]["_source"].to_dict())
        self.assertDictEqual(expected_return_user3[3], user3_logins.hits.hits[3]["_source"].to_dict())
        user4_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny")
        self.assertEqual(2, len(user4_logins))
        self.assertDictEqual(expected_return_user4[0], user4_logins.hits.hits[0]["_source"].to_dict())
        self.assertDictEqual(expected_return_user4[1], user4_logins.hits.hits[1]["_source"].to_dict())
        user5_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny2")
        self.assertEqual(1, len(user5_logins))
        self.assertDictEqual(expected_return_user5[0], user5_logins.hits.hits[0]["_source"].to_dict())

    def test_normalize_fields_no_source(self):
        # test the function normalize_fields for a response without the "source" nested dict populated
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        elastic_response_to_be_normalized = {"@timestamp": "2025-02-26T13:40:35.173Z", "user": {"name": "Stitch"}, "user_agent": {"original": "Linux"}}
        expected_result = []
        actual_result = elastic_ingestor.normalize_fields(logins_response=elastic_response_to_be_normalized)
        self.assertListEqual(expected_result, actual_result)

    def test_normalize_fields_data_user1(self):
        # test the function normalize_fields for the logins response of user1
        # TODO
        elastic_response_to_be_normalized = []
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config)
        hit_data_list = load_test_data("test_data_elasticsearch_returned_logins_user1")
        hit_meta = {"_id": "login_id1", "_index": "cloud-test_data"}
        for hit_data in hit_data_list:
            elastic_response_to_be_normalized.append(Hit.from_dict({"_source": hit_data, **hit_meta}))
        expected_result = [{}]
        actual_result = elastic_ingestor.normalize_fields(logins_response=elastic_response_to_be_normalized)
        self.assertListEqual(expected_result, actual_result)

    def test_normalize_fields_data_user2(self):
        # test the function normalize_fields for the logins response of user2
        # TODO
        pass

    def test_normalize_fields_data_user3(self):
        # test the function normalize_fields for the logins response of user3
        # TODO
        pass

    def test_normalize_fields_data_user4(self):
        # test the function normalize_fields for the logins response of user4
        # TODO
        pass

    def test_normalize_fields_data_user5(self):
        # test the function normalize_fields for the logins response of user5
        # TODO
        pass
