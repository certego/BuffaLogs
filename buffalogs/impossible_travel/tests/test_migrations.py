import datetime
import json
import os

from django.core.management import call_command
from django.db import connections
from django.db.utils import OperationalError
from django.forms.models import model_to_dict
from django.test import TestCase
from impossible_travel import constants, models

DATA_PATH = "impossible_travel/tests/test_data"


def load_test_data(name):
    with open(os.path.join(DATA_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


class MigrationTest(TestCase):
    def test_migration_0010_to_0011(self):
        """Testing 0011 migration in order to check that values are correctly set
        for User and Alert models that have had enums changes"""
        call_command("migrate", "impossible_travel", "0010_config_alert_max_days_config_distance_accepted_and_more")

        # upload data fixture
        call_command("loaddata", "impossible_travel/tests/test_data/test_migration_0010_to_0011.json")

        # check initial data state - users
        # used models.UserRiskScoreType because the previous implementation used that enum defined directly in the model
        prev_users = models.User.objects.all().order_by("created")
        self.assertEqual(4, len(prev_users))
        self.assertEqual(prev_users[0].risk_score, models.UserRiskScoreType.NO_RISK)
        self.assertEqual({"username": "user1", "risk_score": "No risk"}, model_to_dict(prev_users[0], fields=["username", "risk_score"]))
        self.assertEqual(prev_users[1].risk_score, models.UserRiskScoreType.LOW)
        self.assertEqual({"username": "user2", "risk_score": "Low"}, model_to_dict(prev_users[1], fields=["username", "risk_score"]))
        self.assertEqual(prev_users[2].risk_score, models.UserRiskScoreType.MEDIUM)
        self.assertEqual({"username": "user3", "risk_score": "Medium"}, model_to_dict(prev_users[2], fields=["username", "risk_score"]))
        self.assertEqual(prev_users[3].risk_score, models.UserRiskScoreType.HIGH)
        self.assertEqual({"username": "user4", "risk_score": "High"}, model_to_dict(prev_users[3], fields=["username", "risk_score"]))

        # check initial data state - logins (no changes affected)
        prev_logins = models.Login.objects.all().order_by("timestamp")
        self.check_logins_no_changes(logins=prev_logins)

        # check initial data state - alerts
        prev_alerts = models.Alert.objects.all()
        self.assertEqual(3, len(prev_alerts))
        self.assertEqual(prev_alerts[0].user, prev_users[0])
        self.assertEqual(prev_alerts[0].name, models.AlertDetectionType.NEW_DEVICE)
        self.assertEqual(prev_alerts[0].name, "Login from new device")
        self.assertEqual(prev_alerts[1].user, prev_users[0])
        self.assertEqual(prev_alerts[1].name, models.AlertDetectionType.NEW_COUNTRY)
        self.assertEqual(prev_alerts[1].name, "Login from new country")
        self.assertEqual(prev_alerts[2].user, prev_users[0])
        self.assertEqual(prev_alerts[2].name, models.AlertDetectionType.IMP_TRAVEL)
        self.assertEqual(prev_alerts[2].name, "Impossible Travel detected")

        # Exec the new migration 0011
        call_command("migrate", "impossible_travel", "0011_alert_filter_type_alert_is_filtered_and_more")

        # Update objects from dB
        new_users = prev_users.refresh_from_db()
        new_alerts = prev_alerts.refresh_from_db()
        new_logins = prev_logins.refresh_from_db()

        # check post data state - users
        self.assertEqual(4, len(new_users))
        self.assertEqual(new_users[0].risk_score, constants.UserRiskScoreType.NO_RISK)
        self.assertEqual({"username": "user1", "risk_score": "No risk"}, model_to_dict(new_users[0], fields=["username", "risk_score"]))
        self.assertEqual(new_users[1].risk_score, constants.UserRiskScoreType.LOW)
        self.assertEqual({"username": "user2", "risk_score": "Low"}, model_to_dict(new_users[1], fields=["username", "risk_score"]))
        self.assertEqual(new_users[2].risk_score, constants.UserRiskScoreType.MEDIUM)
        self.assertEqual({"username": "user3", "risk_score": "Medium"}, model_to_dict(new_users[2], fields=["username", "risk_score"]))
        self.assertEqual(new_users[3].risk_score, constants.UserRiskScoreType.HIGH)
        self.assertEqual({"username": "user4", "risk_score": "High"}, model_to_dict(new_users[3], fields=["username", "risk_score"]))

        # check post data state - logins (no changes affected)
        self.check_logins_no_changes(logins=new_logins)

        # check post data state - alerts
        self.assertEqual(3, len(new_alerts))
        self.assertEqual(new_alerts[0].user, new_users[0])
        self.assertEqual(new_alerts[0].name, constants.AlertDetectionType.NEW_DEVICE)
        self.assertEqual(prev_alerts[0].name, "New Device")
        self.assertEqual(new_alerts[1].user, new_users[0])
        self.assertEqual(new_alerts[1].name, constants.AlertDetectionType.NEW_COUNTRY)
        self.assertEqual(prev_alerts[1].name, "New Country")
        self.assertEqual(new_alerts[2].user, new_users[0])
        self.assertEqual(new_alerts[2].name, constants.AlertDetectionType.IMP_TRAVEL)
        self.assertEqual(prev_alerts[2].name, "Imp Travel")

    def check_logins_no_changes(self, logins: dict):
        self.assertEqual(3, len(logins))
        self.assertEqual(logins[0].user, logins[0])
        login_timestamp = datetime.datetime(2024, 12, 20, 16, 45, 0, 904000, tzinfo=datetime.timezone.utc)
        self.assertEqual(logins[0].timestamp, login_timestamp)
        self.assertEqual(
            {
                "latitude": 26.8871,
                "longitude": 75.8033,
                "country": "India",
                "user_agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0)",
                "index": "cloud",
                "event_id": "M1ZosYkBqcYN0otHYDeF",
                "ip": "1.2.3.4",
            },
            model_to_dict(logins[0], fields=["latitude", "longitude", "country", "user_agent", "index", "event_id", "ip"]),
        )
        self.assertEqual(logins[1].user, logins[0])
        login_timestamp = datetime.datetime(2024, 12, 20, 16, 45, 1, 904000, tzinfo=datetime.timezone.utc)
        self.assertEqual(logins[1].timestamp, login_timestamp)
        self.assertEqual(
            {
                "latitude": 27.0519,
                "longitude": 79.7899,
                "country": "Italy",
                "user_agent": "Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
                "index": "fw-proxy",
                "event_id": "H1ZosYkBqcYN0otHYDiG",
                "ip": "5.6.7.8",
            },
            model_to_dict(logins[1], fields=["latitude", "longitude", "country", "user_agent", "index", "event_id", "ip"]),
        )
        self.assertEqual(logins[2].user, logins[1])
        login_timestamp = datetime.datetime(2024, 12, 20, 16, 45, 2, 904000, tzinfo=datetime.timezone.utc)
        self.assertEqual(logins[2].timestamp, login_timestamp)
        self.assertEqual(
            {
                "latitude": 37.7468,
                "longitude": -84.3014,
                "country": "United States",
                "user_agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)",
                "index": "cloud",
                "event_id": "RlZosYkBqcYN0otHYDiG",
                "ip": "7.8.9.1",
            },
            model_to_dict(logins[2], fields=["latitude", "longitude", "country", "user_agent", "index", "event_id", "ip"]),
        )

    def tearDown(self):
        """Pulisci il database dopo il test."""
        models.User.objects.all().delete()
