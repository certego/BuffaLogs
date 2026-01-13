import logging
from datetime import datetime

from elasticsearch.dsl import Search, connections
from impossible_travel.ingestion.base_ingestion import BaseIngestion


class ElasticsearchIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Elasticsearch ingestion source
    """

    def __init__(self, ingestion_config: dict, mapping: dict):
        """
        Constructor for the Elasticsearch Ingestion object
        """
        super().__init__(ingestion_config, mapping)
        # create the elasticsearch host connection
        connections.create_connection(hosts=self.ingestion_config["url"], request_timeout=self.ingestion_config["timeout"], verify_certs=False)
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
        response = None
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        users_list = []
        s = (
            Search(index=self.ingestion_config["indexes"])
            .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
            .query("match", **{"event.category": "authentication"})
            .query("match", **{"event.outcome": "success"})
            .query("match", **{"event.type": "start"})
            .query("exists", field="user.name")
        )
        s.aggs.bucket("login_user", "terms", field="user.name", size=self.ingestion_config["bucket_size"])
        try:
            response = s.execute()
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {connections.get_connection()}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {connections.get_connection()}")
        except Exception as e:
            self.logger.error(f"Exception while quering elasticsearch: {e}")

        if response:
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

        :return: list of the logins (dictionaries) for that username
        :rtype: list of dicts
        """
        response = None
        user_logins = []
        s = (
            Search(index=self.ingestion_config["indexes"])
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
            .extra(size=self.ingestion_config["bucket_size"])
        )
        try:
            response = s.execute()
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {connections.get_connection()}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {connections.get_connection()}")
        except Exception as e:
            self.logger.error(f"Exception while quering elasticsearch: {e}")

        # create a single standard dict (with the required fields listed in the ingestion.json config file) for each login
        if response:
            self.logger.info(f"Got {len(response)} logins for the user {username} to be normalized")

            for hit in response.hits.hits:
                hit_dict = hit.to_dict()
                tmp = {
                    "_index": "fw-proxy" if hit_dict.get("_index", "").startswith("fw-") else hit_dict.get("_index", "").split("-")[0],
                    "_id": hit_dict["_id"],
                }
                tmp.update(hit_dict["_source"])
                user_logins.append(tmp)

        return user_logins
