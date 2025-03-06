from django.test import TestCase
from django.utils import timezone
from impossible_travel.models import Config, Login, User, UsersIP
from impossible_travel.modules import impossible_travel


class TestImpossibleTravel(TestCase):
    imp_travel = impossible_travel.Impossible_Travel()

    def setUp(self):
        Config.objects.create(
            id=1,
            ignored_users=["N/A", "Not Available"],
            ignored_ips=["0.0.0.0", "192.168.1.0/24"],
            allowed_countries=["Italy", "United States"],
            vip_users=["Asa Strickland", "Krista Moran"],
        )
        user_obj = User.objects.create(
            username="Lorena Goldoni",
            risk_score="Low",
        )
        Login.objects.create(
            user=user_obj,
            event_id="vfraw14gw",
            index="cloud",
            ip="1.2.3.4",
            timestamp="2023-03-08T17:08:33.358Z",
            latitude=40.364,
            longitude=-79.8605,
            country="United States",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
        )

    def test_calc_distance(self):
        # if distance >  Config.distance_accepted --> FALSE
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "40.364",
            "lon": "-79.8605",
            "country": "United States",
        }
        db_user = User.objects.get(username="Lorena Goldoni")
        prev_login = Login.objects.get(user_id=db_user.id)
        result, vel = self.imp_travel.calc_distance(db_user, prev_login, last_login_user_fields)
        self.assertEqual({}, result)
        self.assertEqual(0, vel)

    def test_calc_distance_alert(self):
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:08:33.358Z",
            "lat": "15.9876",
            "lon": "25.3456",
            "country": "Sudan",
        }
        db_user = User.objects.get(username="Lorena Goldoni")
        prev_login = Login.objects.get(user_id=db_user.id)
        result, vel = self.imp_travel.calc_distance(db_user, prev_login, last_login_user_fields)
        self.assertEqual("Imp Travel", result["alert_name"])
        self.assertEqual(
            "Impossible Travel detected for User: Lorena Goldoni, at: 2023-03-08T17:08:33.358Z, from: Sudan, "
            + f"previous country: United States, distance covered at {vel} Km/h",  # noqa: E231
            result["alert_desc"],
        )

    def test_update_model(self):
        """Test update_model() function for unique login, so with same user_agent and country"""
        user_obj = User.objects.get(username="Lorena Goldoni")
        old_login = Login.objects.get(user=user_obj)
        new_time = timezone.now()
        new_login_fields = {
            "id": "test1",
            "index": "cloud",
            "ip": "1.2.3.4",
            "lat": 39.1841,
            "lon": -77.0242,
            "country": "United States",
            "agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
            "timestamp": new_time,
        }
        self.imp_travel.update_model(user_obj, new_login_fields)
        new_login_db = Login.objects.get(user=user_obj)
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
        self.imp_travel.add_new_login(user_obj, new_login_fields)
        self.assertTrue(Login.objects.filter(user=user_obj, event_id=new_login_fields["id"]).exists())
        new_login = Login.objects.get(user=user_obj, event_id=new_login_fields["id"])
        self.assertEqual(new_login.index, new_login_fields["index"])
        self.assertEqual(new_login.ip, new_login_fields["ip"])
        self.assertEqual(new_login.latitude, new_login_fields["lat"])
        self.assertEqual(new_login.longitude, new_login_fields["lon"])
        self.assertEqual(new_login.country, new_login_fields["country"])
        self.assertEqual(new_login.user_agent, new_login_fields["agent"])
        self.assertEqual(new_login.timestamp, new_login_fields["timestamp"])

    def test_add_new_user_ip(self):
        """Test add_new_user_ip function for multiple ips to the same user"""
        user_obj = User.objects.get(username="Lorena Goldoni")
        source_ip1 = "5.9.5.2"
        self.imp_travel.add_new_user_ip(user_obj, source_ip1)
        source_ip2 = "6.7.8.9"
        self.imp_travel.add_new_user_ip(user_obj, source_ip2)
        self.assertEqual(2, UsersIP.objects.filter(user=user_obj).count())
