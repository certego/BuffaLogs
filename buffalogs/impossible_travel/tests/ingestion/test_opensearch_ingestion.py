import json
import os
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlparse

from django.conf import settings
from django.test import TestCase
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

from impossible_travel.ingestion.opensearch_ingestion import (
    OpensearchIngestion,
)


def create_opensearch_client(config):
    parsed = urlparse(config["url"])

    return OpenSearch(
        hosts=[{"host": parsed.hostname, "port": parsed.port}],
        http_auth=(config["username"], config["password"]),
        timeout=config.get("timeout", 30),
        use_ssl=parsed.scheme == "https",
        verify_certs=False,
    )


def load_ingestion_config_data():
    with open(
        os.path.join(
            settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"
        ),
        mode="r",
        encoding="utf-8",
    ) as f:
        config_ingestion = json.load(f)
    return config_ingestion


def load_example_data(name):
    with open(
        os.path.join(
            settings.CERTEGO_BUFFALOGS_CONFIG_PATH,
            "elasticsearch/",
            name + ".json",
        )
    ) as file:
        data = json.load(file)
    return data


class OpensearchIngestionTestCase(TestCase):
    def setUp(self):
        # Executes once per test
        self.ingestion_config = load_ingestion_config_data()
        self.opensearch_config = self.ingestion_config["opensearch"]
        self.opensearch_config["url"] = "http://localhost:9200"

        # test data for cloud index - users: Stitch, Jessica, bugs-bunny@organization.com
        self.user1_test_data = [
            {
                "user.name": "Stitch",
                "@timestamp": "2025-02-26T13:40:15.173Z",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "source.ip": "192.0.2.1",
                "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "source.as.organization.name": "",
                "source.geo.location": {"lat": 37.2924, "lon": 136.2759},
                "source.geo.country_name": "Japan",
            },
            {
                "user.name": "Stitch",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:40:35.173Z",
                "source.ip": "192.0.2.1",
                "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "source.as.organization.name": "",
                "source.geo.location": {"lat": 34.2924, "lon": 141.2759},
                "source.geo.country_name": "Japan",
            },
            {
                "user.name": "Jessica",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:45:12.123Z",
                "source.ip": "192.0.2.5",
                "user_agent.original": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, "
                "like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "source.as.organization.name": "Example ISP",
                "source.geo.location": {"lat": 40.7128, "lon": -74.0060},
                "source.geo.country_name": "United States",
            },
            {
                "user.name": "bugs-bunny@organization.com",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:57:49.953Z",
                "source.ip": "192.0.2.21",
                "user_agent.original": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/78.0.3904.108 Safari/537.36",
                "source.as.organization.name": "",
                "source.geo.location": {"lat": 41.1732, "lon": 12.3425},
                "source.geo.country_name": "Italy",
            },
        ]

        # test data for fw-proxy index - users: scooby.doo@gmail.com, Andrew, bugs.bunny
        self.user2_test_data = [
            {
                "user.name": "scooby.doo@gmail.com",
                "event.category": "authentication",
                "event.outcome": "success",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:56:21.123Z",
                "source.ip": "192.0.2.10",
                "user_agent.original": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
                "source.as.organization.name": "",
                "source.geo.location": {"lat": 51.0951, "lon": 10.2714},
                "source.geo.country_name": "Germany",
            },
            {
                "user.name": "Andrew",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:40:18.253Z",
                "source.ip": "192.0.2.2",
                "source.geo.country_name": "Japan",
                "source.geo.location": {"lat": 35.7426, "lon": 137.6321},
                "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
            },
            {
                "user.name": "bugs.bunny",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:59:59.167Z",
                "source.ip": "192.0.2.26",
                "user_agent.original": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
                "source.as.organization.name": "",
                "source.geo.location": {"lat": 45.6342, "lon": 10.2578},
                "source.geo.country_name": "France",
            },
        ]

        self.os = create_opensearch_client(self.opensearch_config)
        self.template = load_example_data("example_template")

        self._load_example_template_on_opensearch(
            template_to_be_added=self.template
        )
        # load test data into the 2 indexes: cloud-* and fw-proxy-*
        self._load_test_data_on_opensearch(
            data_to_be_added=self.user1_test_data, index="cloud-test_data"
        )
        self._load_test_data_on_opensearch(
            data_to_be_added=self.user2_test_data, index="fw-proxy-test_data"
        )

    def _load_example_template_on_opensearch(self, template_to_be_added):
        response = self.os.indices.put_index_template(
            name="example_template", body=template_to_be_added
        )
        self.assertTrue(response["acknowledged"])

    def _load_test_data_on_opensearch(
        self, data_to_be_added: List[dict], index: str
    ):
        bulk(
            self.os,
            self._bulk_gendata(index, data_to_be_added),
            refresh="true",
        )
        # Check that the data has been uploaded correctly
        count = self.os.count(index=index)["count"]
        self.assertTrue(count > 0)

    def tearDown(self) -> None:
        # executed once per test (at the end)
        self.os.indices.delete(index="cloud-test_data", ignore=[404])
        self.os.indices.delete(index="fw-proxy-test_data", ignore=[404])

    def _bulk_gendata(self, index: str, data_list: list):
        for single_data in data_list:
            yield {
                "_op_type": "index",
                "_id": f"log_id_{data_list.index(single_data)}",
                "_index": index,
                "_source": single_data,
            }

    def test_process_users_ConnectionError(self):
        self.opensearch_config["url"] = "http://doesntexist-url:8888"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        with self.assertLogs(opensearch_ingestor.logger, level="ERROR"):
            opensearch_ingestor.process_users(start_date, end_date)

    def test_process_users_Exception(self):
        # Test the function process_users with a generic exception (e.g. for wrong indexes)
        self.opensearch_config["indexes"] = "unexisting-index"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        with self.assertLogs(opensearch_ingestor.logger, level="ERROR"):
            opensearch_ingestor.process_users(start_date, end_date)

    def test_process_users_no_data(self):
        # Test the function process_users with NO DATA in that range time
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        returned_users = opensearch_ingestor.process_users(
            start_date, end_date
        )
        self.assertEqual(0, len(returned_users))

    def test_process_users_data(self):
        # Test the function process_users with data in OpenSearch
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 30, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        # Users returned should be all users from the test data
        returned_users = opensearch_ingestor.process_users(
            start_date, end_date
        )
        self.assertEqual(6, len(returned_users))
        self.assertCountEqual(
            [
                "Stitch",
                "Jessica",
                "bugs-bunny@organization.com",
                "scooby.doo@gmail.com",
                "Andrew",
                "bugs.bunny",
            ],
            returned_users,
        )

    def test_process_user_logins_ConnectionError(self):
        # Test the function process_user_logins with the exception ConnectionError
        self.opensearch_config["url"] = "http://unexisting-url:8888"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        with self.assertLogs(opensearch_ingestor.logger, level="ERROR"):
            opensearch_ingestor.process_user_logins(
                start_date, end_date, username="Stitch"
            )

    def test_process_user_logins_Exception(self):
        # Test the function process_user_logins with a generic exception (e.g. for wrong indexes)
        self.opensearch_config["indexes"] = "unexisting-index"
        start_date = datetime(2025, 2, 26, 11, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 12, 00, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        with self.assertLogs(opensearch_ingestor.logger, level="ERROR"):
            opensearch_ingestor.process_user_logins(
                start_date, end_date, username="Stitch"
            )

    def test_process_user_logins_data_out_of_date(self):
        # Test the function process_user_logins with some data on OpenSearch but not in the specific datetime range
        start_date = datetime(2025, 2, 26, 8, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 10, 00, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        user1_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="Stitch"
        )
        self.assertEqual(0, len(user1_logins))
        user2_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="Jessica"
        )
        self.assertEqual(0, len(user2_logins))
        user3_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="bugs-bunny@organization.com"
        )
        self.assertEqual(0, len(user3_logins))
        user4_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="Andrew"
        )
        self.assertEqual(0, len(user4_logins))
        user5_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="bugs.bunny"
        )
        self.assertEqual(0, len(user5_logins))

    def test_process_user_logins(self):
        # Test the function process_user_logins with some data on OpenSearch in the specific datetime range
        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 30, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )

        # User1 - jessica (should have 1 login)
        user1_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="Jessica"
        )
        self.assertEqual(1, len(user1_logins))
        self.assertEqual(user1_logins[0]["user.name"], "Jessica")
        self.assertEqual(
            user1_logins[0]["source.geo.country_name"], "United States"
        )

    def test_process_user_logins_empty_result(self):

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 30, tzinfo=timezone.utc)
        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )

        user_login = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="Johnathan Doe"
        )
        self.assertEqual([], user_login)

    def test_process_user_logins_missing_ip(self):
        test_data = [
            {
                "user.name": "StitchMissing",
                "@timestamp": "2025-02-26T13:40:15.173Z",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                # source.ip is intentionally missing for this test
                "user_agent.original": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                "source.as.organization.name": "",
                "source.geo.location": {"lat": 37.2924, "lon": 136.2759},
                "source.geo.country_name": "Japan",
            }
        ]

        index_name = "cloud-missing-ip-test"
        self._load_test_data_on_opensearch(
            data_to_be_added=test_data, index=index_name
        )

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 30, tzinfo=timezone.utc)

        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=self.opensearch_config,
            mapping=self.opensearch_config["custom_mapping"],
        )
        # for this test, I had to create a new username because a basic username like "Stitch" already exists in the test db. In the setup() method the test data is loaded but before it can cleared up again this test runs and that is why a new user is needed.
        user_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="StitchMissing"
        )

        self.assertEqual([], user_logins)

        # Clean up the test index
        self.os.indices.delete(index="cloud-missing-ip-test", ignore=[404])

    def test_process_user_logins_field_mapping(self):
        # Test that field mapping works correctly in process_user_logins
        # Set up test data with a unique username
        test_data = [
            {
                "user.name": "Jane Doe",
                "event.outcome": "success",
                "event.category": "authentication",
                "event.type": "start",
                "@timestamp": "2025-02-26T13:40:15.173Z",
                "source.ip": "192.0.2.100",
                "user_agent.original": "Mozilla/5.0 (Test Browser)",
                "source.as.organization.name": "Test ISP",
                "source.geo.location": {"lat": 40.7128, "lon": -74.0060},
                "source.geo.country_name": "United States",
            }
        ]

        index_name = "cloud-mapping-test"
        self._load_test_data_on_opensearch(
            data_to_be_added=test_data, index=index_name
        )

        start_date = datetime(2025, 2, 26, 13, 30, tzinfo=timezone.utc)
        end_date = datetime(2025, 2, 26, 14, 30, tzinfo=timezone.utc)

        custom_mapping = {
            "user.name": "username",
            "@timestamp": "timestamp",
            "source.ip": "ip_address",
            "source.geo.country_name": "country",
            "source.geo.location.lat": "latitude",
            "source.geo.location.lon": "longitude",
            "user_agent.original": "browser",
        }

        test_config = self.opensearch_config.copy()
        test_config["custom_mapping"] = custom_mapping

        opensearch_ingestor = OpensearchIngestion(
            ingestion_config=test_config, mapping=custom_mapping
        )

        user_logins = opensearch_ingestor.process_user_logins(
            start_date, end_date, username="Jane Doe"
        )

        self.assertEqual(1, len(user_logins))
        login = user_logins[0]
        self.assertEqual("Jane Doe", login["user.name"])
        self.assertEqual("2025-02-26T13:40:15.173Z", login["@timestamp"])
        self.assertEqual("192.0.2.100", login["source.ip"])
        self.assertEqual("United States", login["source.geo.country_name"])

        # clean up the test index
        self.os.indices.delete(index="cloud-mapping-test", ignore=[404])
