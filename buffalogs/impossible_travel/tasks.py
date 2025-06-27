from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from impossible_travel.alerting.alert_factory import AlertFactory
from impossible_travel.ingestion.ingestion_factory import IngestionFactory
from impossible_travel.models import Alert, Config, Login, TaskSettings, User, UsersIP
from impossible_travel.modules import detection

logger = get_task_logger(__name__)


def delete_old_data(model, days):
    """Helper function to delete old data,takes model and days as args"""
    now = timezone.now()
    delete_time = now - timedelta(days=days)
    model.objects.filter(updated__lte=delete_time).delete()


@shared_task(name="BuffalogsCleanModelsPeriodicallyTask")
def clean_models_periodically():
    """Delete old data in the models"""
    app_config, _ = Config.objects.get_or_create(id=1)

    delete_old_data(User, app_config.user_max_days)
    delete_old_data(Login, app_config.login_max_days)
    delete_old_data(Alert, app_config.alert_max_days)


@shared_task(name="BuffalogsProcessLogsTask")
def process_logs(start_date=None, end_date=None):
    """Set the datetime range within which the users must be considered and start the detection"""
    ingestion_factory = IngestionFactory()
    ingestion = ingestion_factory.get_ingestion_class()
    date_ranges = []

    if start_date and end_date:
        date_ranges.append((start_date, end_date))
    else:
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

        # get the users that logged into the system in those time ranges
        for start_date, end_date in date_ranges:
            process_task.start_date = start_date
            process_task.end_date = end_date
            process_task.save()

            usernames_list = ingestion.process_users(start_date, end_date)

            # for each user returned, get the related logins
            for username in usernames_list:
                user_logins = ingestion.process_user_logins(start_date, end_date, username)

                parsed_logins = ingestion.normalize_fields(logins=user_logins)

                logger.info(f"Got {len(parsed_logins)} actual useful logins for the user {username}")

                # if valid logins have been found, add the user into the DB and start the detection
                if parsed_logins:
                    db_user, created = User.objects.get_or_create(username=username)
                    if not created:
                        # Saving user anyway to update updated_at field in order to take track of the recent users seen
                        db_user.save()
                    detection.check_fields(db_user=db_user, fields=parsed_logins)


@shared_task(name="NotifyAlertsTask")
def notify_alerts():
    active_alerters = AlertFactory().get_alert_classes()
    for alerter in active_alerters:
        # Reset the notified status to False for each alerter
        Alert.objects.all().update(notified=False)
        # This will again set the notified status to True
        alerter.notify_alerts()
