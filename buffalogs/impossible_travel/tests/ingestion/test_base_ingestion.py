from django.test import TestCase
from impossible_travel.ingestion.elasticsearch_ingestion import ElasticsearchIngestion
from impossible_travel.tests.utils import load_ingestion_config_data, load_test_data


class TestBaseIngestion(TestCase):
    def setUp(self):
        # executed once per test (at the beginning)
        self.ingestion_config = load_ingestion_config_data()

    def test_normalize_fields_elasticsearch_user1(self):
        # test the _normalize_fields() fields normalization for Elasticsearch login response user1
        logins_returned_user1 = load_test_data(
            "test_data_elasticsearch_returned_logins_user1"
        )

        # user1
        actual_result = ElasticsearchIngestion(
            ingestion_config=self.ingestion_config["elasticsearch"],
            mapping=self.ingestion_config["elasticsearch"]["custom_mapping"],
        ).normalize_fields(logins=logins_returned_user1)
        expected_result = [
            {
                "timestamp": "2025-02-26T13:40:15.173Z",
                "id": "log_id_0",
                "index": "cloud",
                "intelligence_category": "",
                "username": "Stitch",
                "ip": "192.0.2.1",
                "agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "organization": "",
                "country": "Japan",
                "lat": 37.2924,
                "lon": 136.2759,
            },
            {
                "timestamp": "2025-02-26T13:40:35.173Z",
                "id": "log_id_3",
                "index": "cloud",
                "intelligence_category": "",
                "username": "Stitch",
                "ip": "192.0.2.1",
                "agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "organization": "",
                "country": "Japan",
                "lat": 34.2924,
                "lon": 141.2759,
            },
        ]
        self.assertEqual(len(expected_result), len(actual_result))
        self.assertListEqual(expected_result, actual_result)

    def test_normalize_fields_elasticsearch_user2(self):
        # test the _normalize_fields() fields normalization for Elasticsearch login response user2
        logins_returned_user2 = load_test_data(
            "test_data_elasticsearch_returned_logins_user2"
        )

        # user1
        actual_result = ElasticsearchIngestion(
            ingestion_config=self.ingestion_config["elasticsearch"],
            mapping=self.ingestion_config["elasticsearch"]["custom_mapping"],
        ).normalize_fields(logins=logins_returned_user2)
        expected_result = [
            {
                "timestamp": "2025-02-26T13:56:21.123Z",
                "id": "log_id_4",
                "index": "cloud",
                "intelligence_category": "",
                "username": "scooby.doo@gmail.com",
                "ip": "192.0.2.10",
                "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                "organization": "",
                "country": "Germany",
                "lat": 51.0951,
                "lon": 10.2714,
            }
        ]
        self.assertEqual(len(expected_result), len(actual_result))
        self.assertListEqual(expected_result, actual_result)

    def test_normalize_fields_elasticsearch_user3(self):
        # test the _normalize_fields() fields normalization for Elasticsearch login response user3
        logins_returned_user3 = load_test_data(
            "test_data_elasticsearch_returned_logins_user3"
        )

        # user1
        actual_result = ElasticsearchIngestion(
            ingestion_config=self.ingestion_config["elasticsearch"],
            mapping=self.ingestion_config["elasticsearch"]["custom_mapping"],
        ).normalize_fields(logins=logins_returned_user3)
        expected_result = [
            {
                "timestamp": "2025-02-26T13:57:49.953Z",
                "id": "log_id_12",
                "index": "cloud",
                "intelligence_category": "",
                "username": "bugs-bunny@organization.com",
                "ip": "192.0.2.21",
                "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                "organization": "",
                "country": "Italy",
                "lat": 41.1732,
                "lon": 12.3425,
            },
            {
                "timestamp": "2025-02-26T13:58:49.953Z",
                "id": "log_id_13",
                "index": "cloud",
                "intelligence_category": "",
                "username": "bugs-bunny@organization.com",
                "ip": "192.0.2.21",
                "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                "organization": "",
                "country": "Italy",
                "lat": 38.1732,
                "lon": 15.3425,
            },
        ]
        self.assertEqual(len(expected_result), len(actual_result))
        self.assertListEqual(expected_result, actual_result)

    def test_normalize_fields_elasticsearch_user4(self):
        # test the _normalize_fields() fields normalization for Elasticsearch login response user4
        logins_returned_user4 = load_test_data(
            "test_data_elasticsearch_returned_logins_user4"
        )

        # user1
        actual_result = ElasticsearchIngestion(
            ingestion_config=self.ingestion_config["elasticsearch"],
            mapping=self.ingestion_config["elasticsearch"]["custom_mapping"],
        ).normalize_fields(logins=logins_returned_user4)
        expected_result = [
            {
                "timestamp": "2025-02-26T13:59:59.167Z",
                "id": "log_id_2",
                "index": "fw-proxy",
                "intelligence_category": "",
                "username": "bugs.bunny",
                "ip": "192.0.2.26",
                "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                "organization": "",
                "country": "France",
                "lat": 45.6342,
                "lon": 10.2578,
            },
            {
                "timestamp": "2025-02-26T14:01:10.167Z",
                "id": "log_id_3",
                "index": "fw-proxy",
                "intelligence_category": "",
                "username": "bugs.bunny",
                "ip": "192.0.2.26",
                "agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "organization": "",
                "country": "Germany",
                "lat": 45.6342,
                "lon": 18.2578,
            },
        ]
        self.assertEqual(len(expected_result), len(actual_result))
        self.assertListEqual(expected_result, actual_result)

    def test_normalize_fields_elasticsearch_user5(self):
        # test the _normalize_fields() fields normalization for Elasticsearch login response user4
        logins_returned_user5 = load_test_data(
            "test_data_elasticsearch_returned_logins_user5"
        )

        # user1
        actual_result = ElasticsearchIngestion(
            ingestion_config=self.ingestion_config["elasticsearch"],
            mapping=self.ingestion_config["elasticsearch"]["custom_mapping"],
        ).normalize_fields(logins=logins_returned_user5)
        expected_result = [
            {
                "timestamp": "2025-02-26T14:02:10.167Z",
                "id": "log_id_4",
                "index": "fw-proxy",
                "intelligence_category": "",
                "username": "bugs.bunny2",
                "ip": "192.0.2.26",
                "agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "organization": "",
                "country": "Germany",
                "lat": 45.6342,
                "lon": 18.2578,
            }
        ]
        self.assertEqual(len(expected_result), len(actual_result))
        self.assertListEqual(expected_result, actual_result)
