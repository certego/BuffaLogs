import json
from datetime import datetime, timedelta

from django.test import Client
from django.urls import reverse
from impossible_travel.constants import AlertDetectionType, UserRiskScoreType
from impossible_travel.models import Alert, Login, User
from rest_framework.test import APITestCase


class TestViews(APITestCase):
    def setUp(self):
        self.client = Client()
        User.objects.bulk_create(
            [
                User(username="Lorena Goldoni", risk_score=UserRiskScoreType.NO_RISK),
                User(username="Lorygold", risk_score=UserRiskScoreType.LOW),
                User(username="Lory", risk_score=UserRiskScoreType.LOW),
                User(username="Lor", risk_score=UserRiskScoreType.LOW),
                User(username="Loryg", risk_score=UserRiskScoreType.MEDIUM),
            ]
        )
        db_user = User.objects.get(username="Lorena Goldoni")
        Login.objects.bulk_create(
            [
                Login(
                    user=db_user,
                    event_id="vfraw14gw",
                    index="cloud",
                    ip="1.2.3.4",
                    timestamp="2023-06-19T10:01:33.358Z",
                    latitude=40.364,
                    longitude=-79.8605,
                    country="United States",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                ),
                Login(
                    user=db_user,
                    event_id="ht9DEIgBnkLiMp6r-SG-",
                    index="weblog",
                    ip="203.0.113.24",
                    timestamp="2023-06-19T10:08:33.358Z",
                    latitude=36.2462,
                    longitude=138.8497,
                    country="Japan",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
                ),
                Login(
                    user=db_user,
                    event_id="vfraw14gw",
                    index="cloud",
                    ip="1.2.3.4",
                    timestamp="2023-06-20T10:01:33.358Z",
                    latitude=40.364,
                    longitude=-79.8605,
                    country="United States",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                ),
                Login(
                    user=db_user,
                    event_id="ht9DEIgBnkLiMp6r-SG-",
                    index="weblog",
                    ip="203.0.113.24",
                    timestamp="2023-06-20T10:08:33.358Z",
                    latitude=36.2462,
                    longitude=138.8497,
                    country="Japan",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
                ),
            ]
        )
        Alert.objects.bulk_create(
            [
                Alert(
                    user=db_user,
                    name=AlertDetectionType.NEW_DEVICE,
                    login_raw_data={
                        "id": "ht9DEIgBnkLiMp6r-SG-",
                        "ip": "203.0.113.24",
                        "lat": 36.2462,
                        "lon": 138.8497,
                        "agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
                        "index": "weblog",
                        "country": "Japan",
                        "timestamp": "2023-05-20T11:45:01.229Z",
                    },
                    description="Test_Description0",
                ),
                Alert(
                    user=db_user,
                    name=AlertDetectionType.IMP_TRAVEL,
                    login_raw_data={
                        "id": "vfraw14gw",
                        "ip": "1.2.3.4",
                        "lat": 40.364,
                        "lon": -79.8605,
                        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                        "index": "cloud",
                        "country": "United States",
                        "timestamp": "2023-06-19T17:17:31.358Z",
                    },
                    description="Test_Description1",
                ),
                Alert(
                    user=db_user,
                    name=AlertDetectionType.IMP_TRAVEL,
                    login_raw_data={
                        "id": "vfraw14gw",
                        "ip": "1.2.3.4",
                        "lat": 40.364,
                        "lon": -79.8605,
                        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                        "index": "cloud",
                        "country": "United States",
                        "timestamp": "2023-06-19T18:15:33.548Z",
                    },
                    description="Test_Descriptio2",
                ),
                Alert(
                    user=db_user,
                    name=AlertDetectionType.IMP_TRAVEL,
                    login_raw_data={
                        "id": "vfraw14gw",
                        "ip": "1.2.3.4",
                        "lat": 40.364,
                        "lon": -79.8605,
                        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                        "index": "cloud",
                        "country": "United States",
                        "timestamp": "2023-06-20T10:17:33.358Z",
                    },
                    description="Test_Description3",
                ),
                Alert(
                    user=db_user,
                    name=AlertDetectionType.NEW_DEVICE,
                    login_raw_data={
                        "id": "ht9DEIgBnkLiMp6r-SG-",
                        "ip": "203.0.113.24",
                        "lat": 36.2462,
                        "lon": 138.8497,
                        "agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
                        "index": "weblog",
                        "country": "Japan",
                        "timestamp": "2023-06-20T11:31:10.149Z",
                    },
                    description="Test_Description4",
                ),
                Alert(
                    user=db_user,
                    name=AlertDetectionType.NEW_DEVICE,
                    login_raw_data={
                        "id": "ht9DEIgBnkLiMp6r-SG-",
                        "ip": "203.0.113.24",
                        "lat": 36.2462,
                        "lon": 138.8497,
                        "agent": "Mozilla/5.0 (X11; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
                        "index": "weblog",
                        "country": "Japan",
                        "timestamp": "2023-06-20T11:45:01.229Z",
                    },
                    description="Test_Description5",
                ),
            ]
        )

    def test_users_pie_chart_api(self):
        end = datetime.now() + timedelta(minutes=1)
        start = end - timedelta(hours=3)
        dict_expected_result = {"no_risk": 1, "low": 3, "medium": 1, "high": 0}
        response = self.client.get(f"{reverse('users_pie_chart_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_hour(self):
        start = datetime(2023, 6, 20, 10, 0)
        end = datetime(2023, 6, 20, 12, 0)
        dict_expected_result = {"Timeframe": "hour", "2023-06-20T10:00:00Z": 1, "2023-06-20T11:00:00Z": 2}
        response = self.client.get(f"{reverse('alerts_line_chart_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_day(self):
        start = datetime(2023, 6, 19, 0, 0)
        end = datetime(2023, 6, 20, 23, 59, 59)
        dict_expected_result = {"Timeframe": "day", "2023-6-19": 2, "2023-6-20": 3}
        response = self.client.get(f"{reverse('alerts_line_chart_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_month(self):
        start = datetime(2023, 5, 1, 0, 0)
        end = datetime(2023, 6, 30, 23, 59, 59)
        dict_expected_result = {"Timeframe": "month", "2023-5": 1, "2023-6": 5}
        response = self.client.get(f"{reverse('alerts_line_chart_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_world_map_chart_api(self):
        start = datetime(2023, 5, 1, 0, 0)
        end = datetime(2023, 6, 30, 23, 59, 59)
        num_alerts = 0
        list_expected_result = [{"country": "jp", "lat": 36.2462, "lon": 138.8497, "alerts": 3}, {"country": "us", "lat": 40.364, "lon": -79.8605, "alerts": 3}]
        response = self.client.get(f"{reverse('world_map_chart_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        for elem in list_expected_result:
            num_alerts += elem["alerts"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_alerts, Alert.objects.all().count())
        self.assertListEqual(list_expected_result, json.loads(response.content))

    def test_alerts_api(self):
        creation_mock_time = datetime(2023, 7, 25, 12, 0)
        alert = Alert.objects.get(login_raw_data__timestamp="2023-05-20T11:45:01.229Z")
        alert.created = creation_mock_time
        alert.save()
        alert = Alert.objects.get(login_raw_data__timestamp="2023-06-20T10:17:33.358Z")
        alert.created = creation_mock_time + timedelta(minutes=5)
        alert.save()
        start = creation_mock_time
        end = creation_mock_time + timedelta(minutes=10)
        list_expected_result = [
            {"timestamp": "2023-06-20T10:17:33.358Z", "username": "Lorena Goldoni", "rule_name": "Imp Travel"},
            {"timestamp": "2023-05-20T11:45:01.229Z", "username": "Lorena Goldoni", "rule_name": "New Device"},
        ]
        response = self.client.get(f"{reverse('alerts_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(list_expected_result, json.loads(response.content))

    def test_risk_score_api(self):
        end = datetime.now() + timedelta(seconds=1)
        start = end - timedelta(minutes=1)
        dict_expected_result = {"Lorena Goldoni": "No risk", "Lorygold": "Low", "Lory": "Low", "Lor": "Low", "Loryg": "Medium"}
        response = self.client.get(f"{reverse('risk_score_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))
