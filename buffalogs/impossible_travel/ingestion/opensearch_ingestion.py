import logging

from datetime import datetime
from django.conf import settings
from impossible_travel.ingestion.base_ingestion import BaseIngestion

try:
    from opensearchpy import OpenSearch
except ImportError:
    pass


class OpensearchIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Opensearch ingestion source
    """

    def __init__(self, ingestion_config: dict, mapping: dict):
        """
        Constructor for the Opensearch Ingestion object
        """
        super().__init__(ingestion_config, mapping)
        # create the opensearch host connection
        self.client = OpenSearch(
            hosts=[self.ingestion_config["url"]],
            timeout=self.ingestion_config["timeout"],
            verify_certs=False,
        )
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def process_users(self, start_date: datetime, end_date) -> list:
        """
            Concrete implementation of the BaseIngestion.process_users abstract method

            :param start_date: the initial datetime from which the users are considered
            :type start_date: datetime (with tzinfo=datetime.timezone.utc)
            :param end_date: the final datetime within which the users are considered
            :type end_date: datetime (with tzinfo=datetime.timezone.utc)

            :return: list of users strings that logged in Opensearch
            :rtype: list
            """
        # response = None
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
            # making change to already committed code on the basis that the dynamic templates stores all strings as keywords so having user.name.keyword will cause program to fail
            "aggs": {
                "login_user": {"terms": {"field": "user.name", "size": self.ingestion_config["bucket_size"]}}},
        }
        try:
            response = self.client.search(index=self.ingestion_config["indexes"], body=query)
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

    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        """
        Concrete implementation of the BaseIngestion.process_user_logins abstract method

        :param username: Username of the user that logged in
        :param start_date: the initial datetime from which the logins of the user are considered
        :param end_date: the final datetime within which the logins of the user are considered
        :return: list of the logins (dictionaries) for that specified username
        :rtype: list of dicts
        """
        response = []
        user_logins = []
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
            "size": self.ingestion_config["bucket_size"],
        }
        try:
            response = self.client.search(index=self.ingestion_config["indexes"], body=query)
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host:{self.client}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host:{self.client}")
        except Exception as e:
            self.logger.error(f"Exception while querying opensearch:{e}")
        else:
            # Process hits into standardized format
            self.logger.info(f"Got {len(response['hits']['hits'])} logins or the user {username} to be normalized")

            for hit in response["hits"]["hits"]:
                tmp = {
                    "_index": "fw-proxy" if hit.get("_index",
                                                    "").startswith("fw-") else hit.get("_index",
                                                                                       "").split("-")[0],
                    "_id": hit["_id"],
                }
                # Add source data to the tmp dict
                tmp.update(hit["_source"])
                user_logins.append(tmp)

        return user_logins
