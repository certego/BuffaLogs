import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from impossible_travel.tasks import exec_process_logs, process_logs

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Impossible Travel tasks call to run the detection manually"

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument("start_date", nargs="?", type=str, help="Start datetime from which begin the detection")
        parser.add_argument("end_date", nargs="?", type=str, help="End datetime for the detection")

    def handle(self, *args, **options):
        """Run the detection manually with the commands: manage.py impossible_travel
        or with the start and end dates, for example: manage.py impossible_travel '2022-11-02 10:00:00' '2022-11-02 10:30:00'
        """
        logger = logging.getLogger()
        if options["start_date"] and options["end_date"]:
            try:
                start_date_obj = datetime.strptime(options["start_date"], "%Y-%m-%d %H:%M:%S")
                end_date_obj = datetime.strptime(options["end_date"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.info("Time data does not match format '%Y-%m-%d %H:%M:%S'")

            self.stdout.write(self.style.SUCCESS(f"Starting detection from {start_date_obj} and {end_date_obj}"))
            exec_process_logs(start_date_obj, end_date_obj)

        elif options["start_date"] or options["end_date"]:
            self.stdout.write(self.style.ERROR("Error: missing one argument"))

        else:
            process_logs()
