from datetime import datetime, timezone

import elasticsearch
from django.test import TestCase
from elasticsearch_dsl import connections
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.utils.ingestion_utils import bulk_write_documents, load_ingestion_config_data, load_template_data
from impossible_travel.utils.test_utils import load_test_data


class ElasticsearchIngestionTestCase(TestCase):
    def setUp(self):
        # executed once per test (at the beginning)
        self._cleanup_test_indices(["cloud-test_data-*", "fw-proxy-test_data-*"])
        # Load ingestion config
        self.ingestion_config = load_ingestion_config_data()
        self.elastic_config = self.ingestion_config["elasticsearch"]
        self.elastic_config["url"] = "http://localhost:9200"

        # Create ES client and connection
        self.es = elasticsearch.Elasticsearch(self.elastic_config["url"])
        connections.create_connection(hosts=self.elastic_config["url"], timeout=self.elastic_config["timeout"])

        # Load test data
        self.list_to_be_added_cloud = load_test_data("test_data_elasticsearch_cloud")
        self.list_to_be_added_fw_proxy = load_test_data("test_data_elasticsearch_fw_proxy")

        # Load and upload template
        response = load_template_data("example_template")
        self.assertTrue(response["acknowledged"])

        # Load test data into indices
        bulk_write_documents(self.es, "cloud-*", self.list_to_be_added_cloud)
        bulk_write_documents(self.es, "fw-proxy-*", self.list_to_be_added_fw_proxy)

    def _cleanup_test_indices(self, patterns):
        for pattern in patterns:
            try:
                indices = self.es.indices.get(index=pattern)
                for index in indices:
                    self.es.indices.delete(index=index)
            except elasticsearch.exceptions.NotFoundError:
                pass

    def test_data_ingestion_cloud(self):
        # testing that the cloud-test_data-* index has been loaded correctly and that it contains docs
        index_pattern = "cloud-test_data-*"

        # Check that test data is not empty
        self.assertIsInstance(self.list_to_be_added_cloud, list, "Cloud test data is not a list")
        self.assertGreater(len(self.list_to_be_added_cloud), 0, "No cloud test documents loaded into memory")

        # Check that the index exists
        self.assertTrue(self.es.indices.exists(index=index_pattern), f"Index '{index_pattern}' does not exist")

        # Check that the index contains documents
        response = self.es.search(index=index_pattern, body={"query": {"match_all": {}}})
        doc_count = response["hits"]["total"]["value"]
        print(f"Found {doc_count} documents in index '{index_pattern}'")
        self.assertGreater(doc_count, 0, f"No documents found in index '{index_pattern}'")

    def test_data_ingestion_fw_proxy(self):
        # testing that the fw-proxy-test_data-* index has been loaded correctly and that it contains docs
        index_pattern = "fw-proxy-test_data-*"

        # Check that test data is not empty
        self.assertIsInstance(self.list_to_be_added_fw_proxy, list, "FW proxy test data is not a list")
        self.assertGreater(len(self.list_to_be_added_fw_proxy), 0, "No fw-proxy test documents loaded into memory")

        # Check that the index exists
        self.assertTrue(self.es.indices.exists(index=index_pattern), f"Index '{index_pattern}' does not exist")

        # Check that the index contains documents
        response = self.es.search(index=index_pattern, body={"query": {"match_all": {}}})
        doc_count = response["hits"]["total"]["value"]
        print(f"Found {doc_count} documents in index '{index_pattern}'")
        self.assertGreater(doc_count, 0, f"No documents found in index '{index_pattern}'")

    def test_process_users_ConnectionError(self):
        # test the function process_users with the exception ConnectionError
        self.elastic_config["url"] = "http://unexisting-url:8888"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_users(start_date, end_date)

    def test_process_users_TimeoutError(self):
        # test the function process_users with the exception TimeoutError
        self.elastic_config["timeout"] = 0.001
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_users(start_date, end_date)

    def test_process_users_Exception(self):
        # test the function process_users with a generic exception (e.g. for wrong indexes)
        self.elastic_config["indexes"] = "unexisting-index"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_users(start_date, end_date)

    def test_process_users_no_data(self):
        # test the function process_users with no data in that range time
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor.process_users(start_date, end_date)
        self.assertEqual(0, len(returned_users))
        self.assertListEqual([], returned_users)

    def test_process_users_data(self):
        # test the function process_users with data on Elasticsearch
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        # users returned should be: "Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com" (from "cloud" index)
        # and "bugs.bunny" (from "fw-proxy" index)
        returned_users = elastic_ingestor.process_users(start_date, end_date)
        self.assertEqual(4, len(returned_users))
        self.assertCountEqual(["Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com", "bugs.bunny"], returned_users)

    def test_process_user_logins_ConnectionError(self):
        # test the function process_user_logins with the exception ConnectionError
        self.elastic_config["url"] = "http://unexisting-url:8888"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")

    def test_process_user_logins_TimeoutError(self):
        # test the function process_user_logins with the exception TimeoutError
        self.elastic_config["timeout"] = 0.001
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")

    def test_process_user_logins_Exception(self):
        # test the function process_user_logins with a generic exception (e.g. for wrong indexes)
        self.elastic_config["indexes"] = "unexisting-index"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        with self.assertLogs(elastic_ingestor.logger, level="ERROR"):
            elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")

    def test_process_user_logins_data_out_of_date(self):
        # test the function process_user_logins with some data on Elasticsearch but not in the specific datetime range
        start_date = datetime(2025, 2, 26, 8, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 10, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
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
        expected_logins_user1 = load_test_data("test_data_elasticsearch_returned_logins_user1")
        expected_logins_user2 = load_test_data("test_data_elasticsearch_returned_logins_user2")
        expected_logins_user3 = load_test_data("test_data_elasticsearch_returned_logins_user3")
        expected_logins_user4 = load_test_data("test_data_elasticsearch_returned_logins_user4")
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        # user1 logins
        user1_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")
        self.assertEqual(2, len(user1_logins))
        self.assertListEqual(expected_logins_user1, user1_logins)
        # user2 logins
        user2_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="scooby.doo@gmail.com")
        self.assertEqual(4, len(user2_logins))
        self.assertListEqual(expected_logins_user2, user2_logins)
        # user3 logins
        user3_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs-bunny@organization.com")
        self.assertEqual(4, len(user3_logins))
        self.assertListEqual(expected_logins_user3, user3_logins)
        # user4 logins
        user4_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny")
        self.assertEqual(1, len(user4_logins))
        # only the first login in this time range
        self.assertListEqual([expected_logins_user4[0]], user4_logins)
        # user5 logins
        user5_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny2")
        self.assertEqual(0, len(user5_logins))
        self.assertListEqual([], user5_logins)

    def test_process_user_logins_data_all(self):
        # test the function process_user_logins with all data on Elasticsearch in the specific datetime range
        expected_return_user1 = load_test_data("test_data_elasticsearch_returned_logins_user1")
        expected_return_user2 = load_test_data("test_data_elasticsearch_returned_logins_user2")
        expected_return_user3 = load_test_data("test_data_elasticsearch_returned_logins_user3")
        expected_return_user4 = load_test_data("test_data_elasticsearch_returned_logins_user4")
        expected_return_user5 = load_test_data("test_data_elasticsearch_returned_logins_user5")
        start_date = datetime(2025, 2, 26, 10, 40, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 18, 10, tzinfo=timezone.utc)
        elastic_ingestor = ElasticsearchIngestion(ingestion_config=self.elastic_config, mapping=self.elastic_config["custom_mapping"])
        # user1 logins
        user1_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="Stitch")
        self.assertEqual(2, len(user1_logins))
        self.assertListEqual(expected_return_user1, user1_logins)
        # user2 logins
        user2_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="scooby.doo@gmail.com")
        self.assertEqual(4, len(user2_logins))
        self.assertListEqual(expected_return_user2, user2_logins)
        # user3 logins
        user3_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs-bunny@organization.com")
        self.assertEqual(4, len(user3_logins))
        self.assertListEqual(expected_return_user3, user3_logins)
        # user4 logins
        user4_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny")
        self.assertEqual(2, len(user4_logins))
        self.assertListEqual(expected_return_user4, user4_logins)
        # user5 logins
        user5_logins = elastic_ingestor.process_user_logins(start_date, end_date, username="bugs.bunny2")
        self.assertEqual(1, len(user5_logins))
        self.assertListEqual(expected_return_user5, user5_logins)
