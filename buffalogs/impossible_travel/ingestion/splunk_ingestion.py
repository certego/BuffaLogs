import logging
from datetime import datetime

try:
    from splunklib import client, results
except ImportError:
    pass
from impossible_travel.ingestion.base_ingestion import BaseIngestion


class SplunkIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Splunk ingestion source
    """

    def __init__(self, ingestion_config: dict, mapping: dict):
        """
        Constructor for the Splunk Ingestion object
        """
        super().__init__(ingestion_config, mapping)
        try:
            # Create the Splunk host connection
            self.service = client.connect(
                host=self.ingestion_config.get("host", "localhost"),
                port=self.ingestion_config.get("port", 8089),
                username=self.ingestion_config.get("username"),
                password=self.ingestion_config.get("password"),
                scheme=self.ingestion_config.get("scheme", "http"),
            )
        except ConnectionError as e:
            logging.error("Failed to establish a connection: %s", e)
            self.service = None

        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        """
        Concrete implementation of the BaseIngestion.process_users abstract method

        :param start_date: Initial datetime from which users are considered
        :param end_date: Final datetime within which users are considered
        :return: List of user strings that logged in Splunk
        """
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        users_list = []

        # Format dates for Splunk query
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        query = f"""
            search index={self.ingestion_config["indexes"]}
            earliest="{start_date_str}" latest="{end_date_str}"
            event.category="authentication" event.outcome="success" event.type="start"
            | stats count by user.name
            | where isnotnull(user.name) AND user.name!=""
        """

        try:
            search_kwargs = {
                "earliest_time": start_date_str,
                "latest_time": end_date_str,
                "exec_mode": "normal",
                "count": self.ingestion_config.get("bucket_size", 10000),
            }

            search_job = self.service.jobs.create(query, **search_kwargs)

            while not search_job.is_done():
                search_job.refresh()

            results_reader = results.ResultsReader(search_job.results())
            for result in results_reader:
                if isinstance(result, dict) and "user.name" in result:
                    users_list.append(result["user.name"])

            self.logger.info(f"Successfully got {len(users_list)} users")

        except ConnectionError:
            self.logger.error(
                f"Failed to establish a connection with host: {self.ingestion_config.get('host')}"
            )
        except TimeoutError:
            self.logger.error(
                f"Timeout reached for the host: {self.ingestion_config.get('host')}"
            )
        except Exception as e:
            self.logger.error(f"Exception while querying Splunk: {e}")
        return users_list

    def process_user_logins(
        self, start_date: datetime, end_date: datetime, username: str
    ) -> list:
        """
        Concrete implementation of the BaseIngestion.process_user_logins abstract method

        :param username: Username of the user that logged in
        :param start_date: Initial datetime from which logins are considered
        :param end_date: Final datetime within which logins are considered
        :return: List of login dictionaries for the specified user
        """
        response = []

        # Format dates for Splunk query
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Build Splunk query to get login events for the specific user
        query = f"""
            search index={self.ingestion_config["indexes"]}
            earliest="{start_date_str}" latest="{end_date_str}"
            user.name="{username}" event.category="authentication" event.outcome="success" event.type="start"
            | where isnotnull(source.ip)
            | fields user.name, _time AS "@timestamp", source.geo.location.lat, source.geo.location.lon,
              source.geo.country_name, source.as.organization.name, user_agent.original, index, source.ip, _id,
              source.intelligence_category
            | sort 0 @timestamp
        """
        try:
            search_kwargs = {
                "earliest_time": start_date_str,
                "latest_time": end_date_str,
                "exec_mode": "normal",
                "count": self.ingestion_config.get("bucket_size", 10000),
            }

            search_job = self.service.jobs.create(query, **search_kwargs)

            # Wait for the job to complete
            while not search_job.is_done():
                search_job.refresh()

            results_reader = results.ResultsReader(search_job.results())
            for result in results_reader:
                if isinstance(result, dict):
                    response.append(result)

            self.logger.info(
                f"Got {len(response)} logins for user {username} to be normalized"
            )

        except ConnectionError:
            self.logger.error(
                f"Failed to establish a connection with host: {self.ingestion_config.get('host')}"
            )
        except TimeoutError:
            self.logger.error(
                f"Timeout reached for the host: {self.ingestion_config.get('host')}"
            )
        except Exception as e:
            self.logger.error(f"Exception while querying Splunk: {e}")
        return response
