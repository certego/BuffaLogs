from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.db import connection
from django.test import TestCase
from django.utils import timezone
from impossible_travel import tasks
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert, Login, User, UsersIP


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

    def _scheduled_alert_summary_setup(self):
        """Setup for ScheduledAlertSummaryTask tests"""
        now = timezone.now()
        start_date = now - timedelta(days=1)
        start_week = now - timedelta(weeks=1)

        self.user1 = User.objects.create(username="User1")
        self.user2 = User.objects.create(username="User2")
        self.user3 = User.objects.create(username="User3")

        alert1 = Alert.objects.create(
            user=self.user1,
            name="Imp Travel",
            login_raw_data={},
        )
        alert2 = Alert.objects.create(
            user=self.user1,
            name="New Country",
            login_raw_data={},
        )
        alert3 = Alert.objects.create(
            user=self.user2,
            name="Imp Travel",
            login_raw_data={},
        )
        alert4 = Alert.objects.create(
            user=self.user3,
            name="New Country",
            login_raw_data={},
        )

        # Configure the creation dates
        Alert.objects.filter(id=alert1.id).update(created=start_date + timedelta(hours=1))
        Alert.objects.filter(id=alert2.id).update(created=start_date + timedelta(hours=2))
        Alert.objects.filter(id=alert3.id).update(created=start_week + timedelta(days=2))
        Alert.objects.filter(id=alert4.id).update(created=start_week + timedelta(days=5))
        alert1.refresh_from_db()
        alert2.refresh_from_db()
        alert3.refresh_from_db()
        alert4.refresh_from_db()

    @patch("requests.post")
    def test_scheduled_alert_summary_daily(self, mock_post):
        """Test ScheduledAlertSummaryTask for 'daily'"""
        self._scheduled_alert_summary_setup()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Returns 2 alerts
        tasks.scheduled_alert_summary("daily")

        args, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        attachment = payload["attachments"][0]

        self.assertIn("BuffaLogs - Scheduled Alert Summary", attachment["title"])
        self.assertIn("Total Alerts: 2", attachment["text"])

    @patch("requests.post")
    def test_scheduled_alert_summary_weekly(self, mock_post):
        """Test ScheduledAlertSummaryTask for 'weekly'"""
        self._scheduled_alert_summary_setup()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Returns 4 alerts
        tasks.scheduled_alert_summary("weekly")

        args, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        attachment = payload["attachments"][0]

        self.assertIn("BuffaLogs - Scheduled Alert Summary", attachment["title"])
        self.assertIn("Total Alerts: 4", attachment["text"])

    @patch("requests.post")
    def test_scheduled_alert_summary_no_alert(self, mock_post):
        """Test ScheduledAlertSummaryTask when no alerts are there"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        tasks.scheduled_alert_summary()

        args, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        attachment = payload["attachments"][0]

        self.assertIn("BuffaLogs - Scheduled Alert Summary", attachment["title"])
        self.assertIn("No alerts were generated during this period", attachment["text"])

    def test_scheduled_alert_summary_invalid_frequency(self):
        """Test ScheduledAlertSummaryTask for an invalid frequency"""
        with self.assertRaises(ValueError) as context:
            tasks.scheduled_alert_summary("monthly")

        self.assertEqual(str(context.exception), "Invalid frequency. Use 'daily' or 'weekly'")
