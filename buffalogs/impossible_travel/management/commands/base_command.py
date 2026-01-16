import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from impossible_travel.constants import ExecutionModes
from impossible_travel.models import TaskSettings

logger = logging.getLogger("impossible_travel.management.commands")


class TaskLoggingCommand(BaseCommand):
    def execute(self, *args, **options):
        """
        We override execute() to prevent double handle() call.
        django BaseCommand.execute() calls handle() internally.
        We temporarily replace self.handle with a no-op, let system set up
        stdout/args, then restore and run our own logic.
        """
        original = self.handle
        self.handle = lambda *a, **kw: None
        try:
            super().execute(*args, **options)
        finally:
            self.handle = original
        return self.run_task(*args, **options)

    def run_task(self, *args, **options):
        execution_mode = options.get("execution_mode", ExecutionModes.AUTOMATIC)
        task_name = self.__class__.__module__.split(".")[-1]
        start_time = timezone.now()

        msg_start = f"Starting command '{task_name}' ({execution_mode}) at {start_time}"
        self.stdout.write(msg_start)
        logger.info(msg_start)

        task_settings = None
        success = False

        try:
            with transaction.atomic():
                task_settings, created = TaskSettings.objects.get_or_create(
                    task_name=task_name,
                    execution_mode=execution_mode,
                    defaults={"start_date": start_time, "end_date": start_time},
                )
                if not created:
                    task_settings.start_date = start_time
                    task_settings.save(update_fields=["start_date"])

                self.handle(*args, **options)
                success = True

            if success:
                end_time = timezone.now()
                task_settings.end_date = end_time
                task_settings.save(update_fields=["end_date"])

                msg_end = f"Completed command '{task_name}' ({execution_mode}) at {end_time}"
                self.stdout.write(msg_end)
                logger.info(msg_end)

        except Exception as e:
            error_msg = f"Error in command '{task_name}': {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)

            if task_settings and not success:
                try:
                    fresh = TaskSettings.objects.get(pk=task_settings.pk)
                    fresh.end_date = timezone.now()
                    fresh.save(update_fields=["end_date"])
                except Exception:
                    pass
            raise

    def handle(self, *args, **options):
        raise NotImplementedError("Subclasses must implement handle()")

    def add_arguments(self, parser):
        parser.add_argument(
            "--execution_mode",
            choices=[ExecutionModes.MANUAL, ExecutionModes.AUTOMATIC],
            default=ExecutionModes.AUTOMATIC,
            help="Specify execution mode (manual or automatic)",
        )
