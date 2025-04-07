import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

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
            {
                "user.name": "Stitch",
                "@timestamp": "2025-02-26T13:40:15.173Z",
                "_id": "log_id_0",
                "index": "cloud-test_data",
                "source.ip": "192.0.2.1",
                "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "source.as.organization.name": "",
                "source.geo.location.lat": 37.2924,
                "source.geo.location.lon": 136.2759,
                "source.geo.country_name": "Japan",
            },
            {
                "user.name": "Stitch",
                "@timestamp": "2025-02-26T13:40:35.173Z",
                "_id": "log_id_1",
                "index": "cloud-test_data",
                "source.ip": "192.0.2.1",
                "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "source.as.organization.name": "",
                "source.geo.location.lat": 34.2924,
                "source.geo.location.lon": 141.2759,
                "source.geo.country_name": "Japan",
            },
        ]

    @patch("splunklib.client.connect")
    def test_init(self, mock_connect):
        mock_service = MagicMock()
        mock_connect.return_value = mock_service

        ingestor = SplunkIngestion(self.splunk_config, mapping={})
        mock_connect.assert_called_once_with(
            host=self.splunk_config["host"],
            port=self.splunk_config["port"],
            username=self.splunk_config["username"],
            password=self.splunk_config["password"],
            scheme=self.splunk_config["scheme"],
        )
        self.assertEqual(ingestor.service, mock_service)

    @patch("splunklib.client.connect")
    def test_process_users(self, mock_connect):
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        mock_job = MagicMock()
        mock_job.is_done.return_value = True
        mock_results = [
            {"user.name": "Stitch"},
            {"user.name": "scooby.doo@gmail.com"},
        ]

        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = mock_results

        with patch("splunklib.results.ResultsReader", return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            ingestor = SplunkIngestion(self.splunk_config, mapping={})

            start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
            end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

            result = ingestor.process_users(start_date, end_date)
            self.assertCountEqual(result, ["Stitch", "scooby.doo@gmail.com"])
            mock_service.jobs.create.assert_called_once()

    @patch("splunklib.client.connect")
    def test_process_users_connection_error(self, mock_connect):
        mock_connect.side_effect = ConnectionError("Connection failed")
        with self.assertLogs(level="ERROR") as cm:
            ingestor = SplunkIngestion(self.splunk_config, mapping={})
            result = ingestor.process_users(
                start_date=datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc),
                end_date=datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(result, [])
        self.assertIn("Failed to establish a connection", cm.output[0])

    @patch("splunklib.client.connect")
    def test_process_user_logins(self, mock_connect):
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        mock_job = MagicMock()
        mock_job.is_done.return_value = True

        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = self.user1_test_data

        with patch("splunklib.results.ResultsReader", return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            ingestor = SplunkIngestion(self.splunk_config, mapping={})

            start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
            end_date = datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc)

            result = ingestor.process_user_logins(start_date, end_date, "Stitch")
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["user.name"], "Stitch")
            mock_service.jobs.create.assert_called_once()

    @patch("splunklib.client.connect")
    def test_process_user_logins_empty_result(self, mock_connect):
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        mock_job = MagicMock()
        mock_job.is_done.return_value = True

        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = []

        with patch("splunklib.results.ResultsReader", return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            ingestor = SplunkIngestion(self.splunk_config, mapping={})

            result = ingestor.process_user_logins(
                start_date=datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc),
                end_date=datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc),
                username="Unknown",
            )
            self.assertEqual(result, [])

    @patch("splunklib.client.connect")
    def test_process_user_logins_missing_ip(self, mock_connect):
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        mock_job = MagicMock()
        mock_job.is_done.return_value = True

        # Data missing source.ip (should be filtered out by Splunk query)
        test_data = (
            [
                {
                    "user.name": "Stitch",
                    "@timestamp": "2025-02-26T13:40:15.173Z",
                    "_id": "log_id_0",
                    "index": "cloud-test_data",
                    "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                    "source.as.organization.name": "",
                    "source.geo.location.lat": 37.2924,
                    "source.geo.location.lon": 136.2759,
                    "source.geo.country_name": "Japan",
                }
            ],
        )

        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = test_data

        with patch("splunklib.results.ResultsReader", return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            ingestor = SplunkIngestion(self.splunk_config, mapping={})
            result = ingestor.process_user_logins(
                start_date=datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc),
                end_date=datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc),
                username="Stitch",
            )
            self.assertEqual(result, [])

    @patch("splunklib.client.connect")
    def test_process_user_logins_field_mapping(self, mock_connect):
        mock_service = MagicMock()
        mock_connect.return_value = mock_service
        mock_job = MagicMock()
        mock_job.is_done.return_value = True

        mock_results_reader = MagicMock()
        mock_results_reader.__iter__.return_value = self.user1_test_data

        with patch("splunklib.results.ResultsReader", return_value=mock_results_reader):
            mock_service.jobs.create.return_value = mock_job
            ingestor = SplunkIngestion(self.splunk_config, mapping={})
            result = ingestor.process_user_logins(
                start_date=datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc),
                end_date=datetime(2025, 2, 26, 14, 0, tzinfo=timezone.utc),
                username="Stitch",
            )

            self.assertEqual(len(result), len(self.user1_test_data))
            for expected, actual in zip(self.user1_test_data, result):
                for key in expected:
                    self.assertIn(key, actual)
                    self.assertEqual(actual[key], expected[key])
