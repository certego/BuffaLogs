import logging

from django.conf import settings
from opensearchpy import OpenSearch
from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.models import User
from impossible_travel.modules import detection


class OpensearchIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Opensearch ingestion source
    """

    def __init__(self, ingestion_config: dict):
        super().__init__()
        self.opensearch_config = ingestion_config
        # create the opensearch host connection
        self.client = OpenSearch(
            hosts=[self.opensearch_config["url"]],
            timeout=self.opensearch_config["timeout"],
            verify_certs=False,
        )
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def process_users(self, start_date, end_date) -> list:
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        users_list = []
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": start_date, "lt": end_date}}},
                        {"match": {"event.category": "authentication"}},
                        {"match": {"event.outcome": "success"}},
                        {"match": {"event.type": "start"}},
                        {"exists": {"field": "user.name"}},
                    ]
                }
            },
            "aggs": {"login_user": {"terms": {"field": "user.name.keyword", "size": self.opensearch_config["bucket_size"]}}},
        }
        try:
            response = self.client.search(index=self.opensearch_config["indexes"], body=query)
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {self.client}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {self.client}")
        except Exception as e:
            self.logger.error(f"Exception while quering opensearch: {e}")
        else:
            self.logger.info(f"Successfully got {len(response['aggregations']['login_user']['buckets'])} users")
            for user in response["aggregations"]["login_user"]["buckets"]:
                users_list.append(user["key"])
        return users_list

    def process_user_logins(self, start_date, end_date, username):
        response = []
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": start_date, "lt": end_date}}},
                        {"match": {"user.name": username}},
                        {"match": {"event.outcome": "success"}},
                        {"match": {"event.type": "start"}},
                        {"exists": {"field": "source.ip"}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "asc"}}],
            "_source": [
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
            ],
            "size": self.opensearch_config["bucket_size"],
        }
        try:
            response = self.client.search(index=self.opensearch_config["indexes"], body=query)
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {self.client}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {self.client}")
        except Exception as e:
            self.logger.error(f"Exception while quering opensearch: {e}")
        else:
            self.logger.info(f"Got {len(response['hits']['hits'])} logins for the user {username} to be normalized")
        return response["hits"]["hits"]

    def normalize_fields(self, logins_response):
        fields = []
        for hit in logins_response:
            if "_source" in hit:
                # meta
                tmp = {}
                tmp["id"] = hit["_id"]
                if hit["_index"].split("-")[0] == "fw":
                    tmp["index"] = "fw-proxy"
                else:
                    tmp["index"] = hit["_index"].split("-")[0]

                # record
                data = hit["_source"]
                tmp["timestamp"] = data["@timestamp"]
                tmp["ip"] = data["source"]["ip"]
                if "user_agent" in data:
                    tmp["agent"] = data["user_agent"]["original"]
                else:
                    tmp["agent"] = ""
                if "as" in data["source"]:
                    tmp["organization"] = data["source"]["as"]["organization"]["name"]
                if "geo" in data["source"]:
                    if "location" in data["source"]["geo"] and "country_name" in data["source"]["geo"]:
                        tmp["lat"] = data["source"]["geo"]["location"]["lat"]
                        tmp["lon"] = data["source"]["geo"]["location"]["lon"]
                        tmp["country"] = data["source"]["geo"]["country_name"]
                    else:
                        tmp["lat"] = None
                        tmp["lon"] = None
                        tmp["country"] = ""
                    fields.append(tmp)  # up to now: no geo info --> login discard
        return fields
