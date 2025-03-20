import logging

from django.conf import settings
from elasticsearch_dsl import Search, connections
from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.models import User
from impossible_travel.modules import detection


class ElasticsearchIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Elasticsearch ingestion source
    """

    def __init__(self, ingestion_config: dict):
        super().__init__()
        self.elastic_config = ingestion_config
        # create the elasticsearch host connection
        connections.create_connection(hosts=self.elastic_config["url"], timeout=self.elastic_config["timeout"], verify_certs=False)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def process_users(self, start_date, end_date) -> list:
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        users_list = []
        s = (
            Search(index=self.elastic_config["indexes"])
            .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
            .query("match", **{"event.category": "authentication"})
            .query("match", **{"event.outcome": "success"})
            .query("match", **{"event.type": "start"})
            .query("exists", field="user.name")
        )
        s.aggs.bucket("login_user", "terms", field="user.name", size=self.elastic_config["bucket_size"])
        try:
            response = s.execute()
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {connections.get_connection()}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {connections.get_connection()}")
        except Exception as e:
            self.logger.error(f"Exception while quering elasticsearch: {e}")
        else:
            self.logger.info(f"Successfully got {len(response.aggregations.login_user.buckets)} users")
            for user in response.aggregations.login_user.buckets:
                users_list.append(user.key)
            return users_list

    def process_user_logins(self, start_date, end_date, username):
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
        try:
            response = s.execute()
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {connections.get_connection()}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {connections.get_connection()}")
        except Exception as e:
            self.logger.error(f"Exception while quering elasticsearch: {e}")
        else:
            self.logger.info(f"Got {len(response)} logins for the user {username} to be normalized")
            return response

    def normalize_fields(self, logins_response):
        fields = []
        for hit in logins_response:
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
                    fields.append(tmp)  # up to now: no geo info --> login discard
        return fields
