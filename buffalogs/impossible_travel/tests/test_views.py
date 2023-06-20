import json
from datetime import datetime, timedelta

from django.test import Client
from django.urls import reverse
from impossible_travel.models import Alert, Login, User
from rest_framework.test import APITestCase


class TestViews(APITestCase):
    def setUp(self):
        self.client = Client()
        User.objects.bulk_create(
            [
                User(username="Lorena Goldoni", risk_score=User.riskScoreEnum.NO_RISK),
                User(username="Lorygold", risk_score=User.riskScoreEnum.LOW),
                User(username="Lory", risk_score=User.riskScoreEnum.LOW),
                User(username="Lor", risk_score=User.riskScoreEnum.LOW),
                User(username="Loryg", risk_score=User.riskScoreEnum.MEDIUM),
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
                    name=Alert.ruleNameEnum.NEW_DEVICE,
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
                    name=Alert.ruleNameEnum.IMP_TRAVEL,
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
                    name=Alert.ruleNameEnum.IMP_TRAVEL,
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
                    name=Alert.ruleNameEnum.IMP_TRAVEL,
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
                    name=Alert.ruleNameEnum.NEW_DEVICE,
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
                    name=Alert.ruleNameEnum.NEW_DEVICE,
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
        end = datetime.now()
        start = end - timedelta(hours=5)
        dict_expected_result = {"no_risk": 1, "low": 3, "medium": 1, "high": 0}
        response = self.client.get(reverse("users_pie_chart_api", args=[str(start), str(end)]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_hour(self):
        start = datetime(2023, 6, 20, 10, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = datetime(2023, 6, 20, 12, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
        dict_expected_result = {"Timeframe": "hour", "2023-06-20T10:00:00Z": 1, "2023-06-20T11:00:00Z": 2}
        response = self.client.get(reverse("alerts_line_chart_api", args=[start, end]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_day(self):
        start = datetime(2023, 6, 19, 0, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = datetime(2023, 6, 20, 23, 59, 59).strftime("%Y-%m-%dT%H:%M:%SZ")
        dict_expected_result = {"Timeframe": "day", "2023-6-19": 2, "2023-6-20": 3}
        response = self.client.get(reverse("alerts_line_chart_api", args=[start, end]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_month(self):
        start = datetime(2023, 5, 1, 0, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = datetime(2023, 6, 30, 23, 59, 59).strftime("%Y-%m-%dT%H:%M:%SZ")
        dict_expected_result = {"Timeframe": "month", "2023-5": 1, "2023-6": 5}
        response = self.client.get(reverse("alerts_line_chart_api", args=[start, end]))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))
