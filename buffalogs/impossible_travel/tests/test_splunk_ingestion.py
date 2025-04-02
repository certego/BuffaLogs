import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.test import TestCase
from impossible_travel.ingestion.splunk_ingestion import SplunkIngestion


def load_ingestion_config_data():
    with open(
        os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"),
        mode="r",
        encoding="utf-8",
    ) as f:
        config_ingestion = json.load(f)
    return config_ingestion


def load_test_data(name):
    with open(os.path.join(settings.CERTEGO_DJANGO_PROJ_BASE_DIR, "impossible_travel/tests/test_data/", name + ".json")) as file:
        data = json.load(file)
    return data


class SplunkIngestionTestCase(TestCase):
    def setUp(self):
        self.ingestion_config = load_ingestion_config_data()
        # Create a fake Splunk config based on the elasticsearch config structure
        self.splunk_config = {
            "host": "localhost",
            "port": 8089,
            "username": "admin",
            "password": "changeme",
            "scheme": "https",
            "timeout": 90,
            "indexes": "cloud-*,fw-proxy-*",
            "bucket_size": 10000,
        }
        # Setup test data
        self.user1_test_data = [
            {"user.name": "Stitch", "@timestamp": "2025-02-26T13:40:15.173Z", "_id": "log_id_0", "index": "cloud-test_data",
             "source.ip": "192.0.2.1", "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
             "source.as.organization.name": "", "source.geo.location.lat": 37.2924, "source.geo.location.lon": 136.2759, 
             "source.geo.country_name": "Japan"},
            {"user.name": "Stitch", "@timestamp": "2025-02-26T13:40:35.173Z", "_id": "log_id_1", "index": "cloud-test_data",
             "source.ip": "192.0.2.1", "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
             "source.as.organization.name": "", "source.geo.location.lat": 34.2924, "source.geo.location.lon": 141.2759, 
             "source.geo.country_name": "Japan"}
        ]
        
        # Set up expected results for normalize_fields
        self.expected_normalized_user1 = [
            {
                "timestamp": "2025-02-26T13:40:15.173Z",
                "id": "log_id_0",
                "index": "cloud",
                "ip": "192.0.2.1",
                "agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "organization": "",
                "lat": 37.2924,
                "lon": 136.2759,
                "country": "Japan",
            },
            {
                "timestamp": "2025-02-26T13:40:35.173Z",
                "id": "log_id_1",
                "index": "cloud",
                "ip": "192.0.2.1",
                "agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "organization": "",
                "lat": 34.2924,
                "lon": 141.2759,
                "country": "Japan",
            },
        ]

    @patch('splunklib.client.connect')
    def test_init(self, mock_connect):
        # Test that initialization sets up the connection properly
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        
        ingestor = SplunkIngestion(self.splunk_config)
        
        # Check that connect was called with the right parameters
        mock_connect.assert_called_once_with(
            host=self.splunk_config["host"],
            port=self.splunk_config["port"],
            username=self.splunk_config["username"],
            password=self.splunk_config["password"],
            scheme=self.splunk_config["scheme"]
        )
        
        # Verify service was set
        self.assertEqual(ingestor.service, mock_service)

    @patch('splunklib.client.connect')
    def test_process_users(self, mock_connect):
        # Setup mock
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        
        # Setup mock job
        mock_job = MagicMock()
        mock_job.is_done.return_value = True
        
        # Setup mock results reader
        mock_results = [
            {"user.name": "Stitch"},
            {"user.name": "scooby.doo@gmail.com"},
            {"user.name": "bugs-bunny@organization.com"},
            {"user.name": "bugs.bunny"}
        ]
        
        # Configure the mock job to return our results
        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = mock_results
        
        with patch('splunklib.results.ResultsReader', return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            
            ingestor = SplunkIngestion(self.splunk_config)
            start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
            end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
            
            result = ingestor.process_users(start_date, end_date)
            
            # Verify result
            self.assertEqual(len(result), 4)
            self.assertCountEqual(result, ["Stitch", "scooby.doo@gmail.com", "bugs-bunny@organization.com", "bugs.bunny"])
            
            # Verify search was called with expected parameters
            mock_service.jobs.create.assert_called_once()

    @patch('splunklib.client.connect')
    def test_process_users_connection_error(self, mock_connect):
        # Setup mock to raise ConnectionError
        mock_connect.side_effect = ConnectionError("Connection failed")
        
        # Test that error is handled properly
        with self.assertLogs(level="ERROR") as cm:
            ingestor = SplunkIngestion(self.splunk_config)
            start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
            end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
            
            result = ingestor.process_users(start_date, end_date)
            
            # Verify result is empty
            self.assertEqual(result, [])
        
        # Verify log message
        self.assertIn("Failed to establish a connection", cm.output[0])

    @patch('splunklib.client.connect')
    def test_process_user_logins(self, mock_connect):
        # Setup mock
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        
        # Setup mock job
        mock_job = MagicMock()
        mock_job.is_done.return_value = True
        
        # Setup mock results
        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = self.user1_test_data
        
        with patch('splunklib.results.ResultsReader', return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            
            ingestor = SplunkIngestion(self.splunk_config)
            start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
            end_date = datetime(2025, 2, 26, 14, 00, tzinfo=timezone.utc)
            
            result = ingestor.process_user_logins(start_date, end_date, "Stitch")
            
            # Verify result structure
            self.assertEqual(len(result["hits"]["hits"]), 2)
            self.assertEqual(result["hits"]["hits"][0]["user.name"], "Stitch")
            self.assertEqual(result["_shards"]["total"], 1)
            
            # Verify search was called with expected parameters
            mock_service.jobs.create.assert_called_once()

    @patch('splunklib.client.connect')
    def test_normalize_fields(self, mock_connect):
        # Setup mock
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        
        # Create the ingestion object
        ingestor = SplunkIngestion(self.splunk_config)
        
        # Create a mock response similar to what process_user_logins would return
        mock_response = {
            "hits": {
                "hits": self.user1_test_data
            },
            "_shards": {
                "total": 1,
                "successful": 1,
                "skipped": 0,
                "failed": 0
            }
        }
        
        # Test normalize_fields
        result = ingestor.normalize_fields(mock_response)
        
        # Verify the normalized fields
        self.assertEqual(len(result), 2)
        self.assertEqual(result, self.expected_normalized_user1)

    @patch('splunklib.client.connect')
    def test_normalize_fields_no_data(self, mock_connect):
        # Setup mock
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        
        # Create the ingestion object
        ingestor = SplunkIngestion(self.splunk_config)
        
        # Test with empty response
        result = ingestor.normalize_fields({})
        
        # Verify empty result
        self.assertEqual(result, [])

    @patch('splunklib.client.connect')
    def test_normalize_fields_missing_geo(self, mock_connect):
        # Setup mock
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        
        # Create the ingestion object
        ingestor = SplunkIngestion(self.splunk_config)
        
        # Create data with missing geo fields
        data_missing_geo = [
            {"user.name": "Stitch", "@timestamp": "2025-02-26T13:40:15.173Z", "_id": "log_id_0", "index": "cloud-test_data",
             "source.ip": "192.0.2.1", "user_agent.original": "Mozilla/5.0", "source.as.organization.name": ""}
        ]
        
        mock_response = {
            "hits": {
                "hits": data_missing_geo
            },
            "_shards": {
                "total": 1,
                "successful": 1,
                "skipped": 0,
                "failed": 0
            }
        }
        
        # Test normalize_fields
        result = ingestor.normalize_fields(mock_response)
        
        # Verify empty result (should skip entries with missing geo data)
        self.assertEqual(result, [])