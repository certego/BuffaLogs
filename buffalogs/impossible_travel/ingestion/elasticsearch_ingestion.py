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
        response = {}
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
        if not isinstance(logins_response, dict):
            # assume it's a Response object
            logins_response = logins_response.to_dict()

        fields = []
        for hit in logins_response.get("hits", {}).get("hits", []):
            source_data = hit.get("_source", {})
            if "source" in source_data:
                tmp = {
                    "timestamp": source_data.get("@timestamp", ""),
                    "id": hit.get("_id", ""),
                    "index": "fw-proxy" if hit.get("_index", "").startswith("fw-") else hit.get("_index", "").split("-")[0],
                    "ip": source_data.get("source", {}).get("ip", ""),
                    "agent": source_data.get("user_agent", {}).get("original", ""),
                    "organization": source_data.get("source", {}).get("as", {}).get("organization", {}).get("name", ""),
                }

                # geolocation fields
                geo_dict = source_data.get("source", {}).get("geo", {})
                if geo_dict.get("location", {}).get("lat", "") and geo_dict.get("location", {}).get("lon", "") and geo_dict.get("country_name", {}):
                    # no all of the geo info (latitude, longitude and country_name) --> login discarded (up to now)
                    tmp.update(
                        {
                            "lat": geo_dict["location"]["lat"],
                            "lon": geo_dict["location"]["lon"],
                            "country": geo_dict["country_name"],
                        }
                    )

                    fields.append(tmp)
        return fields
