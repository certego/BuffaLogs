import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.utils import timezone
from impossible_travel import tasks
from impossible_travel.constants import AlertDetectionType, IngestionSourceType
from impossible_travel.models import Alert, Login, TaskSettings, User, UsersIP
from impossible_travel.modules.ingestion_handler import ElasticsearchIngestion, Ingestion


def load_test_data(name):
    DATA_PATH = "impossible_travel/tests/test_data"
    with open(os.path.join(DATA_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


class TestTasks(TestCase):
    fixtures = ["tests-fixture"]
    raw_data_NEW_COUNTRY = {
        "id": "orig_id_2",
        "index": "cloud",
        "ip": "5.6.7.8",
        "lat": 54.2414,
        "lon": 77.591,
        "country": "India",
        "agent": "Mozilla/5.0 (Linux; Android 12; moto g stylus 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36v",
        "timestamp": "2025-02-13T09:16:25.000Z",
        "organization": "ISP2",
    }

    def reset_auto_increment(self, model):
        # reset the id number sequence after each tearDown
        table_name = model._meta.db_table  # get the django table name, es. if model=Alert --> table_name=impossible_travel_alert
        with connection.cursor() as cursor:
            # get the sequence name dinamically
            cursor.execute(f"SELECT pg_get_serial_sequence('{table_name}', 'id'); ")  # noqa: E702
            sequence_name = cursor.fetchone()[0]  # Estrai il nome della sequenza

            if sequence_name:
                # reset the id sequence starting from 1
                cursor.execute(f"SELECT setval('{sequence_name}', 1, false); ")  # noqa: E702

    def tearDown(self):
        # delete all alerts after each test, to clean the environment
        Alert.objects.all().delete()
        self.reset_auto_increment(model=Alert)

    def test_clear_models_periodically(self):
        """Testing clear_models_periodically() function"""
        user_obj = User.objects.create(username="Lorena")
        Login.objects.create(user=user_obj, timestamp=timezone.now())
        UsersIP.objects.create(user=user_obj, ip=self.raw_data_NEW_COUNTRY["ip"])
        Alert.objects.create(user=user_obj, name=AlertDetectionType.NEW_COUNTRY.value, login_raw_data=self.raw_data_NEW_COUNTRY)
        self.assertTrue(User.objects.filter(username="Lorena").exists())
        self.assertTrue(Login.objects.filter(user=user_obj).exists())
        self.assertTrue(Alert.objects.filter(user=user_obj).exists())
        self.assertTrue(UsersIP.objects.filter(user=user_obj).exists())
        # Setting an old date to the updated field to check the cleaning
        old_date = timezone.now() + timedelta(days=-100)
        User.objects.filter(username="Lorena").update(updated=old_date)
        Login.objects.filter(user=user_obj).update(updated=old_date)
        Alert.objects.filter(user=user_obj).update(updated=old_date)
        UsersIP.objects.filter(user=user_obj).update(updated=old_date)
        tasks.clean_models_periodically()
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="Lorena")
        with self.assertRaises(Login.DoesNotExist):
            Login.objects.get(user__username="Lorena")
        with self.assertRaises(Alert.DoesNotExist):
            Alert.objects.get(user__username="Lorena")
        with self.assertRaises(UsersIP.DoesNotExist):
            UsersIP.objects.get(user__username="Lorena")

    @patch.object(ElasticsearchIngestion, "process_users")
    def test_process_logs_data_lost(self, mockprocess_users):
        # testing the data lost flow
        process_task = TaskSettings.objects.create(
            task_name="process_logs", start_date=timezone.datetime(2023, 4, 18, 10, 0), end_date=timezone.datetime(2023, 4, 18, 10, 30, 0)
        )
        self.assertEqual("ElasticsearchIngestion", process_task.ingestion_source)
        tasks.process_logs()
        process_task = TaskSettings.objects.get(task_name="process_logs", ingestion_source="ElasticsearchIngestion")
        new_end_date_expected = timezone.now() - timedelta(minutes=1)
        new_start_date_expected = new_end_date_expected - timedelta(minutes=30)
        # data have been lost and start_date and end_date updated to now
        self.assertLessEqual((process_task.start_date - new_start_date_expected).total_seconds(), 5)
        self.assertLessEqual((process_task.end_date - new_end_date_expected).total_seconds(), 5)
        mockprocess_users.assert_called_once()

    @patch("django.utils.timezone.now", return_value=datetime(2025, 2, 19, 12, 0, tzinfo=timezone.utc))
    @patch.object(ElasticsearchIngestion, "process_users")
    def test_process_logs_default(self, mockprocess_users, mock_now):
        # test no execution - break
        tasks.process_logs()
        process_task = TaskSettings.objects.get(ingestion_source="ElasticsearchIngestion")
        self.assertEqual(datetime(2025, 2, 19, 11, 30, tzinfo=timezone.utc), process_task.start_date)
        self.assertEqual(datetime(2025, 2, 19, 11, 59, tzinfo=timezone.utc), process_task.end_date)
        self.assertEqual(mockprocess_users.call_count, 0)

    @patch("django.utils.timezone.now", return_value=datetime(2025, 2, 19, 12, 0, tzinfo=timezone.utc))
    @patch.object(ElasticsearchIngestion, "process_users")
    def test_process_logs_loop(self, mockprocess_users, mock_now):
        # fix the "timezone.now()" to test better the execution
        fixed_now = mock_now.return_value
        # test the loop data execution (6 times)
        start = fixed_now - timedelta(hours=5)
        end = fixed_now - timedelta(hours=4.5) - timedelta(minutes=1)
        process_task = TaskSettings.objects.create(task_name="process_logs", start_date=start, end_date=end)
        # check the initial saved datetimes
        self.assertEqual(datetime(2025, 2, 19, 7, 0, tzinfo=timezone.utc), process_task.start_date)
        self.assertEqual(datetime(2025, 2, 19, 7, 29, tzinfo=timezone.utc), process_task.end_date)
        # Let entire exec for loop
        tasks.process_logs()
        self.assertEqual(mockprocess_users.call_count, 6)
        process_task.refresh_from_db()
        # check the final datetimes after the loop
        self.assertEqual(datetime(2025, 2, 19, 9, 59, tzinfo=timezone.utc), process_task.start_date)
        self.assertEqual(datetime(2025, 2, 19, 10, 29, tzinfo=timezone.utc), process_task.end_date)
        # Now the loop is not executed all the 6 times, just 3 --> total 9 times
        tasks.process_logs()
        process_task.refresh_from_db()
        self.assertEqual(mockprocess_users.call_count, 9)
        # check the final datetimes after the second "partial" loop
        self.assertEqual(datetime(2025, 2, 19, 11, 29, tzinfo=timezone.utc), process_task.start_date)
        self.assertEqual(datetime(2025, 2, 19, 11, 59, tzinfo=timezone.utc), process_task.end_date)
