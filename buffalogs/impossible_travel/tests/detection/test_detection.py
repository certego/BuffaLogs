import datetime
from unittest.mock import patch

from django.core.management import call_command
from django.db.models import Count, Q
from django.test import TestCase
from django.utils import timezone
from impossible_travel.constants import AlertDetectionType, AlertFilterType
from impossible_travel.models import Alert, Config, Login, User, UsersIP
from impossible_travel.modules import detection
from impossible_travel.tests.utils import load_test_data


class DetectionTestCase(TestCase):

    # dicts for alert.login_raw_data field
    raw_data_NEW_DEVICE = {
        "id": "orig_id_1",
        "index": "cloud",
        "ip": "1.2.3.4",
        "lat": 40.6079,
        "lon": -74.4037,
        "country": "United States",
        "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "timestamp": "2025-02-13T08:29:17.560Z",
        "organization": "ISP1",
    }
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
    raw_data_IMP_TRAVEL = {
        "id": "orig_id_3",
        "index": "cloud",
        "ip": "9.10.11.12",
        "lat": 43.3178,
        "lon": -5.4125,
        "country": "Italy",
        "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
        "buffalogs": {
            "avg_speed": 810,
            "start_lat": 45.748,
            "start_lon": 4.85,
            "start_country": "France",
        },
        "timestamp": "2025-02-13T09:06:11.000Z",
        "organization": "ISP3",
    }

    def setUp(self):
        # executed once per test (at the beginning)
        call_command("loaddata", "tests-fixture.json", verbosity=0)

    def tearDown(self):
        # executed once per test (at the end)
        User.objects.all().delete()

    def test_calc_distance_impossible_travel(self):
        # if distance >  Config.distance_accepted --> FALSE
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "40.364",
            "lon": "-79.8605",
            "country": "United States",
        }
        db_user = User.objects.get(username="Lorena Goldoni")
        prev_login = Login.objects.create(
            user=db_user,
            event_id="event_1",
            index="cloud",
            ip="1.2.3.4",
            timestamp=datetime.datetime(2023, 3, 8, 17, 8, 33, 358000, tzinfo=datetime.timezone.utc),
            latitude=40.364,
            longitude=-79.8605,
            country="United States",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
        )
        result, vel = detection.calc_distance_impossible_travel(db_user, prev_login, last_login_user_fields)
        self.assertEqual({}, result)
        self.assertEqual(0, vel)
        prev_login.delete()

    def test_calc_distance_impossible_travel_alert(self):
        # Test to check if the IMP_TRAVEL alert has been triggered
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:08:33.358Z",
            "lat": "15.9876",
            "lon": "25.3456",
            "country": "Sudan",
        }
        db_user = User.objects.get(username="Lorena Goldoni")
        prev_login = Login.objects.create(
            user=db_user,
            event_id="event_1",
            index="cloud",
            ip="1.2.3.4",
            timestamp=datetime.datetime(2023, 3, 8, 17, 8, 33, 358000, tzinfo=datetime.timezone.utc),
            latitude=40.364,
            longitude=-79.8605,
            country="United States",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
        )
        result, vel = detection.calc_distance_impossible_travel(db_user, prev_login, last_login_user_fields)
        self.assertEqual("Imp Travel", result["alert_name"])
        self.assertEqual(
            f"Impossible Travel detected for User: Lorena Goldoni, at: 2023-03-08T17:08:33.358Z, from: Sudan, previous country: United States, distance covered at {vel} Km/h",  # noqa: E231
            result["alert_desc"],
        )
        prev_login.delete()

    def test_update_model(self):
        # Test update_model() function for unique login, so if a login has the same [user_agent, country and index], the other fields shuld be updated to the new fields values
        user_obj = User.objects.get(username="Lorena Goldoni")
        old_login = Login.objects.get(user=user_obj, event_id="event_id_2")
        new_time = timezone.now()
        new_login_fields = {
            "id": "test2",
            "index": "cloud",
            "ip": "1.2.3.4",
            "lat": 39.1841,
            "lon": -77.0242,
            "country": "Italy",
            "agent": "Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5",
            "timestamp": new_time,
        }
        detection.update_model(user_obj, new_login_fields)
        new_login_db = Login.objects.get(user=user_obj, event_id="test2")
        # Index, country and user_agent fields must not change
        self.assertEqual(new_login_db.index, old_login.index)
        self.assertEqual(new_login_db.country, old_login.country)
        self.assertEqual(new_login_db.user_agent, old_login.user_agent)
        # Check if the other fields are changed
        self.assertEqual(new_login_db.event_id, new_login_fields["id"])
        self.assertEqual(new_login_db.ip, new_login_fields["ip"])
        self.assertEqual(new_login_db.latitude, new_login_fields["lat"])
        self.assertEqual(new_login_db.longitude, new_login_fields["lon"])
        self.assertEqual(new_login_db.timestamp, new_login_fields["timestamp"])

    def test_add_new_login(self):
        new_time = timezone.now()
        user_obj = User.objects.get(username="Lorena Goldoni")
        new_login_fields = {
            "id": "test2",
            "index": "fw-proxy",
            "ip": "1.1.1.1",
            "lat": 40.1245,
            "lon": 19.4271,
            "country": "United States",
            "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
            "timestamp": new_time,
        }
        detection.add_new_login(user_obj, new_login_fields)
        self.assertTrue(Login.objects.filter(user=user_obj, event_id=new_login_fields["id"]).exists())
        new_login = Login.objects.get(user=user_obj, event_id=new_login_fields["id"])
        self.assertEqual(new_login.index, new_login_fields["index"])
        self.assertEqual(new_login.ip, new_login_fields["ip"])
        self.assertEqual(new_login.latitude, new_login_fields["lat"])
        self.assertEqual(new_login.longitude, new_login_fields["lon"])
        self.assertEqual(new_login.country, new_login_fields["country"])
        self.assertEqual(new_login.user_agent, new_login_fields["agent"])
        self.assertEqual(new_login.timestamp, new_login_fields["timestamp"])

    def test_check_country_no_alerts(self):
        # testing function check_country with no alerts
        db_config = Config.objects.get(id=1)
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2025-02-26T17:10:33.358Z",
            "lat": 14.9876,
            "lon": 24.3456,
            "country": "Italy",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        self.assertDictEqual({}, detection.check_country(db_user, last_login_user_fields, db_config))

    def test_check_country_new_country_alert(self):
        # testing function check_country with "New Country" alert
        db_config = Config.objects.get(id=1)
        db_user = User.objects.get(username="Lorena Goldoni")
        alert_result = detection.check_country(db_user, self.raw_data_NEW_COUNTRY, db_config)
        self.assertEqual("New Country", alert_result["alert_name"])
        self.assertEqual(AlertDetectionType.NEW_COUNTRY.value, alert_result["alert_name"])
        self.assertEqual(
            "Login from new country for User: Lorena Goldoni, at: 2025-02-13T09:16:25.000Z, from: India",
            alert_result["alert_desc"],
        )

    def test_check_country_atypical_country_alert(self):
        # testing function check_country with "Atypical Country" alert
        db_config = Config.objects.get(id=1)
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2025-02-26T17:10:33.358Z",
            "lat": 44.4937,
            "lon": 24.3456,
            "country": "Germany",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        alert_result = detection.check_country(db_user, last_login_user_fields, db_config)
        self.assertEqual("Atypical Country", alert_result["alert_name"])
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY.value, alert_result["alert_name"])
        self.assertEqual(
            "Login from an atypical country for User: Lorena Goldoni, at: 2025-02-26T17:10:33.358Z, from: Germany",
            alert_result["alert_desc"],
        )

    def test_check_new_device(self):
        # Test to check that the NEW_DEVICE alert has not been triggered for the first seen device
        db_user = User.objects.get(username="Lorena Goldoni")
        Login.objects.filter(user=db_user).delete()
        devices = (
            Login.objects.filter(
                user=db_user,
            )
            .values("user_agent")
            .annotate(count=Count("id"))
        )
        self.assertEqual(0, len(devices))
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "14.9876",
            "lon": "24.3456",
            "country": "Sudan",
            "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
        }
        self.assertDictEqual({}, detection.check_new_device(db_user, last_login_user_fields))

    def test_check_new_device_alert(self):
        # Test to check the triggering of the NEW_DEVICE alert
        db_user = User.objects.get(username="Lorena Goldoni")
        # create a device for the user
        Login.objects.create(
            user=db_user,
            event_id="event_1",
            index="cloud",
            ip="1.2.3.4",
            timestamp=datetime.datetime(2023, 3, 8, 17, 8, 33, 358000, tzinfo=datetime.timezone.utc),
            latitude=40.364,
            longitude=-79.8605,
            country="United States",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
        )
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "14.9876",
            "lon": "24.3456",
            "country": "Sudan",
            "agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        alert_result = detection.check_new_device(db_user, last_login_user_fields)
        self.assertEqual("New Device", alert_result["alert_name"])
        self.assertEqual(
            "Login from new device for User: Lorena Goldoni, at: 2023-03-08T17:10:33.358Z",
            alert_result["alert_desc"],
        )

    def test_update_risk_level_norisk(self):
        """Test default no_risk level user"""
        # 0 alert --> no risk
        self.assertTrue(User.objects.filter(username="Lorena Goldoni").exists())
        db_user = User.objects.get(username="Lorena Goldoni")
        self.assertEqual("No risk", db_user.risk_score)

    def test_update_risk_level_low(self):
        """Test update_risk_level() function for low risk user, step-by-step alerts because every time both functions set_alert() and update_risk_level() are called and the "USER_RISK_THRESHOLD" alert could be triggered"""
        # 2 alerts --> Low risk
        db_config = Config.objects.get(id=1)
        self.assertTrue(User.objects.filter(username="Lorena Goldoni").exists())
        db_user = User.objects.get(username="Lorena Goldoni")
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL.value,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description",
        )
        self.assertTrue(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("Low", db_user.risk_score)
        alerts_user = db_user.alert_set.all()
        self.assertEqual(2, alerts_user.count())
        # first user's alert must be the IMP_TRAVEL one
        self.assertEqual(AlertDetectionType.IMP_TRAVEL.value, alerts_user[0].name)
        # then, the second alert must be the USER_RISK_THRESHOLD
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[1].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[1].description,
        )

    def test_update_risk_level_medium(self):
        """Test update_risk_level() function for medium risk user, step-by-step alerts because every time both functions set_alert() and update_risk_level() are called and the "USER_RISK_THRESHOLD" alert could be triggered"""
        #   4 alerts --> Medium risk
        db_config = Config.objects.get(id=1)
        self.assertTrue(User.objects.filter(username="Lorena Goldoni").exists())
        db_user = User.objects.get(username="Lorena Goldoni")
        # first alert --> risk_score passes to Low
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description1",
        )
        self.assertTrue(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("Low", db_user.risk_score)
        db_config.risk_score_increment_alerts = [AlertDetectionType.ATYPICAL_COUNTRY]
        alerts_user = db_user.alert_set.all().order_by("created")
        self.assertEqual(2, alerts_user.count())
        # first user's alert must be the IMP_TRAVEL one
        self.assertEqual(AlertDetectionType.IMP_TRAVEL.value, alerts_user[0].name)
        # then, the second alert must be the USER_RISK_THRESHOLD
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[1].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[1].description,
        )
        # second alert
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.NEW_DEVICE,
            login_raw_data=self.raw_data_NEW_DEVICE,
            description="Test_Description2",
        )
        # no new USER_RISK_THRESHOLD alert and risk_score decreased to "No risk" because the config.rik_score_incrmenet_alerts changed to just ATYPICAL_COUNTRY alert
        self.assertFalse(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("No risk", db_user.risk_score)
        alerts_user = db_user.alert_set.all().order_by("created")
        self.assertEqual(3, alerts_user.count())
        # first user's alert must be the IMP_TRAVEL one
        self.assertEqual(AlertDetectionType.IMP_TRAVEL.value, alerts_user[0].name)
        # then, the second alert must be the USER_RISK_THRESHOLD
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[1].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[1].description,
        )
        self.assertEqual(AlertDetectionType.NEW_DEVICE, alerts_user[2].name)
        # fourth alert
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.ATYPICAL_COUNTRY,
            login_raw_data=self.raw_data_NEW_COUNTRY,
            description="Test_Description3",
        )
        # USER_RISK_THRESHOLD alert
        self.assertTrue(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("Low", db_user.risk_score)
        alerts_user = db_user.alert_set.all().order_by("created")
        self.assertEqual(5, alerts_user.count())
        # first user's alert must be the IMP_TRAVEL one
        self.assertEqual(AlertDetectionType.IMP_TRAVEL.value, alerts_user[0].name)
        # then, the second alert must be the USER_RISK_THRESHOLD
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[1].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[1].description,
        )
        self.assertEqual(AlertDetectionType.NEW_DEVICE, alerts_user[2].name)
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY, alerts_user[3].name)
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[4].name)
        # again from "No risk" to "Low" because Config.risk_score_increment_alerts changed
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[4].description,
        )
        # fourth alert
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.ATYPICAL_COUNTRY,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description4",
        )
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.ATYPICAL_COUNTRY,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description5",
        )
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.ATYPICAL_COUNTRY,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description6",
        )
        # no new USER_RISK_THRESHOLD alert
        self.assertTrue(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("Medium", db_user.risk_score)
        alerts_user = db_user.alert_set.all().order_by("created")
        self.assertEqual(9, alerts_user.count())
        # first user's alert must be the IMP_TRAVEL one
        self.assertEqual(AlertDetectionType.IMP_TRAVEL.value, alerts_user[0].name)
        # then, the second alert must be the USER_RISK_THRESHOLD
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[1].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[1].description,
        )
        self.assertEqual(AlertDetectionType.NEW_DEVICE, alerts_user[2].name)
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY, alerts_user[3].name)
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[4].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from No risk to Low",
            alerts_user[4].description,
        )
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY, alerts_user[5].name)
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY, alerts_user[6].name)
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY, alerts_user[7].name)
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[8].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from Low to Medium",
            alerts_user[8].description,
        )

    def test_update_risk_level_high(self):
        """Test update_risk_level() function for high risk user, step-by-step alerts because every time both functions set_alert() and update_risk_level() are called and the "USER_RISK_THRESHOLD" alert could be triggered"""
        #   5 alerts --> High risk
        db_config = Config.objects.get(id=1)
        db_config.risk_score_increment_alerts.append("New Device")
        db_config.save()
        self.test_update_risk_level_medium()
        db_user = User.objects.get(username="Lorena Goldoni")
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description7",
        )
        alert.save()
        # new USER_RISK_THRESHOLD alert
        self.assertTrue(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description8",
        )
        alert.save()
        self.assertFalse(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("High", db_user.risk_score)
        alerts_user = db_user.alert_set.all().order_by("created")
        self.assertEqual(12, alerts_user.count())
        # the first 9 alerts have been checked in the previous function, called also at the beginning of this test
        self.assertEqual(AlertDetectionType.IMP_TRAVEL, alerts_user[9].name)
        self.assertEqual("Test_Description7", alerts_user[9].description)
        self.assertEqual(AlertDetectionType.USER_RISK_THRESHOLD, alerts_user[10].name)
        self.assertEqual(
            "User risk_score increased for User: Lorena Goldoni, who changed risk_score from Medium to High",
            alerts_user[10].description,
        )
        self.assertEqual(AlertDetectionType.IMP_TRAVEL, alerts_user[11].name)
        self.assertEqual("Test_Description8", alerts_user[11].description)
        # add some other alerts
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description9",
        )
        # no USER_RISK_THRESHOLD alert
        self.assertFalse(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("High", db_user.risk_score)
        self.assertEqual(13, db_user.alert_set.count())
        self.assertEqual(AlertDetectionType.IMP_TRAVEL, alerts_user[12].name)
        self.assertEqual("Test_Description9", alerts_user[12].description)
        alert = Alert.objects.create(
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            login_raw_data=self.raw_data_IMP_TRAVEL,
            description="Test_Description10",
        )
        # no USER_RISK_THRESHOLD alert
        self.assertFalse(detection.update_risk_level(db_user, triggered_alert=alert, app_config=db_config))
        self.assertEqual("High", db_user.risk_score)
        self.assertEqual(14, db_user.alert_set.count())
        self.assertEqual(AlertDetectionType.IMP_TRAVEL, alerts_user[13].name)
        self.assertEqual("Test_Description10", alerts_user[13].description)

    @patch("impossible_travel.modules.detection.update_risk_level")
    def test_set_alert(self, mock_update_risk_level):
        db_config = Config.objects.get(id=1)
        # Add an alert and check if it is correctly inserted in the Alert Model
        db_user = User.objects.get(username="Lorena Goldoni")
        db_login = Login.objects.get(user_agent="Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5")
        timestamp = db_login.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        login_data = {
            "timestamp": timestamp,
            "latitude": "45.4758",
            "longitude": "9.2275",
            "country": db_login.country,
            "agent": db_login.user_agent,
        }
        imp_travel_enrichment = {
            "start_country": "Poland",
            "avg_speed": 1000,
            "start_lat": 51.55,
            "start_lon": 19.08,
        }
        login_data["buffalogs"] = imp_travel_enrichment
        name = AlertDetectionType.IMP_TRAVEL
        desc = f"{name} for User: {db_user.username}, \
                    at: {timestamp}, from: ({db_login.latitude}, {db_login.longitude})"
        alert_info = {
            "alert_name": name,
            "alert_desc": desc,
        }
        detection.set_alert(db_user, login_data, alert_info, db_config)
        db_alert = Alert.objects.get(user=db_user, name=AlertDetectionType.IMP_TRAVEL)
        self.assertIsNotNone(db_alert)
        self.assertEqual("Imp Travel", db_alert.name)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual([AlertFilterType.ALLOWED_COUNTRY_FILTER], db_alert.filter_type)
        mock_update_risk_level.assert_not_called()

    @patch("impossible_travel.modules.detection.update_risk_level")
    def test_set_alert_vip_user(self, mock_update_risk_level):
        db_config = Config.objects.get(id=1)
        db_config.alert_is_vip_only = True
        db_config.save()
        # Test for alert in case of a vip_user
        db_user = User.objects.get(username="Lorena Goldoni")
        db_login = Login.objects.filter(user=db_user).first()
        timestamp = db_login.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        login_data = self.raw_data_IMP_TRAVEL
        name = AlertDetectionType.IMP_TRAVEL
        desc = f"{name} for User: {db_user.username}, \
                    at: {timestamp}, from: ({db_login.latitude}, {db_login.longitude})"
        alert_info = {
            "alert_name": name,
            "alert_desc": desc,
        }
        detection.set_alert(db_user, login_data, alert_info, db_config)
        db_alert = Alert.objects.get(user=db_user, name=AlertDetectionType.IMP_TRAVEL)
        self.assertTrue(db_alert.is_filtered)
        self.assertEqual(
            [AlertFilterType.IS_VIP_FILTER, AlertFilterType.ALLOWED_COUNTRY_FILTER],
            db_alert.filter_type,
        )
        mock_update_risk_level.assert_not_called()

    @patch("impossible_travel.modules.detection.update_risk_level")
    def test_set_alert_not_filtered_alert(self, mock_update_risk_level):
        # test if the update_risk_level is correctly called for a not filtered alert
        db_user = User.objects.get(username="Lorena Goldoni")
        db_config = Config.objects.get(id=1)
        db_config.allowed_countries = []
        db_config.save()
        alert_info = {
            "alert_name": AlertDetectionType.IMP_TRAVEL,
            "alert_desc": "description_fake",
        }
        login_data = self.raw_data_IMP_TRAVEL
        detection.set_alert(db_user, login_data, alert_info, db_config)
        db_alert = Alert.objects.get(user=db_user, name=AlertDetectionType.IMP_TRAVEL)
        self.assertFalse(db_alert.is_filtered)
        self.assertEqual([], db_alert.filter_type)
        mock_update_risk_level.assert_called_once_with(db_user=db_user, triggered_alert=db_alert, app_config=db_config)

    def test_check_fields_logins(self):
        fields1 = load_test_data("test_check_fields_part1")
        fields2 = load_test_data("test_check_fields_part2")
        db_user = User.objects.get(username="Aisha Delgado")
        # First part - Expected logins in Login Model:
        #   1. at 2023-05-03T06:50:03.768Z from India,
        #   2. at 2023-05-03T06:57:27.768Z from Japan,
        #   3. at 2023-05-03T07:10:23.154Z from United States
        detection.check_fields(db_user, fields1)
        self.assertEqual(
            3,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3").count(),
        )
        self.assertEqual(
            1,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="India").count(),
        )
        self.assertEqual(6, Login.objects.get(user=db_user, country="India").timestamp.hour)
        self.assertEqual(50, Login.objects.get(user=db_user, country="India").timestamp.minute)
        self.assertEqual(3, Login.objects.get(user=db_user, country="India").timestamp.second)
        self.assertEqual(
            1,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="United States").count(),
        )
        self.assertEqual(7, Login.objects.get(user=db_user, country="United States").timestamp.hour)
        self.assertEqual(
            10,
            Login.objects.get(user=db_user, country="United States").timestamp.minute,
        )
        self.assertEqual(
            23,
            Login.objects.get(user=db_user, country="United States").timestamp.second,
        )
        self.assertEqual(
            1,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="Japan").count(),
        )
        self.assertEqual(6, Login.objects.get(user=db_user, country="Japan").timestamp.hour)
        self.assertEqual(57, Login.objects.get(user=db_user, country="Japan").timestamp.minute)
        self.assertEqual(27, Login.objects.get(user=db_user, country="Japan").timestamp.second)
        # Second part - Expected changed logins in Login Model:
        #   4. at 2023-05-03T07:14:22.768Z from India with user_agent: Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0
        #   5. at 2023-05-03T07:18:38.768Z from India with user_agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)
        #   6. at 2023-05-03T07:20:36.154Z from United States with user_agent: Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0
        detection.check_fields(db_user, fields2)
        self.assertEqual(
            6,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3").count(),
        )
        self.assertEqual(
            3,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="India").count(),
        )
        self.assertEqual(
            7,
            Login.objects.get(
                user=db_user,
                country="India",
                user_agent="Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0",
            ).timestamp.hour,
        )
        self.assertEqual(
            14,
            Login.objects.get(
                user=db_user,
                country="India",
                user_agent="Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0",
            ).timestamp.minute,
        )
        self.assertEqual(
            22,
            Login.objects.get(
                user=db_user,
                country="India",
                user_agent="Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0",
            ).timestamp.second,
        )
        self.assertEqual(
            7,
            Login.objects.get(
                user=db_user,
                country="India",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
            ).timestamp.hour,
        )
        self.assertEqual(
            18,
            Login.objects.get(
                user=db_user,
                country="India",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
            ).timestamp.minute,
        )
        self.assertEqual(
            38,
            Login.objects.get(
                user=db_user,
                country="India",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
            ).timestamp.second,
        )
        self.assertEqual(
            2,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="United States").count(),
        )
        self.assertEqual(
            7,
            Login.objects.get(
                user=db_user,
                country="United States",
                user_agent="Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0",
            ).timestamp.hour,
        )
        self.assertEqual(
            31,
            Login.objects.get(
                user=db_user,
                country="United States",
                user_agent="Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0",
            ).timestamp.minute,
        )
        self.assertEqual(
            36,
            Login.objects.get(
                user=db_user,
                country="United States",
                user_agent="Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0",
            ).timestamp.second,
        )
        self.assertEqual(
            2,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="United States").count(),
        )
        self.assertEqual(
            7,
            Login.objects.filter(user=db_user, country="United States").last().timestamp.hour,
        )
        self.assertEqual(
            31,
            Login.objects.filter(user=db_user, country="United States").last().timestamp.minute,
        )
        self.assertEqual(
            36,
            Login.objects.filter(user=db_user, country="United States").last().timestamp.second,
        )
        self.assertEqual(
            1,
            Login.objects.filter(user=db_user, index="cloud-test_data-2023-5-3", country="Japan").count(),
        )
        self.assertEqual(6, Login.objects.get(user=db_user, country="Japan").timestamp.hour)
        self.assertEqual(57, Login.objects.get(user=db_user, country="Japan").timestamp.minute)
        self.assertEqual(27, Login.objects.get(user=db_user, country="Japan").timestamp.second)

    def test_check_fields_alerts(self):
        count_filtered_alerts = 0
        app_config = Config.objects.get(id=1)
        app_config.risk_score_increment_alerts.append("New Device")
        app_config.save()
        db_user = User.objects.get(username="Aisha Delgado")
        self.assertEqual(0, db_user.alert_set.count())
        fields1 = load_test_data("test_check_fields_part1")
        fields2 = load_test_data("test_check_fields_part2")
        detection.check_fields(db_user, fields1)
        # First part - Expected alerts in Alert Model:
        #   1. (2° login - id:2) at 2023-05-03T06:55:31.768Z alert NEW DEVICE (device_fingerprint="windows-10-desktop-other")
        #   2. (2° login - id:2) alert User Risk Threshold (from No risk to Low level)
        #   3. (2° login - id:2) at 2023-05-03T06:55:31.768Z alert NEW COUNTRY
        #   4. (2° login - id:2) at 2023-05-03T06:55:31.768Z alert IMP TRAVEL
        # ---
        #   5. (3° login - id: 3) at 2023-05-03T06:57:27.768Z alert ANONYMOUS_IP_LOGIN
        #   6. (3° login - id:3) alert User Risk Threshold (from Low to Medium level)
        #   7. (3° login - id: 3) at 2023-05-03T06:57:27.768Z alert NEW COUNTRY
        #   8. (3° login - id: 3) at 2023-05-03T06:57:27.768Z alert IMP TRAVEL

        #   9.(3° login - id: 3) alert User Risk Threshold (from Medium to High level)
        # ---
        #   10. (4° login - id: 4) at 2023-05-03T07:10:23.154Z alert IMP TRAVEL
        total_alerts = db_user.alert_set.filter().order_by("created")
        self.assertEqual("2023-05-03T06:55:31.768Z", total_alerts[0].login_raw_data["timestamp"])
        self.assertEqual("New Device", total_alerts[0].name)
        self.assertEqual("2023-05-03T06:55:31.768Z", total_alerts[1].login_raw_data["timestamp"])
        self.assertEqual("User Risk Threshold", total_alerts[1].name)
        self.assertEqual("2023-05-03T06:55:31.768Z", total_alerts[2].login_raw_data["timestamp"])
        self.assertEqual("New Country", total_alerts[2].name)
        self.assertEqual("2023-05-03T06:55:31.768Z", total_alerts[3].login_raw_data["timestamp"])
        self.assertEqual("Imp Travel", total_alerts[3].name)
        self.assertEqual("2023-05-03T06:57:27.768Z", total_alerts[4].login_raw_data["timestamp"])
        self.assertEqual("Anonymous IP Login", total_alerts[4].name)
        self.assertEqual("2023-05-03T06:57:27.768Z", total_alerts[5].login_raw_data["timestamp"])
        self.assertEqual("User Risk Threshold", total_alerts[5].name)
        self.assertEqual("2023-05-03T06:57:27.768Z", total_alerts[6].login_raw_data["timestamp"])
        self.assertEqual("New Country", total_alerts[6].name)
        self.assertEqual("2023-05-03T06:57:27.768Z", total_alerts[7].login_raw_data["timestamp"])
        self.assertEqual("Imp Travel", total_alerts[7].name)
        self.assertEqual("2023-05-03T07:10:23.154Z", total_alerts[8].login_raw_data["timestamp"])
        self.assertEqual("Imp Travel", total_alerts[8].name)
        self.assertEqual("2023-05-03T07:10:23.154Z", total_alerts[9].login_raw_data["timestamp"])
        self.assertEqual("User Risk Threshold", total_alerts[9].name)
        self.assertEqual(10, len(total_alerts))
        for alert in total_alerts:
            if alert.is_filtered:
                count_filtered_alerts += 1
        self.assertEqual(0, count_filtered_alerts)
        self.assertEqual(0, Alert.objects.filter(~Q(filter_type=[])).count())
        self.assertEqual(len(total_alerts), len(total_alerts) - count_filtered_alerts)  # not filtered alerts
        self.assertEqual(len(total_alerts), Alert.objects.filter(filter_type=[]).count())

        # ADD ORDER BY TO ENSURE CONSISTENT ORDERING
        new_device_alerts_fields1 = Alert.objects.filter(user=db_user, name=AlertDetectionType.NEW_DEVICE).order_by("created")
        self.assertEqual(1, new_device_alerts_fields1.count())
        new_country_alerts_fields1 = Alert.objects.filter(user=db_user, name=AlertDetectionType.NEW_COUNTRY).order_by("created")
        self.assertEqual(2, new_country_alerts_fields1.count())
        imp_travel_alerts_fields1 = Alert.objects.filter(user=db_user, name=AlertDetectionType.IMP_TRAVEL).order_by("created")
        self.assertEqual(3, imp_travel_alerts_fields1.count())
        user_risk_threshold_alerts_fields1 = Alert.objects.filter(user=db_user, name=AlertDetectionType.USER_RISK_THRESHOLD).order_by("created")
        self.assertEqual(3, user_risk_threshold_alerts_fields1.count())
        anonymous_ip_alerts_fields1 = Alert.objects.filter(user=db_user, name=AlertDetectionType.ANONYMOUS_IP_LOGIN).order_by("created")
        self.assertEqual(1, anonymous_ip_alerts_fields1.count())

        # check new_device alerts for fields1 logins
        self.assertEqual("New Device", new_device_alerts_fields1[0].name)
        self.assertEqual(
            "Login from new device for User: Aisha Delgado, at: 2023-05-03T06:55:31.768Z",
            new_device_alerts_fields1[0].description,
        )
        # check new_country alerts for fields1 logins
        self.assertEqual("New Country", new_country_alerts_fields1[0].name)
        self.assertEqual(
            "Login from new country for User: Aisha Delgado, at: 2023-05-03T06:55:31.768Z, from: United States",
            new_country_alerts_fields1[0].description,
        )
        self.assertEqual("New Country", new_country_alerts_fields1[1].name)
        self.assertEqual(
            "Login from new country for User: Aisha Delgado, at: 2023-05-03T06:57:27.768Z, from: Japan",
            new_country_alerts_fields1[1].description,
        )
        # check imp_travel alerts for fields1 logins
        self.assertEqual("Imp Travel", imp_travel_alerts_fields1[0].name)
        self.assertEqual(
            "Impossible Travel detected for User: Aisha Delgado, at: 2023-05-03T06:55:31.768Z, from: United States, previous country: India, distance covered at 133973 Km/h",
            imp_travel_alerts_fields1[0].description,
        )
        self.assertEqual("Imp Travel", imp_travel_alerts_fields1[1].name)
        self.assertEqual(
            "Impossible Travel detected for User: Aisha Delgado, at: 2023-05-03T06:57:27.768Z, from: Japan, previous country: United States, distance covered at 344009 Km/h",
            imp_travel_alerts_fields1[1].description,
        )
        self.assertEqual("Imp Travel", imp_travel_alerts_fields1[2].name)
        self.assertEqual(
            "Impossible Travel detected for User: Aisha Delgado, at: 2023-05-03T07:10:23.154Z, from: United States, previous country: Japan, distance covered at 52564 Km/h",
            imp_travel_alerts_fields1[2].description,
        )
        # check user_risk_threshold alerts for fields1 logins
        self.assertEqual("User Risk Threshold", user_risk_threshold_alerts_fields1[0].name)
        self.assertEqual(
            "User risk_score increased for User: Aisha Delgado, who changed risk_score from No risk to Low",
            user_risk_threshold_alerts_fields1[0].description,
        )
        self.assertEqual("User Risk Threshold", user_risk_threshold_alerts_fields1[1].name)
        self.assertEqual(
            "User risk_score increased for User: Aisha Delgado, who changed risk_score from Low to Medium",
            user_risk_threshold_alerts_fields1[1].description,
        )
        self.assertEqual("User Risk Threshold", user_risk_threshold_alerts_fields1[2].name)
        self.assertEqual(
            "User risk_score increased for User: Aisha Delgado, who changed risk_score from Medium to High",
            user_risk_threshold_alerts_fields1[2].description,
        )
        # check anonymous_ip_login alerts for fields1 logins
        self.assertEqual("Anonymous IP Login", anonymous_ip_alerts_fields1[0].name)
        self.assertEqual(
            "Login from an anonymous IP from IP: 203.0.113.20 by User: Aisha Delgado",
            anonymous_ip_alerts_fields1[0].description,
        )
        self.assertEqual(0, Alert.objects.filter(user=db_user, filter_type=["is_vip_filter"]).count())

        # Adding "Aisha Delgado" to vip users
        Config.objects.filter(id=1).delete()
        config = Config.objects.create(
            allowed_countries=["Italy", "Romania"],
            vip_users=["Aisha Delgado"],
            alert_is_vip_only=True,
        )
        config.risk_score_increment_alerts.append("New Device")
        config.save()

        # Second part - Expected new alerts in Alert Model:
        #   12. at 2023-05-03T07:14:22.768Z alert NEW DEVICE (device_fingerprint="android-4-mobile-firefoxmobile")
        #   13. at 2023-05-03T07:14:22.768Z alert IMP TRAVEL
        #   14. at 2023-05-03T07:18:38.768Z alert NEW DEVICE (device_fingeprint="linux-unknownosmajor-desktop-other")
        #   15. at 2023-05-03T07:18:38.768Z alert IMP TRAVEL
        #   16. at 2023-05-03T07:20:36.154Z alert IMP TRAVEL

        # get IDs of old alerts to check the new alerts
        new_device_alerts_fields1_ids = list(new_device_alerts_fields1.values_list("id", flat=True))

        detection.check_fields(db_user, fields2)
        # get new_device alerts relating to fields2 making query all_new_device_alerts - new_device_alerts_fields1
        all_new_device_alerts = Alert.objects.filter(user=db_user, name=AlertDetectionType.NEW_DEVICE).order_by("created")
        self.assertEqual(3, all_new_device_alerts.count())
        new_device_alerts_fields2 = all_new_device_alerts.exclude(id__in=new_device_alerts_fields1_ids).order_by("created")
        self.assertEqual(2, new_device_alerts_fields2.count())
        self.assertEqual(15, Alert.objects.filter(user=db_user).count())
        # check new_device alerts for fields2
        self.assertEqual("New Device", new_device_alerts_fields2[0].name)
        self.assertEqual(
            "Login from new device for User: Aisha Delgado, at: 2023-05-03T07:14:22.768Z",
            new_device_alerts_fields2[0].description,
        )
        self.assertEqual("New Device", new_device_alerts_fields2[1].name)
        self.assertEqual(
            "Login from new device for User: Aisha Delgado, at: 2023-05-03T07:18:38.768Z",
            new_device_alerts_fields2[1].description,
        )

        # same old new_country alert relating to fields1 logins
        self.assertEqual(
            2,
            Alert.objects.filter(user=db_user, name=AlertDetectionType.NEW_COUNTRY).count(),
        )

        self.assertEqual(
            6,
            Alert.objects.filter(user=db_user, name=AlertDetectionType.IMP_TRAVEL).count(),
        )

    def test_check_fields_usersip(self):
        db_user = User.objects.get(username="Aisha Delgado")
        fields1 = load_test_data("test_check_fields_part1")
        fields2 = load_test_data("test_check_fields_part2")
        fields3 = load_test_data("test_check_fields_part3")
        detection.check_fields(db_user, fields1)
        # First part: Check presence of ips in the UsersIP model
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.37").exists())
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.17").exists())
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.20").exists())
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.11").exists())
        self.assertEqual(4, UsersIP.objects.filter(user=db_user).count())
        # Second part: Check presence of ips in the UsersIP model
        detection.check_fields(db_user, fields2)
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.40").exists())
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.35").exists())
        self.assertTrue(UsersIP.objects.filter(user=db_user, ip="203.0.113.15").exists())
        self.assertEqual(7, UsersIP.objects.filter(user=db_user).count())
        # Check No duplicated ips
        self.assertEqual(1, UsersIP.objects.filter(user=db_user, ip="203.0.113.17").count())
        self.assertEqual(1, UsersIP.objects.filter(user=db_user, ip="203.0.113.11").count())
        # Third part: no new alerts because all the ips have already been used
        detection.check_fields(db_user, fields3)
        self.assertEqual(
            0,
            Alert.objects.filter(
                user=db_user,
                login_raw_data__timestamp__gt=datetime.datetime(2023, 5, 4, 0, 0, 0).isoformat(),
            ).count(),
        )
