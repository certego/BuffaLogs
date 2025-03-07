import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from functools import reduce

from django.conf import settings
from elasticsearch_dsl import Search, connections
from impossible_travel.models import User
from impossible_travel.modules import detection


class Ingestion(ABC):
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @staticmethod
    def str_to_class(str):
        return reduce(getattr, str.split("."), sys.modules[__name__])

    @staticmethod
    def get_ingestion_sources() -> list:
        """Load the configuration ingestion JSON file in order to create the istances for the active ingestion sources

        :return: list of the ingestion config dictionaries
        :rtype: list
        """
        file_path = settings.CERTEGO_BUFFALOGS_CONFIG_INGESTION_PATH

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: The configuration file for the Ingestion: '{file_path}' doesn't exist")

        try:
            with open(os.path.join(file_path, "ingestion.json"), encoding="utf-8") as f:
                config_ingestion = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error in the parsing of the json configuration file: '{file_path}': {e}")

        active_sources = config_ingestion.get("active_ingestion_sources", [])
        ingestion_dicts = []

        for source in active_sources:
            try:
                ingestion_dicts.append(config_ingestion[source])
            except KeyError:
                Ingestion.logger.error(f"Ingestion source {source} is not supported")
                pass

        return ingestion_dicts  # return the list of config dictionaries for each active ingestion sources

    @abstractmethod
    def process_users(self, start_date: datetime, end_date: datetime, ingestion_config: dict = None):
        """Abstract method that implement the extraction of the users logged in between the time range considered defined by (start_date, end_date).
        This method will be different implemented based on the ingestion source used.

        :param start_date: the initial datetime from which the users are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the users are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)
        """
        pass

    @abstractmethod
    def process_user_logins(self, db_user: User, start_date: datetime, end_date: datetime):
        """Abstract method that implement the extraction of the logins of the given user in the time range defined by (start_date, end_date)

        :param db_user:
        :type db_user: User object
        :param start_date: the initial datetime from which the logins of the user are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the logins of the user are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)
        """
        pass

    def normalize_response_data(self, db_user: User, user_logins: list):
        """General function that normalizes the list of logins got

        :param db_user: User that has made the logins
        :type db_user: User object
        :param user_logins: list of all the logins made by the user
        :type user_logins: list of dicts
        """
        fields = []
        for hit in user_logins:
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
            self.logger.info(f"Correctly normalized {len(fields)} logins for user {db_user.username}")
        detection.check_fields(db_user, fields)


class ElasticsearchIngestion(Ingestion):
    def process_users(self, start_date: datetime, end_date: datetime, elastic_ingestion_config: dict = None) -> list:
        """Starting the execution for the given time range, in order to take all the users that have logged in to the system in that time range

        :param start_date: Start datetime
        :type start_date: datetime
        :param end_date: End datetime
        :type end_date: datetime
        :param elastic_ingestion_config: Config of the elasticsearch ingestion
        :type elastic_ingestion_config: dict

        :return: the list of User objects
        :rtype: list
        """
        logged_users_objects = []
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")

        # elasticsearch connection
        connections.create_connection(hosts=elastic_ingestion_config["url"], timeout=90, verify_certs=False)
        # elasticsaerch query to get the logged users
        s = (
            Search(index=elastic_ingestion_config["indexes"])
            .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
            .query("match", **{"event.category": "authentication"})
            .query("match", **{"event.outcome": "success"})
            .query("match", **{"event.type": "start"})
            .query("exists", field="user.name")
        )
        s.aggs.bucket("login_user", "terms", field="user.name", size=10000)
        response = s.execute()
        try:
            self.logger.info(f"Successfully got {len(response.aggregations.login_user.buckets)} users")
            for user in response.aggregations.login_user.buckets:
                if user.key:  # to discard a not well-defined user, for example: "user":{"name": ""}
                    db_user, created = User.objects.get_or_create(username=user.key)
                    if not created:
                        # Saving user to update the "updated_at" field
                        db_user.save()
                # self._process_user(db_user, start_date, end_date)
        except AttributeError:
            self.logger.info("No users logged in found")
        return logged_users_objects

    def process_user_logins(self, db_user: User, start_date: datetime, end_date: datetime, ingestion_config: dict):
        """Get info for each user login and normalization

        :param db_user: user from db
        :type db_user: object
        :param start_date: start date of analysis
        :type start_date: timezone
        :param end_date: finish date of analysis
        :type end_date: timezone
        """
        s = (
            Search(index=ingestion_config["elasticsearch"]["indexes"])
            .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
            .query("match", **{"user.name": db_user.username})
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
                ]
            )
            .sort("@timestamp")  # from the oldest to the most recent login
            .extra(size=10000)
        )
        # the returned timestamp got by Elastic is in the isoformat: '2025-02-24T09:45:10.930Z'
        response = s.execute()
        self.logger.info(f"Got {len(response)} logins for user {db_user.username}")
        self._parse_elasticsearch_response(db_user, response)

    def _parse_elasticsearch_response(self, db_user, response):
        user_logins = []
        # transform data from the Elasticsearch "Hit" objects to a list of dicts of the logins made by the user considered
        for hit in response:
            user_logins.append(hit.to_dict())
        self.normalize_response_data(db_user=db_user, user_logins=user_logins)
