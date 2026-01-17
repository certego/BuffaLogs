from datetime import datetime, timedelta, timezone

from django.test import TestCase
from impossible_travel.constants import AlertDetectionType, UserRiskScoreType
from impossible_travel.models import Alert, Login, User
from impossible_travel.serializers import (
    AlertSerializer,
    LoginSerializer,
    UserSerializer,
)


class TestSerializers(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase - runs once per test class."""
        User.objects.bulk_create(
            [
                # User 1: NO_RISK, main user for most data
                User(username="Alice Johnson", risk_score=UserRiskScoreType.NO_RISK),
                # User 2: LOW_RISK, used for specific filtering tests
                User(username="Bob Smith", risk_score=UserRiskScoreType.LOW),
                # User 3: LOW_RISK, just for counting
                User(username="Charlie Brown", risk_score=UserRiskScoreType.LOW),
                # User 4: LOW_RISK, just for counting
                User(username="Diana Prince", risk_score=UserRiskScoreType.LOW),
                # User 5: MEDIUM_RISK, just for counting
                User(username="Eve Adams", risk_score=UserRiskScoreType.MEDIUM),
            ]
        )
        cls.db_user_alice = User.objects.get(username="Alice Johnson")
        cls.db_user_bob = User.objects.get(username="Bob Smith")
        cls.db_user_eve = User.objects.get(username="Eve Adams")

        cls.now = datetime.now(timezone.utc)
        cls.yesterday = cls.now - timedelta(days=1)
        cls.login_ts_1 = datetime(2023, 6, 19, 10, 1, 33, 358000, tzinfo=timezone.utc)
        cls.login_ts_2 = datetime(2023, 6, 19, 10, 8, 33, 358000, tzinfo=timezone.utc)
        cls.login_ts_3 = datetime(2023, 6, 20, 10, 1, 33, 358000, tzinfo=timezone.utc)

        Login.objects.bulk_create(
            [
                Login(
                    user=cls.db_user_alice,
                    event_id="vfraw14gw",
                    index="cloud",
                    ip="1.2.3.4",
                    timestamp=cls.login_ts_1,
                    latitude=40.364,
                    longitude=-79.8605,
                    country="United States",
                    user_agent="Chrome/78.0",
                    created=cls.yesterday,
                    updated=cls.yesterday,
                ),
                Login(
                    user=cls.db_user_alice,
                    event_id="ht9DEIgBnkLiMp6r-SG-",
                    index="weblog",
                    ip="203.0.113.24",
                    timestamp=cls.login_ts_2,
                    latitude=36.2462,
                    longitude=138.8497,
                    country="Japan",
                    user_agent="Firefox/107.0",
                    created=cls.yesterday,
                    updated=cls.yesterday,
                ),
                Login(
                    user=cls.db_user_bob,
                    event_id="login_low_risk",
                    index="test",
                    ip="5.6.7.8",
                    timestamp=cls.login_ts_1,
                    latitude=10.0,
                    longitude=10.0,
                    country="Germany",
                    user_agent="Edge/100.0",
                ),
            ]
        )

        cls.latest_login = Login(
            user=cls.db_user_alice,
            event_id="vfraw14gw",
            index="cloud",
            ip="1.2.3.4",
            timestamp=cls.login_ts_3,
            latitude=40.364,
            longitude=-79.8605,
            country="United States",
            user_agent="Chrome/78.0",
            created=cls.now,
            updated=cls.now,
        )

        cls.latest_login.save()

        cls.alert_ts_1 = datetime(2023, 5, 20, 11, 45, 1, 229000, tzinfo=timezone.utc)
        cls.alert_ts_2 = datetime(2023, 6, 19, 17, 17, 31, 358000, tzinfo=timezone.utc)

        Alert.objects.bulk_create(
            [
                Alert(
                    user=cls.db_user_alice,
                    name=AlertDetectionType.NEW_DEVICE,
                    login_raw_data={
                        "country": "Japan",
                        "timestamp": cls.alert_ts_1.isoformat(),
                        "ip": "203.0.113.24",
                    },
                    description="Test_Description0",
                    notified_status={"slack": True},  # Notified
                ),
                Alert(
                    user=cls.db_user_alice,
                    name=AlertDetectionType.IMP_TRAVEL,
                    login_raw_data={
                        "country": "United States",
                        "timestamp": cls.alert_ts_2.isoformat(),
                        "ip": "1.2.3.4",
                    },
                    description="Test_Description1",
                    is_vip=True,
                ),
                Alert(
                    user=cls.db_user_bob,
                    name=AlertDetectionType.NEW_DEVICE,
                    login_raw_data={
                        "country": "Germany",
                        "timestamp": cls.alert_ts_1.isoformat(),
                        "ip": "5.6.7.8",
                    },
                    description="Low Risk Alert",
                    notified_status={},  # Not notified
                ),
            ]
        )

    # ----------------------------------------------------------------------
    # Test QSerializer (Base for LoginSerializer and AlertSerializer)
    # ----------------------------------------------------------------------

    def test_qserializer_invalid_parameters(self):
        """Test that QSerializer raises ValueError for invalid parameter combinations."""
        # Both instance and query defined
        with self.assertRaises(ValueError) as context:
            LoginSerializer(instance=Login.objects.first(), query={"ip": "1.2.3.4"})
        self.assertEqual(
            str(context.exception),
            "Either `instance` or `query` parameter must be defined not both!",
        )

        # Neither instance nor query defined
        with self.assertRaises(ValueError) as context:
            LoginSerializer()
        self.assertEqual(
            str(context.exception),
            "Both `instance` and `query` parameters cannot be None, define only one!",
        )

    # ----------------------------------------------------------------------
    # Test LoginSerializer
    # ----------------------------------------------------------------------

    def test_login_serializer_single_object(self):
        """
        Test single instance serialized fields are correct.
        """
        login_obj = self.latest_login
        serializer = LoginSerializer(instance=login_obj)
        data = serializer.data

        self.assertEqual(data["event_id"], login_obj.event_id)
        self.assertEqual(data["user"], self.db_user_alice.username)
        self.assertEqual(data["country"], "united states")
        self.assertEqual(data["timestamp"], login_obj.timestamp)
        self.assertIn(self.now.strftime("%y-%m-%d %H:%M:%S")[:11], data["created"])
        self.assertIn(self.now.strftime("%y-%m-%d %H:%M:%S")[:11], data["updated"])
        self.assertEqual(data["ip"], "1.2.3.4")
        self.assertIsInstance(data, dict)

    def test_login_serializer_queryset_with_filters_and_pagination(self):
        """
        Test instance list with pagination applied.
        """
        query_params = {
            "username": self.db_user_alice.username,
            "country": "united states",
            "limit": 1,
            "offset": 0,
        }
        serializer = LoginSerializer(query=query_params)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["user"], self.db_user_alice.username)
        self.assertEqual(data[0]["country"], "united states")
        self.assertEqual(data[0]["timestamp"], self.login_ts_3)
        self.assertIsInstance(serializer.json(), str)

    def test_login_serializer_edge_case_no_objects_match_filters(self):
        """
        Test no objects match filters.
        """
        query_params = {"username": "NonExistentUser"}
        serializer = LoginSerializer(query=query_params)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_login_serializer_edge_case_many_true_equivalent(self):
        """
        Test Login serialization from queryset
        """
        login_qs = Login.objects.filter(user=self.db_user_alice).order_by("id")[:2]
        serializer = LoginSerializer(instance=login_qs)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["country"], "united states")
        self.assertEqual(data[1]["country"], "japan")

    # ----------------------------------------------------------------------
    # Test UserSerializer (Does not inherit from QSerializer)
    # ----------------------------------------------------------------------

    def test_user_serializer_single_object(self):
        """
        Test User serialization of single instance
        """
        user_obj = self.db_user_alice
        serializer = UserSerializer(instance=user_obj)
        data = serializer.data

        self.assertEqual(data["username"], "Alice Johnson")
        self.assertEqual(data["risk_score"], UserRiskScoreType.NO_RISK)
        self.assertEqual(data["login_count"], 3)
        self.assertEqual(data["alert_count"], 2)
        self.assertEqual(data["last_login"], self.login_ts_3)
        self.assertIsInstance(data, dict)

    def test_user_serializer_queryset_many_true_equivalent(self):
        """
        Test User serialization of queryset
        """
        # Get users with LOW risk (Bob, Charlie, Diana)
        users_qs = User.objects.filter(risk_score=UserRiskScoreType.LOW).order_by("id")
        serializer = UserSerializer(instance=users_qs)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

        bob_data = next(item for item in data if item["username"] == "Bob Smith")
        self.assertEqual(bob_data["risk_score"], UserRiskScoreType.LOW)
        self.assertEqual(bob_data["login_count"], 1)
        self.assertEqual(bob_data["alert_count"], 1)
        self.assertEqual(bob_data["last_login"], self.login_ts_1)

    # ----------------------------------------------------------------------
    # Test AlertSerializer
    # ----------------------------------------------------------------------

    def test_alert_serializer_single_object(self):
        """
        Test Alert serialization of single instance
        """
        alert_obj = Alert.objects.get(description="Test_Description0")  # Notified, NEW_DEVICE, Alice Johnson
        user_obj = alert_obj.user
        serializer = AlertSerializer(instance=alert_obj)
        data = serializer.data

        self.assertIn(alert_obj.created.strftime("%y-%m-%d %H:%M:%S")[:11], data["created"])
        self.assertEqual(data["country"], "japan")
        self.assertTrue(data["notified"])
        self.assertEqual(data["severity_type"], user_obj.risk_score)
        self.assertEqual(data["triggered_by"], user_obj.username)
        self.assertEqual(data["rule_name"], AlertDetectionType.NEW_DEVICE)
        self.assertFalse(data["is_vip"])
        self.assertIsInstance(data, dict)

    def test_alert_serializer_queryset_with_filters_and_pagination(self):
        """
        Test Alert serialization of query dictionary with matching filters
        """
        query_params = {
            "username": self.db_user_alice.username,
            "is_vip": True,
            "limit": 10,
            "offset": 0,
        }
        serializer = AlertSerializer(query=query_params)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["triggered_by"], self.db_user_alice.username)
        self.assertEqual(data[0]["rule_desc"], "Test_Description1")
        self.assertTrue(data[0]["is_vip"])

    def test_alert_serializer_edge_case_no_objects_match_filters(self):
        """
        Test Alert serialization of queryset with no matching filters
        """
        # Filter for an alert on a user with no alerts
        query_params = {"username": self.db_user_eve.username}
        serializer = AlertSerializer(query=query_params)
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_alert_serializer_edge_case_list_of_objects(self):
        """
        Test Alert serialization of instance list.
        """
        # Get all alerts for Alice Johnson
        alerts = Alert.objects.filter(user=self.db_user_alice).order_by("id")
        serializer = AlertSerializer(instance=list(alerts))
        data = serializer.data

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["rule_desc"], "Test_Description0")
        self.assertEqual(data[1]["rule_desc"], "Test_Description1")
