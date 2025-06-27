import os
import random
from datetime import timedelta
from typing import Any, Dict, Generator, List

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from elasticsearch import Elasticsearch
from elasticsearch.helpers import BulkIndexError, bulk

NUM_LOGS = 2000


class Command(BaseCommand):
    help = "Generate and index fake log data into Elasticsearch for testing purposes."

    def handle(self, *args, **options) -> None:
        """
        Entry point for the management command.
        Initializes Elasticsearch and indexes generated fake logs for predefined indices.
        """
        es = Elasticsearch([settings.CERTEGO_BUFFALOGS_ELASTICSEARCH_HOST])

        indices = [i.strip() for i in settings.CERTEGO_BUFFALOGS_ELASTIC_INDEX.split(",") if i.strip()]

        for index in indices:
            data = self.generate_common_data()
            self.write_bulk(es, index, data)

        self.stdout.write(self.style.SUCCESS("Successfully indexed test data in Elasticsearch."))

    def generate_common_data(self) -> List[Dict[str, Any]]:
        """
        Generates fake log entries using random combinations of user and IP data.

        return: List of log documents
        rtype: List[Dict[str, Any]]
        """
        fields = []

        event_outcome = ["failure"] * 10 + ["success"] * 90
        event_category = ["threat"] * 2 + ["session"] * 2 + ["malware"] * 6 + ["authentication"] * 90
        event_type = ["start"] * 80 + ["end"] * 20

        read_data_file = self._read_data_from_file()
        now = timezone.now()

        for _ in range(NUM_LOGS):
            ip = random.choice(read_data_file["ip"])
            str_time = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp = str_time[:-4] + str_time[-1:]

            log_entry = {
                "@timestamp": timestamp,
                "user": {"name": random.choice(read_data_file["user_name"])},
                "event": {
                    "outcome": random.choice(event_outcome),
                    "category": random.choice(event_category),
                    "type": random.choice(event_type),
                },
                "source": {
                    "ip": ip["address"],
                    "geo": {
                        "country_name": ip["country_name"],
                        "location": {
                            "lat": ip["latitude"],
                            "lon": ip["longitude"],
                        },
                    },
                    "as": {"organization": {"name": ip["organization"]}},
                },
                "user_agent": {"original": random.choice(read_data_file["user_agent"])},
            }

            fields.append(log_entry)
            now = now + timedelta(seconds=1)

        return fields

    def _read_data_from_file(self) -> Dict[str, Any]:
        """
        Reads YAML data file containing test user and IP information.

        :return: parsed YAML data as dictionary
        :rtype: Dict[str, Any]
        """
        yaml_path = os.path.join(settings.CERTEGO_DJANGO_IMPOSSIBLE_TRAVEL_APP_DIR, "tests/test_data/random_data.yaml")

        try:
            with open(yaml_path, "r", encoding="utf-8") as info:
                return yaml.load(info, Loader=yaml.FullLoader)
        except FileNotFoundError:
            self.stderr.write(f"YAML file not found: {yaml_path}")
            raise
        except yaml.YAMLError as e:
            self.stderr.write(f"Error parsing YAML file: {e}")
            raise

    def write_bulk(self, es: Elasticsearch, index: str, msg_list: List[Dict[str, Any]]) -> None:
        """
        Writes log entries to Elasticsearch using bulk indexing.

        :param es: Elasticsearch client instance
        :param index: Name of the target index prefix
        :param msg_list: List of log documents to index

        :raises ValueError: If the index name is empty
        :raises RuntimeError: If index creation fails
        """
        index = index.removesuffix("-*")
        if not index:
            raise ValueError("Index name cannot be empty")

        now = timezone.now()
        index_name = f"{index}-test_data-{now.year}-{now.month}-{now.day}"

        # Ensure the index exists
        if not es.indices.exists(index=index_name):
            self.stdout.write(self.style.WARNING(f"Index '{index_name}' does not exist. Creating it..."))
            try:
                es.indices.create(index=index_name)
            except Exception as e:
                raise RuntimeError(f"Failed to create index '{index_name}': {e}")

        # Bulk indexing
        try:
            bulk(es, self._bulk_gendata(index_name, msg_list))
            self.stdout.write(self.style.SUCCESS(f"Successfully indexed {len(msg_list)} documents into '{index_name}'"))
        except BulkIndexError as e:
            self.stderr.write(self.style.ERROR(f"Bulk indexing failed: {e}"))
            for error in e.errors[:5]:
                self.stderr.write(self.style.ERROR(str(error)))

    def _bulk_gendata(self, index: str, msg_list: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        """
        Generator function to yield bulk indexing data for Elasticsearch.

        :param index: Name of the target index prefix
        :type index: str
        :param msg_list: List of log documents to index
        :type msg_list: List[Dict[str, Any]]
        """
        for msg in msg_list:
            yield {"_op_type": "index", "_index": index, "_source": msg}
