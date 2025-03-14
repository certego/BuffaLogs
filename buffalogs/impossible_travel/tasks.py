from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from elasticsearch_dsl import Search, connections
from impossible_travel.alerting.alert_factory import AlertFactory
from impossible_travel.models import Alert, Config, Login, TaskSettings, User, UsersIP
from impossible_travel.modules import detection

logger = get_task_logger(__name__)


@shared_task(name="BuffalogsCleanModelsPeriodicallyTask")
def clean_models_periodically():
    """Delete old data in the models"""
    app_config = Config.objects.get(id=1)
    now = timezone.now()
    delete_user_time = now - timedelta(days=app_config.user_max_days)
    User.objects.filter(updated__lte=delete_user_time).delete()

    delete_login_time = now - timedelta(days=app_config.login_max_days)
    Login.objects.filter(updated__lte=delete_login_time).delete()

    delete_alert_time = now - timedelta(days=app_config.alert_max_days)
    Alert.objects.filter(updated__lte=delete_alert_time).delete()

    delete_ip_time = now - timedelta(days=app_config.ip_max_days)
    UsersIP.objects.filter(updated__lte=delete_ip_time).delete()


def process_user(db_user, start_date, end_date):
    """Get info for each user login and normalization

    :param db_user: user from db
    :type db_user: object
    :param start_date: start date of analysis
    :type start_date: timezone
    :param end_date: finish date of analysis
    :type end_date: timezone
    """
    fields = []
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
                "source.intelligence_category",
            ]
        )
        .sort("@timestamp")  # from the oldest to the most recent login
        .extra(size=10000)
    )
    response = s.execute()
    logger.info(f"Got {len(response)} logins for user {db_user.username}")
    for hit in response:
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
    detection.check_fields(db_user, fields)


@shared_task(name="BuffalogsProcessLogsTask")
def process_logs():
    """Find all user logged in between that time range"""
    now = timezone.now()
    process_task, _ = TaskSettings.objects.get_or_create(
        task_name=process_logs.__name__, defaults={"end_date": timezone.now() - timedelta(minutes=1), "start_date": timezone.now() - timedelta(minutes=30)}
    )
    if (now - process_task.end_date).days < 1:
        # Recovering old data avoiding task time limit
        for _ in range(6):
            start_date = process_task.end_date
            end_date = start_date + timedelta(minutes=30)
            if end_date < now:
                process_task.start_date = start_date
                process_task.end_date = end_date
                process_task.save()
                exec_process_logs(start_date, end_date)

    else:
        logger.info(f"Data lost from {process_task.end_date} to now")
        end_date = timezone.now() - timedelta(minutes=1)
        start_date = end_date - timedelta(minutes=30)
        process_task.start_date = start_date
        process_task.end_date = end_date
        process_task.save()
        exec_process_logs(start_date, end_date)


@shared_task(name="NotifyAlertsTask")
def notify_alerts():
    alert = AlertFactory().get_alert_class()
    alert.notify_alerts()


def exec_process_logs(start_date, end_date):
    """Starting the execution for the given time range

    :param start_date: Start datetime
    :type start_date: datetime
    :param end_date: End datetime
    :type end_date: datetime
    """
    logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
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
        logger.info(f"Successfully got {len(response.aggregations.login_user.buckets)} users")
        for user in response.aggregations.login_user.buckets:
            db_user, created = User.objects.get_or_create(username=user.key)
            if not created:
                # Saving user to update updated_at field
                db_user.save()
            process_user(db_user, start_date, end_date)
    except AttributeError:
        logger.info("No users login aggregation found")
