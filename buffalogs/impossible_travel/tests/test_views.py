import json
from datetime import datetime, timedelta, timezone

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
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
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
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
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
                        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
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
                        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
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
                        "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
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
        dict_expected_result = {"Timeframe": "day", "2023-06-19": 2, "2023-06-20": 3}
        response = self.client.get(f"{reverse('alerts_line_chart_api')}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(dict_expected_result, json.loads(response.content))

    def test_alerts_line_chart_api_month(self):
        start = datetime(2023, 5, 1, 0, 0)
        end = datetime(2023, 6, 30, 23, 59, 59)
        dict_expected_result = {"Timeframe": "month", "2023-05": 1, "2023-06": 5}
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

    def test_user_login_timeline_api(self):
        """Test the user login timeline API endpoint."""

        db_user = User.objects.get(username="Lorena Goldoni")

        mock_login_date = datetime(2025, 4, 27, 23, 8, 10, 800340, tzinfo=timezone.utc)

        login_timestamps = [
            mock_login_date,
            mock_login_date - timedelta(hours=23),  # previous day
            mock_login_date - timedelta(days=1, hours=18),  # 2 days ago
            mock_login_date - timedelta(days=2, hours=20),  # 3 days ago
        ]

        logins = []
        for timestamp in login_timestamps:
            logins.append(
                Login(
                    user=db_user,
                    event_id=f"login_{timestamp.isoformat()}",
                    index="cloud",
                    ip="192.168.1.1",
                    timestamp=timestamp,
                    latitude=37.7749,
                    longitude=-122.4194,
                    country="United States",
                    user_agent="Firefox",
                )
            )
        Login.objects.bulk_create(logins)

        start = mock_login_date - timedelta(days=3)
        end = mock_login_date + timedelta(minutes=1)

        response = self.client.get(
            f"{reverse('login_timeline_api', args=[db_user.pk])}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("logins", data)
        self.assertEqual(len(data["logins"]), len(login_timestamps))

        response_timestamps = data["logins"]
        for i, timestamp in enumerate(login_timestamps):
            self.assertTrue(
                any(timestamp.isoformat() in resp_time for resp_time in response_timestamps), f"Timestamp {timestamp.isoformat()} not found in response"
            )

    def test_user_device_usage_api(self):
        """Test the user device usage API endpoint."""

        db_user = User.objects.get(username="Lorena Goldoni")

        devices = {
            "Firefox": 3,
            "Chrome": 2,
            "Safari": 1,
            "Edge": 2,
        }

        base_timestamp = datetime(2025, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
        logins = []

        for device, count in devices.items():
            for i in range(count):
                logins.append(
                    Login(
                        user=db_user,
                        event_id=f"device_test_{device}_{i}",
                        index="cloud",
                        ip="192.168.1.1",
                        timestamp=base_timestamp + timedelta(hours=i),
                        latitude=37.7749,
                        longitude=-122.4194,
                        country="United States",
                        user_agent=device,
                    )
                )

        Login.objects.bulk_create(logins)

        start = base_timestamp - timedelta(days=1)
        end = base_timestamp + timedelta(days=1)

        response = self.client.get(
            f"{reverse('device_usage_api', args=[db_user.pk])}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("devices", data)

        for device, count in devices.items():
            self.assertIn(device, data["devices"])
            self.assertGreaterEqual(data["devices"][device], count)

    def test_user_login_frequency_api(self):
        """Test the user login frequency API endpoint."""

        db_user = User.objects.get(username="Lorena Goldoni")

        base_date = datetime(2023, 6, 19, 10, 0, 0, tzinfo=timezone.utc)
        daily_counts = {
            0: 3,  # day 0 (base date)
            1: 2,  # day 1
            3: 4,  # day 3
        }

        logins = []
        for day_offset, count in daily_counts.items():
            for i in range(count):
                logins.append(
                    Login(
                        user=db_user,
                        event_id=f"freq_test_day{day_offset}_{i}",
                        index="cloud",
                        ip="192.168.1.1",
                        timestamp=base_date + timedelta(days=day_offset, hours=i),
                        latitude=37.7749,
                        longitude=-122.4194,
                        country="United States",
                        user_agent="Test Browser",
                    )
                )

        Login.objects.bulk_create(logins)

        start = base_date
        end = base_date + timedelta(days=4)

        response = self.client.get(
            f"{reverse('login_frequency_api', args=[db_user.pk])}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("daily_logins", data)

        login_counts = {datetime.fromisoformat(entry["date"]).date(): entry["count"] for entry in data["daily_logins"]}
        print(login_counts)
        base_date_key = base_date.date()
        next_day_key = (base_date + timedelta(days=1)).date()
        expected_counts = {
            base_date.date(): daily_counts.get(0, 0) + 2,  # 2 existing logins on base date
            (base_date + timedelta(days=1)).date(): daily_counts.get(1, 0) + 2,  # 2 existing logins on next day
            (base_date + timedelta(days=2)).date(): daily_counts.get(2, 0),
            (base_date + timedelta(days=3)).date(): daily_counts.get(3, 0),
            (base_date + timedelta(days=4)).date(): daily_counts.get(4, 0),
        }

        for date, expected_count in expected_counts.items():
            date_str = date.isoformat()
            found = False
            for entry in data["daily_logins"]:
                if entry["date"] == date_str:
                    self.assertEqual(entry["count"], expected_count, f"Count mismatch for date {date_str}")
                    found = True
                    break
            self.assertTrue(found, f"Date {date_str} not found in response")

    def test_user_time_of_day_api(self):
        """Test the user time of day API endpoint."""
        db_user = User.objects.get(username="Lorena Goldoni")
        base_date = datetime(2023, 6, 19, 0, 0, 0, tzinfo=timezone.utc)  # Monday (weekday 0)

        hour_weekday_pattern = {
            5: [0, 1, 1, 0, 0, 1, 0],  # Hour 5: Monday, Tuesday, Tuesday, Friday
            12: [0, 0, 0, 0, 0, 0, 1],  # Hour 12: Sunday
            15: [0, 1, 0, 0, 1, 0, 0],  # Hour 15: Tuesday, Friday
            22: [1, 0, 0, 0, 0, 1, 0],  # Hour 22: Monday, Saturday
        }

        logins = []
        for hour, weekdays in hour_weekday_pattern.items():
            for weekday, count in enumerate(weekdays):
                for i in range(count):
                    # calculating the date for this weekday
                    date = base_date + timedelta(days=weekday)
                    timestamp = date.replace(hour=hour)

                    logins.append(
                        Login(
                            user=db_user,
                            event_id=f"tod_test_h{hour}_d{weekday}_{i}",
                            index="cloud",
                            ip="192.168.1.1",
                            timestamp=timestamp,
                            latitude=37.7749,
                            longitude=-122.4194,
                            country="United States",
                            user_agent="Test Browser",
                        )
                    )

        Login.objects.bulk_create(logins)

        start = base_date
        end = base_date + timedelta(days=7)

        response = self.client.get(
            f"{reverse('time_of_day_api', args=[db_user.pk])}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("hourly_logins", data)

        hourly_data = {entry["hour"]: entry["weekdays"] for entry in data["hourly_logins"]}

        for hour, expected_weekdays in hour_weekday_pattern.items():
            self.assertIn(hour, hourly_data)
            for weekday, expected_count in enumerate(expected_weekdays):
                self.assertGreaterEqual(
                    hourly_data[hour][weekday], expected_count, f"Expected at least {expected_count} logins for hour {hour}, weekday {weekday}"
                )

    def test_user_geo_distribution_api(self):
        """Test the user geo distribution API endpoint."""
        db_user = User.objects.get(username="Lorena Goldoni")

        countries = {
            "United States": {"code": "us", "lat": 37.7749, "lon": -122.4194, "count": 3},
            "Germany": {"code": "de", "lat": 52.5200, "lon": 13.4050, "count": 2},
            "India": {"code": "in", "lat": 20.5937, "lon": 78.9629, "count": 4},
            "Canada": {"code": "ca", "lat": 56.1304, "lon": -106.3468, "count": 1},
        }

        base_timestamp = datetime(2023, 6, 19, 12, 0, 0, tzinfo=timezone.utc)
        logins = []

        offset = 0
        for country, details in countries.items():
            for i in range(details["count"]):
                logins.append(
                    Login(
                        user=db_user,
                        event_id=f"geo_test_{country}_{i}",
                        index="cloud",
                        ip=f"192.168.{offset}.{i + 1}",
                        timestamp=base_timestamp + timedelta(hours=offset + i),
                        latitude=details["lat"],
                        longitude=details["lon"],
                        country=country,
                        user_agent="Test Browser",
                    )
                )
            offset += details["count"]

        Login.objects.bulk_create(logins)

        start = base_timestamp - timedelta(hours=1)
        end = base_timestamp + timedelta(days=1)

        response = self.client.get(
            f"{reverse('geo_distribution_api', args=[db_user.pk])}?start={start.strftime('%Y-%m-%dT%H:%M:%SZ')}&end={end.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("countries", data)

        for country, details in countries.items():
            country_code = details["code"]
            expected_count = details["count"]
            if country_code in data["countries"]:
                self.assertGreaterEqual(data["countries"][country_code], expected_count, f"Expected at least {expected_count} logins for country {country}")
