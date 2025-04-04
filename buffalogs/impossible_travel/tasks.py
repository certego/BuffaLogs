from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
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


@shared_task(name="BuffalogsProcessLogsTask")
def process_logs():
    """Set the datetime range within which the users must be considered and start the detection"""
    ingestion_factory = IngestionFactory()
    ingestion = ingestion_factory.get_ingestion_class()
    normalized_user_logins = []
    date_ranges = []
    now = timezone.now()
    process_task, _ = TaskSettings.objects.get_or_create(
        task_name=process_logs.__name__,
        defaults={
            "end_date": now - timedelta(minutes=1),
            "start_date": now - timedelta(minutes=30),
        },
    )

    if (now - process_task.end_date).days < 1:
        # Recovering old data avoiding task time limit
        for _ in range(6):
            start_date = process_task.end_date
            end_date = start_date + timedelta(minutes=30)
            if end_date < now:
                date_ranges.append((start_date, end_date))
                process_task.end_date = end_date
    else:
        logger.info(f"Data lost from {process_task.end_date} to now")
        end_date = now - timedelta(minutes=1)
        start_date = end_date - timedelta(minutes=30)
        date_ranges.append((start_date, end_date))
        process_task.end_date = end_date

    if date_ranges:
        process_task.start_date = date_ranges[0][0]
        process_task.save()

        # get the users that logged into the system in those time ranges
        for start_date, end_date in date_ranges:
            usernames_list = ingestion.process_users(start_date, end_date)

            # for each user returned, get the related logins
            for username in usernames_list:
                user_logins = ingestion.process_user_logins(start_date, end_date, username)

                # normalize logins in order to map them into the buffalogs fields
                for login in user_logins:
                    normalized_data = {
                        buffalogs_key: ingestion_factory._normalize_fields(login, ingestion_key)
                        for ingestion_key, buffalogs_key in ingestion_factory.mapping.items()
                    }
                    # skip logins without timestamp, ip, country, latitude or longitude (for now)
                    if (
                        normalized_data["timestamp"]
                        and normalized_data["ip"]
                        and normalized_data["country"]
                        and normalized_data["lat"]
                        and normalized_data["lon"]
                    ):
                        normalized_user_logins.append(normalized_data)

                logger.info(f"Got {len(normalized_user_logins)} actual useful logins for the user {username}")

                # if valid logins have been found, add the user into the DB and start the detection
                if normalized_user_logins:
                    db_user, created = User.objects.get_or_create(username=username)
                    if not created:
                        # Saving user anyway to update updated_at field in order to take track of the recent users seen
                        db_user.save()
                    detection.check_fields(db_user=db_user, fields=normalized_user_logins)
