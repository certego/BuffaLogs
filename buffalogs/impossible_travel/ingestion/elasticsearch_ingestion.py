import logging
from datetime import datetime

from elasticsearch_dsl import Search, connections
from impossible_travel.ingestion.base_ingestion import BaseIngestion


class ElasticsearchIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Elasticsearch ingestion source
    """

    def __init__(self, ingestion_config: dict):
        """
        Constructor for the Elasticsearch Ingestion object
        """
        super().__init__()
        self.elastic_config = ingestion_config
        # create the elasticsearch host connection
        connections.create_connection(hosts=self.elastic_config["url"], timeout=self.elastic_config["timeout"], verify_certs=False)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        """
        Concrete implementation of the BaseIngestion.process_users abstract method

        :param start_date: the initial datetime from which the users are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the users are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: list of users strings that logged in Elasticsearch
        :rtype: list
        """
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
            if response.aggregations:
                self.logger.info(f"Successfully got {len(response.aggregations.login_user.buckets)} users")
                for user in response.aggregations.login_user.buckets:
                    if user.key:  # exclude not well-formatted usernames (e.g. "")
                        users_list.append(user.key)
        return users_list

    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        """
        Concrete implementation of the BaseIngestion.process_user_logins abstract method

        :param username: username of the user that logged in Elasticsearch
        :type username: str
        :param start_date: the initial datetime from which the logins of the user are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the logins of the user are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: Elasticsearch response of logins of that username
        :rtype: elasticsearch_dsl.response.Response
        """
        s = (
            Search(index=self.elastic_config["indexes"])
            .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
            .query("match", **{"user.name": username})
            .query("match", **{"event.category": "authentication"})
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
        """
        Concrete implementation of the BaseIngestion.normalize_fields abstract method

        :param logins_response: user related logins returned by the Elasticsearch query
        :type logins_response: Elasticsearch response

        :return: list of normalized logins
        :rtype: list
        """
        fields = []
        for hit in logins_response:
            if "source" in hit:
                tmp = {
                    "timestamp": hit["@timestamp"],
                    "id": getattr(getattr(hit, "meta", {}), "id", ""),
                    "index": "fw-proxy" if getattr(getattr(hit, "meta", {}), "index", "").startswith("fw-") else getattr(hit.meta, "index", "").split("-")[0],
                    "ip": hit["source"]["ip"],
                    "agent": getattr(getattr(hit, "user_agent", {}), "original", ""),
                    "organization": getattr(getattr(getattr(getattr(hit, "source", {}), "as", {}), "organization", {}), "name", ""),
                }

                # geolocation fields
                geo_dict = getattr(getattr(hit, "source", {}), "geo", {})
                if "location" in geo_dict and "country_name" in geo_dict:
                    # no geo info --> login discard
                    tmp.update(
                        {
                            "lat": getattr(getattr(geo_dict, "location", {}), "lat", None),
                            "lon": getattr(getattr(geo_dict, "location", {}), "lon", None),
                            "country": getattr(getattr(geo_dict, "location", {}), "country_name", ""),
                        }
                    )

                    fields.append(tmp)
        return fields
