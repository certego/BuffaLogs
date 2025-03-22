import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from elasticsearch_dsl import Search, connections
from impossible_travel.models import User


class TestViewsElasticIngestion(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User(username="Bradyn Ortega")  # user from random_data.yaml
        user.save()
        cls.user = user

    def setUp(self):
        self.maxDiff = None
        self.client = Client()
        self.read_config()

    def test_get_all_logins(self):
        url = reverse("get_all_logins", kwargs={"pk_user": self.user.id})
        response = self.client.get(url)
        expected_logins = self.get_expected_logins()
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.json())
        self.assertEqual(content, expected_logins)

    def read_config(self):
        with open(os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json"), mode="r", encoding="utf-8") as f:
            config = json.load(f)
            self.elastic_config = config["elasticsearch"]

    def get_expected_logins(self):
        end_date = timezone.now()
        start_date = end_date + timedelta(days=-365)
        username = self.user.username
        connections.create_connection(hosts=self.elastic_config["url"], timeout=self.elastic_config["timeout"], verify_certs=False)
        s = (
            Search(index=self.elastic_config["indexes"])
            .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
            .query("match", **{"user.name": username})
            .query("match", **{"event.outcome": "success"})
            .query("match", **{"event.type": "start"})
            .query("exists", field="source.ip")
            .source(
                includes=[
                    "user.name",
                    "@timestamp",
                    "source.geo.location.lat",
                    "source.geo.location.lon",
                    "source.geo.country_name",
                    "source.as.organization.name",
                    "user_agent.original",
                    "_index",
                    "source.ip",
                    "_id",
                    "source.intelligence_category",
                ]
            )
            .sort("@timestamp")  # from the oldest to the most recent login
            .extra(size=self.elastic_config["bucket_size"])
        )
        response = s.execute()
        fields = []
        for hit in response:
            if "source" in hit:
                tmp = {"timestamp": hit["@timestamp"]}
                tmp["id"] = hit.meta["id"]
                if hit.meta["index"].split("-")[0] == "fw":
                    tmp["index"] = "fw-proxy"
                else:
                    tmp["index"] = hit.meta["index"].split("-")[0]
                tmp["ip"] = hit["source"]["ip"]
                if "user_agent" in hit:
                    tmp["agent"] = hit["user_agent"]["original"]
                else:
                    tmp["agent"] = ""
                if "as" in hit.source:
                    tmp["organization"] = hit["source"]["as"]["organization"]["name"]
                if "geo" in hit.source:
                    if "location" in hit.source.geo and "country_name" in hit.source.geo:
                        tmp["lat"] = hit["source"]["geo"]["location"]["lat"]
                        tmp["lon"] = hit["source"]["geo"]["location"]["lon"]
                        tmp["country"] = hit["source"]["geo"]["country_name"]
                    else:
                        tmp["lat"] = None
                        tmp["lon"] = None
                        tmp["country"] = ""
                    fields.append(tmp)
        return fields
