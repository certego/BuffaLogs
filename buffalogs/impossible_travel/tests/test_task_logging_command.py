import importlib
import io
import logging
import pkgutil
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase
from impossible_travel.constants import ExecutionModes
from impossible_travel.management.commands.base_command import TaskLoggingCommand
from impossible_travel.models import TaskSettings

COMMANDS_PACKAGE = "impossible_travel.management.commands"


class TaskLoggingCommandTests(TestCase):
    def setUp(self):
        self.stream = io.StringIO()
        self.logger = logging.getLogger("impossible_travel.management.commands")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = True
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)

    def test_all_commands_log_and_create_tasksettings_both_modes(self):
        modules = pkgutil.iter_modules(importlib.import_module(COMMANDS_PACKAGE).__path__)
        commands = [name for _, name, _ in modules if name != "_base"]

        for command_name in commands:
            module = importlib.import_module(f"{COMMANDS_PACKAGE}.{command_name}")
            CommandClass = getattr(module, "Command", None)

            if not CommandClass or not issubclass(CommandClass, TaskLoggingCommand):
                continue

            for mode in [ExecutionModes.MANUAL, ExecutionModes.AUTOMATIC]:
                with self.subTest(command=command_name, mode=mode):
                    with patch.object(CommandClass, "handle", return_value=None):
                        call_command(command_name, f"--execution_mode={mode}", stdout=io.StringIO())

                    record = TaskSettings.objects.filter(task_name=command_name, execution_mode=mode).first()
                    self.assertIsNotNone(record, f"Missing TaskSettings for {command_name} {mode}")
                    self.assertIsNotNone(record.start_date)
                    self.assertIsNotNone(record.end_date)

                    self.stream.truncate(0)
                    self.stream.seek(0)
