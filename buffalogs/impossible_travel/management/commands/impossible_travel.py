import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils import timezone
from elasticsearch_dsl import Search, connections
from impossible_travel.models import TaskSettings, User
from impossible_travel.tasks import process_logs, process_user, update_risk_level


class Command(BaseCommand):
    help = "Impossible Travel tasks call"

    def handle(self, *args, **options):
        logger = logging.getLogger()
        now = timezone.now()
        while True:
            try:
                process_task = TaskSettings.objects.get(task_name=process_logs.__name__)
                start_date = process_task.end_date
                end_date = start_date + timedelta(minutes=30)
                process_task.start_date = start_date
                process_task.end_date = end_date
                process_task.save()
            except ObjectDoesNotExist:
                end_date = timezone.now()
                start_date = end_date + timedelta(minutes=-30)
                TaskSettings.objects.create(task_name=process_logs.__name__, start_date=start_date, end_date=end_date)

            logger = logging.getLogger()
            logger.info(f"Starting at:{start_date} Finishing at:{end_date}")
            connections.create_connection(hosts=settings.CERTEGO_ELASTICSEARCH, timeout=90)
            s = Search(index="cloud-*").filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}}).exclude("match", **{"event.outcome": "failure"})
            s.aggs.bucket("login_user", "terms", field="user.name", size=10000)
            response = s.execute()

            for user in response.aggregations.login_user.buckets:
                db_user, created = User.objects.get_or_create(username=user.key)
                if not created:
                    db_user.save()
                process_user(db_user, start_date, end_date)
                update_risk_level()

            if end_date >= now:
                break
