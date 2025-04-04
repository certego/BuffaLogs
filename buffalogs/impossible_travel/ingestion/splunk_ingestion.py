import logging
from datetime import datetime

import splunklib.client as client
import splunklib.results as results
from impossible_travel.ingestion.base_ingestion import BaseIngestion


class SplunkIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Splunk ingestion source
    """

    def __init__(self, ingestion_config: dict):
        """
        Constructor for the Splunk Ingestion object
        """
        super().__init__()
        self.splunk_config = ingestion_config
        try:
            # create the splunk host connection
            self.service = client.connect(
                host=self.splunk_config.get("host", "localhost"),
                port=self.splunk_config.get("port", 8089),
                username=self.splunk_config.get("username"),
                password=self.splunk_config.get("password"),
                scheme=self.splunk_config.get("scheme", "http"),
            )
        except ConnectionError as e:
            logging.error("Failed to establish a connection: %s", e)
            self.service = None

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        """
        Concrete implementation of the BaseIngestion.process_users abstract method

        :param start_date: the initial datetime from which the users are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the users are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: list of users strings that logged in Splunk
        :rtype: list
        """
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        users_list = []

        # Format dates for Splunk query
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        query = f"""
            search index={self.splunk_config["indexes"]}
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
                "count": self.splunk_config.get("bucket_size", 10000),
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
            self.logger.error(f"Failed to establish a connection with host: {self.splunk_config.get('host')}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {self.splunk_config.get('host')}")
        except Exception as e:
            self.logger.error(f"Exception while querying Splunk: {e}")
        return users_list

    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        """
        Concrete implementation of the BaseIngestion.process_user_logins abstract method

        :param username: username of the user that logged in Splunk
        :type username: str
        :param start_date: the initial datetime from which the logins of the user are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the logins of the user are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: Splunk response of logins of that username
        :rtype: list
        """

        response = []

        # Format dates for Splunk query
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Build Splunk query to get login events for specific user
        query = f"""
            search index={self.splunk_config["indexes"]}
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
                "count": self.splunk_config.get("bucket_size", 10000),
            }

            search_job = self.service.jobs.create(query, **search_kwargs)

            # Waiting for the job to complete
            while not search_job.is_done():
                search_job.refresh()

            results_reader = results.ResultsReader(search_job.results())
            for result in results_reader:
                if isinstance(result, dict):
                    response.append(result)

            self.logger.info(f"Got {len(response)} logins for the user {username} to be normalized")

        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {self.splunk_config.get('host')}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {self.splunk_config.get('host')}")
        except Exception as e:
            self.logger.error(f"Exception while querying Splunk: {e}")
        return {"hits": {"hits": response}}

    def normalize_fields(self, logins_response):
        """
        Concrete implementation of the BaseIngestion.normalize_fields abstract method

        :param logins_response: user related logins returned by the Splunk query
        :type logins_response: Splunk response

        :return: list of normalized logins
        :rtype: list
        """
        fields = []

        hits = logins_response.get("hits", {}).get("hits", [])

        for hit in hits:
            if "source.ip" in hit:  # In results, each hit is already a dict (not a nested _source)
                tmp = {
                    "timestamp": hit.get("@timestamp", ""),
                    "id": hit.get("_id", ""),
                    "index": "fw-proxy" if hit.get("index", "").startswith("fw-") else hit.get("index", "").split("-")[0],
                    "ip": hit.get("source.ip", ""),
                    "agent": hit.get("user_agent.original", ""),
                    "organization": hit.get("source.as.organization.name", ""),
                }

                if hit.get("source.geo.location.lat") and hit.get("source.geo.location.lon") and hit.get("source.geo.country_name"):
                    # no all of the geo info (latitude, longitude and country_name) --> login discarded (up to now)
                    tmp.update(
                        {
                            "lat": hit["source.geo.location.lat"],
                            "lon": hit["source.geo.location.lon"],
                            "country": hit["source.geo.country_name"],
                        }
                    )

                    fields.append(tmp)
        return fields
