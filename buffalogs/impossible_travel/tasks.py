from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from impossible_travel.models import Alert, Config, Login, TaskSettings, User, UsersIP
from impossible_travel.modules.ingestion_handler import Ingestion

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


def validate_datetime(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("start_date and end_date must be timezone-aware datetime objects")
    return value


@shared_task(name="BuffalogsProcessLogsTask")
def process_logs(given_start_date: datetime = None, given_end_date: datetime = None):
    """Process logs in a given date range, or default to the last 30 minutes.

    :param start_date: datetime from which to start the detection
    :type start_date: timezone-aware datetime object
    :param end_date: datetime up to which to carry out the detection
    :type end_date: timezone-aware datetime object
    """
    # validate the datetimes if start_date and end_date are passed by the mgmt command
    now = timezone.now()
    try:
        if given_start_date and given_end_date:
            start_date = validate_datetime(given_start_date)
            end_date = validate_datetime(given_end_date)
    except ValueError as e:
        logger.error(f"The datetime given has an invalid datetime format: {e}")
        return

    # get all the active ingestion sources
    ingestion_dicts = Ingestion.get_ingestion_sources()

    # get or create a TaskSetting object for each active ingestion source in order to keep track of the execution times of each job
    for ingestion in ingestion_dicts:
        process_task, _ = TaskSettings.objects.get_or_create(
            task_name=process_logs.__name__,
            ingestion_source=ingestion["class_name"],
            defaults={"start_date": now - timedelta(minutes=30), "end_date": now - timedelta(minutes=1)},
        )

        for _ in range(6):
            if (now - process_task.end_date).days >= 1:
                logger.info(f"Data lost from {process_task.end_date} to now")
                start_date = now - timedelta(minutes=31)
                end_date = now - timedelta(minutes=1)
            else:
                start_date = process_task.end_date
                end_date = process_task.end_date + timedelta(minutes=30)

            if end_date > now:
                break

            process_task.start_date, process_task.end_date = start_date, end_date
            process_task.save()
            Ingestion.str_to_class(ingestion["class_name"]).process_users(start_date=start_date, end_date=end_date, ingestion_config=ingestion)
