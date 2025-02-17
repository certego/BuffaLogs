import logging
from abc import ABC, abstractmethod
from datetime import datetime

from django.conf import settings
from elasticsearch_dsl import Search, connections
from impossible_travel.constants import IngestionSourceType
from impossible_travel.models import TaskSettings, User
from impossible_travel.modules import detection


class Ingestion(ABC):
    def __init__(self, task_settings: TaskSettings):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.task_settings = task_settings

    @staticmethod
    def get_ingestion_source(task_settings: TaskSettings):
        """Static method to get the Ingestion type, based on the TaskSettings.ingestion_source value

        :param task_settings: TaskSettings object to get the ingestion source
        :type: TaskSettings object
        """
        match task_settings.ingestion_source:
            case IngestionSourceType.ELASTICSEARCH:
                return ElasticsearchIngestion(task_settings)
            # add here the future sources
            case _:
                raise TypeError(f"Ingestion source: {task_settings.ingestion_source} is not supported")

    @abstractmethod
    def _exec_process_logs(self, start_date: datetime, end_date: datetime):
        """Starting the execution for the given time range

        :param start_date: Start datetime
        :type start_date: datetime
        :param end_date: End datetime
        :type end_date: datetime
        """ """Abstract method that implement the extraction of the users logged in between the time range considered defined by (start_date, end_date)

        this method will be different implemented based on the ingestion source used
        """
        raise NotImplementedError

    @abstractmethod
    def _process_user(self, db_user: User, start_date: datetime, end_date: datetime):
        """Abstract method that implement the extraction of the logins of the given user in the time range defined by (start_date, end_date)

        :param db_user:
        :type db_user: User object
        :param start_date:   (with tzinfo=datetime.timezone.utc)
        :type start_date:
        :param end_date:   (with tzinfo=datetime.timezone.utc)
        :type end_date:
        """
        raise NotImplementedError

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
    def _exec_process_logs(self, start_date: datetime, end_date: datetime):
        """Starting the execution for the given time range

        :param start_date: Start datetime
        :type start_date: datetime
        :param end_date: End datetime
        :type end_date: datetime
        """
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        connections.create_connection(hosts=settings.CERTEGO_ELASTICSEARCH, timeout=90, verify_certs=False)
        s = (
            Search(index=settings.CERTEGO_BUFFALOGS_ELASTIC_INDEX)
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
                db_user, created = User.objects.get_or_create(username=user.key)
                if not created:
                    # Saving user to update updated_at field
                    db_user.save()
                self._process_user(db_user, start_date, end_date)
        except AttributeError:
            self.logger.info("No users login aggregation found")

    def _process_user(self, db_user: User, start_date: datetime, end_date: datetime):
        """Get info for each user login and normalization

        :param db_user: user from db
        :type db_user: object
        :param start_date: start date of analysis
        :type start_date: timezone
        :param end_date: finish date of analysis
        :type end_date: timezone
        """
        s = (
            Search(index=settings.CERTEGO_BUFFALOGS_ELASTIC_INDEX)
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
        response = s.execute()
        self.logger.info(f"Got {len(response)} logins for user {db_user.username}")
        self._parse_elasticsearch_response(db_user, response)

    def _parse_elasticsearch_response(self, db_user, response):
        user_logins = []
        # transform data from the Elasticsearch "Hit" objects to a list of dicts of the logins made by the user considered
        for hit in response:
            user_logins.append(hit.to_dict())
        self.normalize_response_data(db_user=db_user, user_logins=user_logins)
