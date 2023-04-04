import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from impossible_travel import tasks
from impossible_travel.models import Alert, Login, User
from impossible_travel.modules import impossible_travel


def load_test_data(name):
    DATA_PATH = "impossible_travel/tests/test_data"
    with open(os.path.join(DATA_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


class TestTasks(TestCase):

    imp_travel = impossible_travel.Impossible_Travel()

    @classmethod
    def setUpTestData(self):
        user = User.objects.create(
            username="Lorena Goldoni",
        )
        user.save()
        logins = Login.objects.bulk_create(
            [
                Login(
                    user=user,
                    timestamp="2023-03-08T17:08:33.358Z",
                    latitude=44.4937,
                    longitude=24.3456,
                    country="Italy",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                ),
                Login(
                    user=user,
                    timestamp="2023-03-08T17:25:33.358Z",
                    latitude=45.4758,
                    longitude=9.2275,
                    country="Italy",
                    user_agent="Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5",
                ),
            ]
        )

    def test_set_alert(self):
        # Add an alert and check if it is correctly inserted in the Alert DB
        db_user = User.objects.get(username="Lorena Goldoni")
        login = Login.objects.get(user_agent="Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5")
        timestamp = login.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        login_data = {"timestamp": timestamp, "latitude": "45.4758", "longitude": "9.2275", "country": login.country, "agent": login.user_agent}
        name = Alert.ruleNameEnum.IMP_TRAVEL
        desc = f"{name} for User: {db_user.username},\
                    at: {timestamp}, from:({login.latitude}, {login.longitude})"
        alert_info = {
            "alert_name": name,
            "alert_desc": desc,
        }
        tasks.set_alert(db_user, login_data, alert_info)
        db_alert = Alert.objects.get(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL)
        self.assertIsNotNone(db_alert)

    def test_update_risk_level_norisk(self):
        # 0 alert --> no risk
        db_user = User.objects.get(username="Lorena Goldoni")
        tasks.update_risk_level(db_user)
        self.assertEqual("No risk", db_user.risk_score)

    def test_update_risk_level_low(self):
        # 1 alert --> Low risk
        db_user = User.objects.get(username="Lorena Goldoni")
        Alert.objects.create(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL, login_raw_data="Test", description="Test_Description")
        tasks.update_risk_level(db_user)
        db_user = User.objects.get(username="Lorena Goldoni")
        self.assertEqual("Low", db_user.risk_score)

    def test_update_risk_level_medium(self):
        #   3 alerts --> Medium risk
        db_user = User.objects.get(username="Lorena Goldoni")
        alerts = Alert.objects.bulk_create(
            [
                Alert(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL, login_raw_data="Test1", description="Test_Description1"),
                Alert(user=db_user, name=Alert.ruleNameEnum.NEW_DEVICE, login_raw_data="Test2", description="Test_Description2"),
                Alert(user=db_user, name=Alert.ruleNameEnum.NEW_COUNTRY, login_raw_data="Test3", description="Test_Description3"),
            ]
        )
        tasks.update_risk_level(db_user)
        db_user = User.objects.get(username="Lorena Goldoni")
        self.assertEqual("Medium", db_user.risk_score)

    def test_update_risk_level_high(self):
        #   5 alerts --> High risk
        db_user = User.objects.get(username="Lorena Goldoni")
        alerts = Alert.objects.bulk_create(
            [
                Alert(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL, login_raw_data="Test1", description="Test_Description1"),
                Alert(user=db_user, name=Alert.ruleNameEnum.NEW_DEVICE, login_raw_data="Test2", description="Test_Description2"),
                Alert(user=db_user, name=Alert.ruleNameEnum.NEW_COUNTRY, login_raw_data="Test3", description="Test_Description3"),
                Alert(user=db_user, name=Alert.ruleNameEnum.NEW_COUNTRY, login_raw_data="Test4", description="Test_Description4"),
                Alert(user=db_user, name=Alert.ruleNameEnum.NEW_COUNTRY, login_raw_data="Test5", description="Test_Description5"),
            ]
        )
        tasks.update_risk_level(db_user)
        db_user = User.objects.get(username="Lorena Goldoni")
        self.assertEqual("High", db_user.risk_score)

    @patch("impossible_travel.tasks.check_fields")
    @patch.object(tasks.Search, "execute")
    def test_process_user(self, mock_execute, mock_chedk_fields):
        data_elastic = load_test_data("test_data_elasticsearch")
        data_elastic_sorted = sorted(data_elastic, key=lambda d: d["@timestamp"])
        data_results = load_test_data("test_data")
        mock_execute.return_value = data_elastic_sorted
        start_date = timezone.datetime(2023, 3, 8, 0, 0, 0)
        end_date = timezone.datetime(2023, 3, 8, 23, 59, 59)
        iso_start_date = self.imp_travel.validate_timestamp(start_date)
        iso_end_date = self.imp_travel.validate_timestamp(end_date)
        db_user = User.objects.get(username="Lorena Goldoni")
        tasks.process_user(db_user, iso_start_date, iso_end_date)
        mock_chedk_fields.assert_called_once_with(db_user, data_results)

    def test_clear_models_periodically(self):
        user_obj = User.objects.create(username="Lorena")
        Login.objects.create(user=user_obj, timestamp=timezone.now())
        raw_data = {
            "lat": 40.6079,
            "lon": -74.4037,
            "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
            "country": "United States",
            "timestamp": "2023-04-03T14:01:47.907Z",
        }
        Alert.objects.create(user=user_obj, login_raw_data=raw_data)
        old_date = timezone.now() + timedelta(days=-100)
        User.objects.filter(username="Lorena").update(updated=old_date)
        Login.objects.filter(user__username="Lorena").update(updated=old_date)
        Alert.objects.filter(user__username="Lorena").update(updated=old_date)
        tasks.clear_models_periodically()
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="Lorena")
        with self.assertRaises(Login.DoesNotExist):
            Login.objects.get(user__username="Lorena")
        with self.assertRaises(Alert.DoesNotExist):
            Alert.objects.get(user__username="Lorena")
