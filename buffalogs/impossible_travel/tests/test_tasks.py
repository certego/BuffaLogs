import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from impossible_travel import tasks
from impossible_travel.models import Alert, Config, Login, TaskSettings, User
from impossible_travel.modules import impossible_travel
from impossible_travel.tests.setup import Setup


def load_test_data(name):
    DATA_PATH = "impossible_travel/tests/test_data"
    with open(os.path.join(DATA_PATH, name + ".json")) as file:
        data = json.load(file)
    return data


class TestTasks(TestCase):
    @classmethod
    def setUpTestData(self):
        setup_obj = Setup()
        setup_obj.setup()

    def test_set_alert(self):
        # Add an alert and check if it is correctly inserted in the Alert Model
        db_user = User.objects.get(username="Lorena Goldoni")
        db_login = Login.objects.get(user_agent="Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5")
        timestamp = db_login.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        login_data = {"timestamp": timestamp, "latitude": "45.4758", "longitude": "9.2275", "country": db_login.country, "agent": db_login.user_agent}
        name = Alert.ruleNameEnum.IMP_TRAVEL
        desc = f"{name} for User: {db_user.username},\
                    at: {timestamp}, from:({db_login.latitude}, {db_login.longitude})"
        alert_info = {
            "alert_name": name,
            "alert_desc": desc,
        }
        tasks.set_alert(db_user, login_data, alert_info)
        db_alert = Alert.objects.get(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL)
        self.assertIsNotNone(db_alert)
        self.assertEqual("Impossible Travel detected", db_alert.name)
        self.assertFalse(db_alert.is_vip)

    def test_set_alert_vip_user(self):
        # Test for alert in case of a vip_user
        db_user = User.objects.get(username="Asa Strickland")
        db_login = Login.objects.filter(user=db_user).first()
        timestamp = db_login.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        login_data = {"timestamp": timestamp, "latitude": "45.4758", "longitude": "9.2275", "country": db_login.country, "agent": db_login.user_agent}
        name = Alert.ruleNameEnum.IMP_TRAVEL
        desc = f"{name} for User: {db_user.username},\
                    at: {timestamp}, from:({db_login.latitude}, {db_login.longitude})"
        alert_info = {
            "alert_name": name,
            "alert_desc": desc,
        }
        tasks.set_alert(db_user, login_data, alert_info)
        db_alert = Alert.objects.get(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL)
        self.assertTrue(db_alert.is_vip)

    def test_update_risk_level_norisk(self):
        # 0 alert --> no risk
        tasks.update_risk_level()
        db_user = User.objects.get(username="Lorena Goldoni")
        self.assertEqual("No risk", db_user.risk_score)

    def test_update_risk_level_low(self):
        # 1 alert --> Low risk
        db_user = User.objects.get(username="Lorena Goldoni")
        Alert.objects.create(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL, login_raw_data="Test", description="Test_Description")
        tasks.update_risk_level()
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
        tasks.update_risk_level()
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
        tasks.update_risk_level()
        db_user = User.objects.get(username="Lorena Goldoni")
        self.assertEqual("High", db_user.risk_score)

    # TO DO
    # @patch("impossible_travel.tasks.check_fields")
    # @patch.object(tasks.Search, "execute")
    # def test_process_user(self, mock_execute, mock_chedk_fields):
    #     data_elastic = load_test_data("test_data_elasticsearch")
    #     data_elastic_sorted = sorted(data_elastic, key=lambda d: d["@timestamp"])
    #     data_results = load_test_data("test_data")
    #     mock_execute.return_value = Search.Result.from_dict(data_elastic_sorted)
    #     start_date = timezone.datetime(2023, 3, 8, 0, 0, 0)
    #     end_date = timezone.datetime(2023, 3, 8, 23, 59, 59)
    #     iso_start_date = self.imp_travel.validate_timestamp(start_date)
    #     iso_end_date = self.imp_travel.validate_timestamp(end_date)
    #     db_user = User.objects.get(username="Lorena Goldoni")
    #     tasks.process_user(db_user, iso_start_date, iso_end_date)
    #     mock_chedk_fields.assert_called_once_with(db_user, data_results)

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

    def test_clear_models_periodically_alert_delete(self):
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
        Alert.objects.filter(user__username="Lorena").update(updated=old_date)
        tasks.clear_models_periodically()
        with self.assertRaises(Alert.DoesNotExist):
            Alert.objects.get(user__username="Lorena")
        self.assertTrue(User.objects.filter(username="Lorena").exists())
        self.assertTrue(Login.objects.filter(user__username="Lorena").exists())

    def test_process_logs_data_lost(self):
        TaskSettings.objects.create(
            task_name="process_logs", start_date=timezone.datetime(2023, 4, 18, 10, 0), end_date=timezone.datetime(2023, 4, 18, 10, 30, 0)
        )
        tasks.process_logs()
        new_end_date_expected = (timezone.now() - timedelta(minutes=1)).replace(microsecond=0)
        new_start_date_expected = new_end_date_expected - timedelta(minutes=30)
        process_task = TaskSettings.objects.get(task_name="process_logs")
        self.assertEqual(new_start_date_expected, (process_task.start_date).replace(microsecond=0))
        self.assertEqual(new_end_date_expected, (process_task.end_date).replace(microsecond=0))

    def test_process_logs_loop(self):
        start = (timezone.now() - timedelta(hours=5) - timedelta(minutes=1)).replace(microsecond=0)
        end = (timezone.now() - timedelta(hours=4.5) - timedelta(minutes=1)).replace(microsecond=0)
        TaskSettings.objects.create(task_name="process_logs", start_date=start, end_date=end)
        # Let entire exec for loop
        tasks.process_logs()
        start_date_expected = start + timedelta(hours=3)
        end_date_expected = end + timedelta(hours=3)
        process_task = TaskSettings.objects.get(task_name="process_logs")
        self.assertEqual(process_task.start_date, start_date_expected)
        self.assertEqual(process_task.end_date, end_date_expected)
        # Now not entire for loop executed
        tasks.process_logs()
        start_date_expected = start + timedelta(hours=5)
        end_date_expected = end + timedelta(hours=4.5)

    def test_check_fields(self):
        fields1 = load_test_data("test_check_fields_part1")
        fields2 = load_test_data("test_check_fields_part2")
        db_user = User.objects.get(username="Aisha Delgado")

        # First part - Expected logins in Login Model:
        #   1. at 2023-05-03T06:50:03.768Z from India,
        #   2. at 2023-05-03T06:57:27.768Z from Japan,
        #   3. at 2023-05-03T07:10:23.154Z from United States
        tasks.check_fields(db_user, fields1)
        self.assertEqual(3, Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3").count())
        self.assertEqual(1, Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="India").count())
        self.assertEqual(1, Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="United States").count())
        self.assertEqual(1, Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="Japan").count())
        # First part - Expected alerts in Alert Model:
        #   1. at 2023-05-03T06:55:31.768Z alert NEW DEVICE
        #   2. at 2023-05-03T06:55:31.768Z alert NEW COUNTRY - NO because allowed_country
        #   3. at 2023-05-03T06:55:31.768Z alert IMP TRAVEL
        #   4. at 2023-05-03T06:57:27.768Z alert NEW DEVICE
        #   4. at 2023-05-03T06:57:27.768Z alert NEW COUNTRY
        #   5. at 2023-05-03T06:57:27.768Z alert IMP TRAVEL
        #   6. at 2023-05-03T07:10:23.154Z alert IMP TRAVEL - TO DO, deve scattare !!!!
        self.assertEqual(5, Alert.objects.filter(user=db_user).count())
        self.assertEqual(2, Alert.objects.filter(user=db_user, name=Alert.ruleNameEnum.NEW_DEVICE).count())
        self.assertEqual(1, Alert.objects.filter(user=db_user, name=Alert.ruleNameEnum.NEW_COUNTRY).count())
        self.assertEqual(2, Alert.objects.filter(user=db_user, name=Alert.ruleNameEnum.IMP_TRAVEL).count())
        self.assertEqual(0, Alert.objects.filter(user=db_user, is_vip=True).count())

        # Adding "Aisha Delgado" to vip users
        Config.objects.filter(id=1).delete()
        Config.objects.create(allowed_countries=["Italy"], vip_users=["Aisha Delgado"])

        # Second part - Expected logins in Login Model:
        tasks.check_fields(db_user, fields2)
