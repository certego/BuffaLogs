from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.test import TestCase
from impossible_travel.ingestion.opensearch_ingestion import OpensearchIngestion
from impossible_travel.tests.utils import load_ingestion_config_data


class OpensearchIngestionTestCase(TestCase):
    """
    Test case for OpensearchIngestion class.

    Uses setUpTestData for improved performance by loading configuration
    and static test data once per test class instead of once per test method.
    """

    @classmethod
    def setUpTestData(cls):
        cls.ingestion_config = load_ingestion_config_data()
        cls.opensearch_config = cls.ingestion_config["opensearch"]

        # Test data for process_users aggregation response
        cls.user_aggregation_response = {
            "aggregations": {
                "login_user": {
                    "buckets": [
                        {"key": "Stitch"},
                        {"key": "Jessica"},
                        {"key": "bugs-bunny@organization.com"},
                        {"key": "scooby.doo@gmail.com"},
                        {"key": "Andrew"},
                        {"key": "bugs.bunny"},
                    ]
                }
            }
        }

        # Test data for process_user_logins search response
        cls.user_logins_response = {
            "hits": {
                "hits": [
                    {
                        "_index": "cloud-test_data",
                        "_id": "log_id_0",
                        "_source": {
                            "user.name": "Stitch",
                            "@timestamp": "2025-02-26T13:40:15.173Z",
                            "source.ip": "192.0.2.1",
                            "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                            "source.as.organization.name": "",
                            "source.geo.location": {"lat": 37.2924, "lon": 136.2759},
                            "source.geo.country_name": "Japan",
                        },
                    },
                    {
                        "_index": "cloud-test_data",
                        "_id": "log_id_1",
                        "_source": {
                            "user.name": "Stitch",
                            "@timestamp": "2025-02-26T13:40:35.173Z",
                            "source.ip": "192.0.2.1",
                            "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                            "source.as.organization.name": "",
                            "source.geo.location": {"lat": 34.2924, "lon": 141.2759},
                            "source.geo.country_name": "Japan",
                        },
                    },
                ]
            }
        }

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_init(self, mock_opensearch):
        """Test OpensearchIngestion initialization"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})
        self.assertEqual(ingestor.client, mock_client)
        mock_opensearch.assert_called_once()

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_users(self, mock_opensearch):
        """Test process_users method with mocked OpenSearch response"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.return_value = self.user_aggregation_response

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        result = ingestor.process_users(start_date, end_date)
        self.assertEqual(len(result), 6)
        self.assertCountEqual(
            result,
            ["Stitch", "Jessica", "bugs-bunny@organization.com", "scooby.doo@gmail.com", "Andrew", "bugs.bunny"],
        )
        mock_client.search.assert_called_once()

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_users_connection_error(self, mock_opensearch):
        """Test process_users with connection error"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.side_effect = ConnectionError("Connection failed")

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        with self.assertLogs(ingestor.logger, level="ERROR"):
            result = ingestor.process_users(start_date, end_date)
            self.assertEqual(result, [])

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_users_no_data(self, mock_opensearch):
        """Test process_users with no aggregation data"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.return_value = {"aggregations": {"login_user": {"buckets": []}}}

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 0, tzinfo=timezone.utc)

        result = ingestor.process_users(start_date, end_date)
        self.assertEqual(len(result), 0)

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_user_logins(self, mock_opensearch):
        """Test process_user_logins method with mocked OpenSearch response"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.return_value = self.user_logins_response

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        result = ingestor.process_user_logins(start_date, end_date, "Stitch")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["user.name"], "Stitch")
        self.assertEqual(result[0]["_index"], "cloud")  # Should be normalized to "cloud"
        mock_client.search.assert_called_once()

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_user_logins_empty_result(self, mock_opensearch):
        """Test process_user_logins with empty search results"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.return_value = {"hits": {"hits": []}}

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        result = ingestor.process_user_logins(start_date, end_date, "Unknown")
        self.assertEqual(result, [])

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_user_logins_connection_error(self, mock_opensearch):
        """Test process_user_logins with connection error"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.side_effect = ConnectionError("Connection failed")

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        with self.assertLogs(ingestor.logger, level="ERROR"):
            result = ingestor.process_user_logins(start_date, end_date, "Stitch")
            self.assertEqual(result, [])

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_user_logins_missing_ip(self, mock_opensearch):
        """Test process_user_logins handles missing source.ip correctly"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client

        # Response with data missing source.ip (should be filtered by query)
        response_missing_ip = {"hits": {"hits": []}}  # OpenSearch query should filter out entries without source.ip
        mock_client.search.return_value = response_missing_ip

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        result = ingestor.process_user_logins(start_date, end_date, "StitchMissing")
        self.assertEqual(result, [])

    @patch("impossible_travel.ingestion.opensearch_ingestion.OpenSearch")
    def test_process_user_logins_field_mapping(self, mock_opensearch):
        """Test process_user_logins with field mapping"""
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        mock_client.search.return_value = self.user_logins_response

        ingestor = OpensearchIngestion(self.opensearch_config, mapping={})

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

        result = ingestor.process_user_logins(start_date, end_date, "Stitch")

        self.assertEqual(len(result), 2)
        for login in result:
            self.assertIn("user.name", login)
            self.assertIn("@timestamp", login)
            self.assertIn("source.ip", login)
            self.assertEqual(login["user.name"], "Stitch")

    def test_normalize_fields_valid_data(self):
        """Test normalize_fields with valid data (no mocking needed for data transformation)"""
        mapping = {
            "user.name": "username",
            "@timestamp": "timestamp",
            "source.ip": "ip",
            "source.geo.country_name": "country",
            "source.geo.location.lat": "lat",
            "source.geo.location.lon": "lon",
            "user_agent.original": "user_agent",
        }
        ingestor = OpensearchIngestion(self.opensearch_config, mapping=mapping)
        log_entry = {
            "user": {"name": "test_user"},
            "@timestamp": "2025-02-26T13:40:15.173Z",
            "source": {
                "ip": "192.168.1.1",
                "geo": {
                    "country_name": "Japan",
                    "location": {"lat": 35.6762, "lon": 139.6503},
                },
            },
            "user_agent": {"original": "Mozilla/5.0"},
        }
        normalized = ingestor.normalize_fields([log_entry])
        self.assertEqual(len(normalized), 1)
        normalized_entry = normalized[0]
        self.assertEqual(normalized_entry["username"], "test_user")
        self.assertEqual(normalized_entry["timestamp"], "2025-02-26T13:40:15.173Z")
        self.assertEqual(normalized_entry["ip"], "192.168.1.1")
        self.assertEqual(normalized_entry["country"], "Japan")
        self.assertEqual(normalized_entry["lat"], 35.6762)
        self.assertEqual(normalized_entry["lon"], 139.6503)
        self.assertEqual(normalized_entry["user_agent"], "Mozilla/5.0")

    def test_normalize_fields_missing_optional(self):
        """Test normalize_fields when optional fields are missing"""
        mapping = {
            "user.name": "username",
            "@timestamp": "timestamp",
            "source.ip": "ip",
            "source.geo.country_name": "country",
            "source.geo.location.lat": "lat",
            "source.geo.location.lon": "lon",
            "user_agent.original": "user_agent",
        }
        ingestor = OpensearchIngestion(self.opensearch_config, mapping=mapping)
        log_entry = {
            "user": {"name": "test_user"},
            "@timestamp": "2025-02-26T13:40:15.173Z",
            "source": {
                "ip": "192.168.1.1",
                "geo": {
                    "country_name": "Japan",
                    "location": {"lat": 35.6762, "lon": 139.6503},
                },
            },
            # Missing user_agent.original
        }
        normalized = ingestor.normalize_fields([log_entry])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["user_agent"], "")

    def test_normalize_fields_missing_required(self):
        """Test normalize_fields excludes entries with missing required fields"""
        mapping = {
            "user.name": "username",
            "@timestamp": "timestamp",
            "source.ip": "ip",
            "source.geo.country_name": "country",
            "source.geo.location.lat": "lat",
            "source.geo.location.lon": "lon",
        }
        ingestor = OpensearchIngestion(self.opensearch_config, mapping=mapping)
        log_entry = {
            "user.name": "test_user",
            "@timestamp": "2025-02-26T13:40:15.173Z",
            # Missing source.ip
            "source.geo.country_name": "Japan",
            "source.geo.location.lat": 35.6762,
            "source.geo.location.lon": 139.6503,
        }
        normalized = ingestor.normalize_fields([log_entry])
        self.assertEqual(len(normalized), 0)

    def test_normalize_nested_fields(self):
        """Test normalize_fields correctly handles nested fields"""
        mapping = {
            "source.geo.location.lat": "lat",
            "source.geo.location.lon": "lon",
            "user.name": "username",
            "@timestamp": "timestamp",
            "source.ip": "ip",
            "source.geo.country_name": "country",
        }
        ingestor = OpensearchIngestion(self.opensearch_config, mapping=mapping)
        log_entry = {
            "user": {"name": "test_user"},
            "@timestamp": "2025-02-26T13:40:15.173Z",
            "source": {
                "ip": "192.168.1.1",
                "geo": {
                    "country_name": "Japan",
                    "location": {"lat": 35.6762, "lon": 139.6503},
                },
            },
        }
        normalized = ingestor.normalize_fields([log_entry])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["lat"], 35.6762)
        self.assertEqual(normalized[0]["lon"], 139.6503)
