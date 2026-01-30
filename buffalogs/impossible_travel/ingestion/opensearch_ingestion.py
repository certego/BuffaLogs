import logging
from datetime import datetime

from impossible_travel.ingestion.base_ingestion import BaseIngestion
from impossible_travel.utils.connection_retry import create_retry_decorator

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
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize OpenSearch connection with retry logic."""
        retry_decorator = create_retry_decorator(
            retry_config=self.retry_config,
            exception_types=(ConnectionError, TimeoutError, OSError),
            operation_name="OpenSearch connection"
        )

        @retry_decorator
        def _connect():
            self.client = OpenSearch(
                hosts=[self.ingestion_config["url"]],
                timeout=self.ingestion_config["timeout"],
                verify_certs=False,
            )
            self.client.cluster.health()
            self.logger.info(f"Successfully connected to OpenSearch at {self.ingestion_config['url']}")

        try:
            _connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to OpenSearch after all retry attempts: {e}")
            raise

    def _execute_search(self, query: dict):
        """Execute search with retry logic."""
        retry_decorator = create_retry_decorator(
            retry_config=self.retry_config,
            exception_types=(ConnectionError, TimeoutError, OSError),
            operation_name="OpenSearch search"
        )

        @retry_decorator
        def _execute():
            return self.client.search(index=self.ingestion_config["indexes"], body=query)

        return _execute()

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
            "aggs": {"login_user": {"terms": {"field": "user.name", "size": self.ingestion_config["bucket_size"]}}},
        }

        try:
            response = self._execute_search(query)
            if response and "aggregations" in response and "login_user" in response["aggregations"]:
                self.logger.info(f"Successfully got {len(response['aggregations']['login_user']['buckets'])} users")
                for user in response["aggregations"]["login_user"]["buckets"]:
                    users_list.append(user["key"])
        except Exception as e:
            self.logger.error(f"Failed to retrieve users from OpenSearch: {e}")
            raise

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
            response = self._execute_search(query)
            if response and "hits" in response and "hits" in response["hits"]:
                self.logger.info(f"Got {len(response['hits']['hits'])} logins for the user {username} to be normalized")
                for hit in response["hits"]["hits"]:
                    tmp = {
                        "_index": "fw-proxy" if hit.get("_index", "").startswith("fw-") else hit.get("_index", "").split("-")[0],
                        "_id": hit["_id"],
                    }
                    tmp.update(hit["_source"])
                    user_logins.append(tmp)
        except Exception as e:
            self.logger.error(f"Failed to retrieve logins for user {username}: {e}")
            raise

        return user_logins
