from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from impossible_travel.models import (
    Alert,
    AlertDetectionType,
    AlertFilterType,
    Config,
    ExecutionModes,
    Login,
    TaskSettings,
    User,
    UserRiskScoreType,
    UsersIP,
)


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="Lorygold",
            risk_score=UserRiskScoreType.LOW,
        )

    def test_model_fields(self):
        """Check the existing model fields"""
        model_fields = [f.name for f in User._meta.get_fields()]
        # add also foreignkey fields
        expected_fields = [
            "id",
            "risk_score",
            "username",
            "created",
            "updated",
            "login",
            "alert",
            "usersip",
        ]
        self.assertCountEqual(model_fields, expected_fields)

    def test_user_creation(self):
        """Check correct user creation"""
        self.assertIsInstance(self.user, User)
        self.assertEqual(self.user.username, "Lorygold")
        self.assertEqual(self.user.risk_score, UserRiskScoreType.LOW)
        self.assertIsNotNone(self.user.created)
        self.assertIsNotNone(self.user.updated)

    def test_str_representation(self):
        """Test __str__ correct representation"""
        expected_str = f"User object ({self.user.id}) - {self.user.username}"
        self.assertEqual(str(self.user), expected_str)

    def test_default_risk_score(self):
        """Test default risk_score value"""
        user = User.objects.create(username="bob")
        self.assertEqual(user.risk_score, UserRiskScoreType.NO_RISK)

    def test_username_uniqueness(self):
        """Test that the username is unique"""
        with self.assertRaises(IntegrityError):
            User.objects.create(username="Lorygold", risk_score=UserRiskScoreType.HIGH)

    def test_updated_field_changes_on_save(self):
        """Test the auto-update of the field updated"""
        old_updated = self.user.updated
        self.user.username = "Lorygold_updated"
        self.user.save()
        self.user.refresh_from_db()
        self.assertGreater(self.user.updated, old_updated)

    def test_invalid_risk_score_raises_error(self):
        """CheckConstraint must arise for an invalid risk_score"""
        invalid_user = User(username="invalid_user", risk_score="INVALID")
        with self.assertRaises(IntegrityError):
            invalid_user.save()


class LoginModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser-a")
        self.login = Login.objects.create(
            user=self.user,
            timestamp=timezone.now(),
            latitude=40.7128,
            longitude=-74.0060,
            country="India",
            user_agent="Mozilla/5.0",
            index="test_index_abc",
            event_id="event_123",
            ip="172.241.212.12",
        )

    def test_model_fields(self):
        """Check the existing model fields"""
        model_fields = [f.name for f in Login._meta.get_fields()]
        expected_fields = [
            "id",
            "user",
            "created",
            "updated",
            "timestamp",
            "latitude",
            "longitude",
            "country",
            "user_agent",
            "index",
            "event_id",
            "ip",
            "device_fingerprint",
        ]
        self.assertCountEqual(model_fields, expected_fields)

    def test_login_creation(self):
        """Check correct login creation"""
        self.assertIsInstance(self.login, Login)
        self.assertEqual(self.login.user, self.user)
        self.assertEqual(self.login.ip, "172.241.212.12")
        self.assertEqual(self.login.country, "India")
        self.assertEqual(self.login.latitude, 40.7128)
        self.assertEqual(self.login.longitude, -74.0060)
        self.assertIsNotNone(self.login.created)
        self.assertIsNotNone(self.login.updated)
        self.assertIsNotNone(self.login.timestamp)

    def test_login_with_nullable_fields(self):
        """Test login creation with nullable latitude/longitude"""
        login = Login.objects.create(
            user=self.user,
            index="test_index_xyz",
            event_id="event_456",
            ip="10.0.0.1",
        )
        self.assertIsNone(login.latitude)
        self.assertIsNone(login.longitude)
        self.assertEqual(login.country, "")
        self.assertEqual(login.user_agent, "")

    def test_login_foreign_key_cascade(self):
        """Test that deleting user deletes related logins"""
        login_id = self.login.id
        self.user.delete()
        with self.assertRaises(Login.DoesNotExist):
            Login.objects.get(id=login_id)

    def test_updated_field_changes_on_save(self):
        """Test auto-update of updated field"""
        old_updated = self.login.updated
        self.login.ip = "192.168.1.2"
        self.login.save()
        self.login.refresh_from_db()
        self.assertGreater(self.login.updated, old_updated)

    def test_apply_filters_username(self):
        """Test apply_filters method with username filter"""
        Login.objects.create(
            user=self.user,
            index="idx",
            event_id="evt",
            ip="1.1.1.1",
        )
        other_user = User.objects.create(username="otheruser")
        Login.objects.create(
            user=other_user,
            index="idx2",
            event_id="evt2",
            ip="2.2.2.2",
        )
        results = Login.apply_filters(username="testuser")
        self.assertEqual(results.count(), 2)
        for login in results:
            self.assertEqual(login.user.username, "testuser-a")

    def test_apply_filters_ip(self):
        """Test apply_filters method with IP filter"""
        results = Login.apply_filters(ip="172.241.212.12")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().ip, "172.241.212.12")

    def test_apply_filters_country(self):
        """Test apply_filters method with country filter"""
        results = Login.apply_filters(country="India")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().country, "India")

    def test_apply_filters_limit_offset(self):
        """Test apply_filters with pagination"""
        for i in range(5):
            Login.objects.create(
                user=self.user,
                index=f"idx_{i}",
                event_id=f"evt_{i}",
                ip=f"192.168.1.{i}",
            )
        results = Login.apply_filters(limit=3, offset=0)
        self.assertEqual(len(results), 3)
        results_offset = Login.apply_filters(limit=3, offset=3)
        self.assertEqual(len(results_offset), 3)


class UsersIPModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.users_ip = UsersIP.objects.create(
            user=self.user,
            ip="172.241.212.120",
        )

    def test_model_fields(self):
        """Check the existing model fields"""
        model_fields = [f.name for f in UsersIP._meta.get_fields()]
        expected_fields = ["id", "created", "updated", "user", "ip"]
        self.assertCountEqual(model_fields, expected_fields)

    def test_users_ip_creation(self):
        """Check correct UsersIP creation"""
        self.assertIsInstance(self.users_ip, UsersIP)
        self.assertEqual(self.users_ip.user, self.user)
        self.assertEqual(self.users_ip.ip, "172.241.212.120")
        self.assertIsNotNone(self.users_ip.created)
        self.assertIsNotNone(self.users_ip.updated)

    def test_users_ip_foreign_key_cascade(self):
        """Test that deleting user deletes related UsersIP records"""
        users_ip_id = self.users_ip.id
        self.user.delete()
        with self.assertRaises(UsersIP.DoesNotExist):
            UsersIP.objects.get(id=users_ip_id)

    def test_users_ip_ipv4_address(self):
        """Test UsersIP with valid IPv4 address"""
        users_ip = UsersIP.objects.create(user=self.user, ip="10.0.0.1")
        self.assertEqual(users_ip.ip, "10.0.0.1")

    def test_users_ip_ipv6_address(self):
        """Test UsersIP with valid IPv6 address"""
        users_ip = UsersIP.objects.create(
            user=self.user, ip="2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        self.assertEqual(users_ip.ip, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")

    def test_users_ip_invalid_ip_raises_error(self):
        """Test that invalid IP address raises ValidationError"""
        invalid_users_ip = UsersIP(user=self.user, ip="not_an_ip")
        with self.assertRaises(ValidationError):
            invalid_users_ip.full_clean()

    def test_updated_field_changes_on_save(self):
        """Test auto-update of updated field"""
        old_updated = self.users_ip.updated
        self.users_ip.ip = "172.241.212.120"
        self.users_ip.save()
        self.users_ip.refresh_from_db()
        self.assertGreater(self.users_ip.updated, old_updated)

    def test_multiple_ips_per_user(self):
        """Test that a user can have multiple IP addresses"""
        UsersIP.objects.create(user=self.user, ip="10.0.0.1")
        UsersIP.objects.create(user=self.user, ip="10.0.0.2")
        user_ips = UsersIP.objects.filter(user=self.user)
        self.assertEqual(user_ips.count(), 3)


class AlertModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="alice")
        self.alert = Alert.objects.create(
            name=AlertDetectionType.NEW_DEVICE,
            user=self.user,
            login_raw_data={"ip": "1.1.1.1"},
            description="Suspicious login detected",
            tags=["SECURITY_THREAT", "TEST_EVENT"],
            filter_type=[],
            is_vip=False,
        )

    def test_model_fields(self):
        """Check the existing model fields"""
        model_fields = [f.name for f in Alert._meta.get_fields()]
        expected_fields = [
            "id",
            "name",
            "user",
            "login_raw_data",
            "created",
            "updated",
            "description",
            "is_vip",
            "filter_type",
            "tags",
            "notified_status",
        ]
        self.assertCountEqual(model_fields, expected_fields)

    def test_alert_creation(self):
        """Check correct alert creation"""
        self.assertIsInstance(self.alert, Alert)
        self.assertEqual(self.alert.user, self.user)
        self.assertEqual(self.alert.name, AlertDetectionType.NEW_DEVICE)
        self.assertEqual(self.alert.description, "Suspicious login detected")
        self.assertIsNotNone(self.alert.created)
        self.assertIsNotNone(self.alert.updated)

    def test_tags_field(self):
        """Test tags stores valid alert tag values"""
        self.assertIn("SECURITY_THREAT", self.alert.tags)
        self.assertIn("TEST_EVENT", self.alert.tags)

    def test_tags_validation(self):
        """Invalid tag should raise ValidationError via validator"""
        invalid_alert = Alert(
            name=AlertDetectionType.NEW_DEVICE,
            user=self.user,
            login_raw_data={},
            description="invalid tag",
            tags=["INVALID_TAG"],
        )
        with self.assertRaises(ValidationError):
            invalid_alert.full_clean()

    def test_filter_type_sets_is_filtered_property(self):
        """Check is_filtered returning correct value or not"""
        self.assertFalse(self.alert.is_filtered)
        self.alert.filter_type = [AlertFilterType.USER_LEARNING_PERIOD]
        self.alert.save()
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.is_filtered)

    def test_check_constraint_invalid_detection_type(self):
        """CheckConstraint must arise for an invalid name"""
        invalid_alert = Alert(
            name="NOT_VALID",
            user=self.user,
            login_raw_data={},
            description="Invalid detection type",
        )
        with self.assertRaises(IntegrityError):
            invalid_alert.save()

    def test_check_constraint_invalid_filter_type(self):
        """CheckConstraint for invalid filter_type element"""
        invalid_alert = Alert(
            name=AlertDetectionType.NEW_DEVICE,
            user=self.user,
            login_raw_data={},
            description="Invalid filter type",
            filter_type=["WRONG"],
        )
        with self.assertRaises(IntegrityError):
            invalid_alert.save()

    def test_updated_field_changes_on_save(self):
        """Test auto-update of updated field"""
        old_updated = self.alert.updated
        self.alert.description = "Updated description"
        self.alert.save()
        self.alert.refresh_from_db()
        self.assertGreater(self.alert.updated, old_updated)


class TaskSettingsModelTest(TestCase):
    def setUp(self):
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timezone.timedelta(days=1)

    def test_tasksettings_creation(self):
        """TaskSettings object should be created"""
        task = TaskSettings.objects.create(
            task_name="clear_models",
            start_date=self.start_date,
            end_date=self.end_date,
            execution_mode=ExecutionModes.AUTOMATIC,
        )
        self.assertEqual(task.task_name, "clear_models")
        self.assertEqual(task.execution_mode, ExecutionModes.AUTOMATIC)
        self.assertTrue(task.created is not None)
        self.assertTrue(task.updated is not None)

    def test_unique_task_execution_constraint(self):
        """Duplicate task_name + execution_mode should raises an error"""
        TaskSettings.objects.create(
            task_name="clear_models",
            start_date=self.start_date,
            end_date=self.end_date,
            execution_mode=ExecutionModes.AUTOMATIC,
        )
        with self.assertRaises(IntegrityError):
            TaskSettings.objects.create(
                task_name="clear_models",
                start_date=self.start_date,
                end_date=self.end_date,
                execution_mode=ExecutionModes.AUTOMATIC,
            )

    def test_different_execution_modes_allowed(self):
        """Same task_name with different execution_mode should be allowed"""
        TaskSettings.objects.create(
            task_name="clear_models",
            start_date=self.start_date,
            end_date=self.end_date,
            execution_mode=ExecutionModes.AUTOMATIC,
        )
        task = TaskSettings.objects.create(
            task_name="clear_models",
            start_date=self.start_date,
            end_date=self.end_date,
            execution_mode=ExecutionModes.MANUAL,
        )
        self.assertEqual(task.execution_mode, ExecutionModes.MANUAL)


class ConfigModelTest(TestCase):
    def setUp(self):
        Config.objects.all().delete()  # Deleted any existing Config object to ensurre singleton behavior
        self.config = Config.objects.create(
            ignored_users=["admin", "test_user"],
            enabled_users=[],
            vip_users=["vip_user"],
            alert_is_vip_only=False,
            alert_minimum_risk_score=UserRiskScoreType.MEDIUM,
            risk_score_increment_alerts=[AlertDetectionType.NEW_DEVICE],
            ignored_ips=["127.0.0.1"],
            allowed_countries=["India"],
            ignored_ISPs=[],
            ignore_mobile_logins=True,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.HIGH,
            distance_accepted=500,
            vel_accepted=800,
            atypical_country_days=30,
            user_learning_period=7,
            user_max_days=365,
            login_max_days=90,
            alert_max_days=180,
            ip_max_days=90,
        )

    def test_model_fields(self):
        """Check the existing model fields"""
        model_fields = [f.name for f in Config._meta.get_fields()]
        expected_fields = [
            "id",
            "created",
            "updated",
            "ignored_users",
            "enabled_users",
            "vip_users",
            "alert_is_vip_only",
            "alert_minimum_risk_score",
            "risk_score_increment_alerts",
            "ignored_ips",
            "allowed_countries",
            "ignored_ISPs",
            "ignore_mobile_logins",
            "filtered_alerts_types",
            "threshold_user_risk_alert",
            "ignored_impossible_travel_countries_couples",
            "ignored_impossible_travel_all_same_country",
            "distance_accepted",
            "vel_accepted",
            "atypical_country_days",
            "user_learning_period",
            "user_max_days",
            "login_max_days",
            "alert_max_days",
            "ip_max_days",
        ]
        self.assertCountEqual(model_fields, expected_fields)

    def test_config_creation(self):
        """Check correct Config creation"""
        self.assertIsInstance(self.config, Config)
        self.assertEqual(self.config.ignored_users, ["admin", "test_user"])
        self.assertEqual(self.config.vip_users, ["vip_user"])
        self.assertEqual(self.config.alert_minimum_risk_score, UserRiskScoreType.MEDIUM)
        self.assertTrue(self.config.ignore_mobile_logins)
        self.assertIsNotNone(self.config.created)
        self.assertIsNotNone(self.config.updated)

    def test_config_singleton_constraint(self):
        """Test that only one Config object can exist"""
        with self.assertRaises(ValidationError):
            Config.objects.create(
                alert_minimum_risk_score=UserRiskScoreType.LOW,
            )

    def test_config_always_has_id_one(self):
        """Test that Config object always has id=1"""
        self.assertEqual(self.config.id, 1)
        self.assertEqual(self.config.pk, 1)

    def test_config_array_fields(self):
        """Test that array fields store correct values"""
        self.assertIn("admin", self.config.ignored_users)
        self.assertIn("vip_user", self.config.vip_users)
        self.assertIn(
            AlertDetectionType.NEW_DEVICE, self.config.risk_score_increment_alerts
        )

    def test_config_positive_integer_fields(self):
        """Test that positive integer fields have correct values"""
        self.assertEqual(self.config.distance_accepted, 500)
        self.assertEqual(self.config.vel_accepted, 800)
        self.assertEqual(self.config.atypical_country_days, 30)
        self.assertGreater(self.config.user_max_days, 0)
        self.assertGreater(self.config.login_max_days, 0)

    def test_config_default_values(self):
        """Test Config default values from settings"""
        Config.objects.all().delete()
        config = Config.objects.create()
        self.assertIsNotNone(config.ignored_users)
        self.assertIsNotNone(config.enabled_users)
        self.assertEqual(config.alert_minimum_risk_score, UserRiskScoreType.MEDIUM)
        self.assertTrue(config.ignored_impossible_travel_all_same_country)

    def test_updated_field_changes_on_save(self):
        """Test auto-update of updated field"""
        old_updated = self.config.updated
        self.config.alert_is_vip_only = True
        self.config.save()
        self.config.refresh_from_db()
        self.assertGreater(self.config.updated, old_updated)

    def test_check_constraint_invalid_alert_minimum_risk_score(self):
        """CheckConstraint for invalid alert_minimum_risk_score"""
        self.config.alert_minimum_risk_score = "INVALID_SCORE"
        with self.assertRaises(IntegrityError):
            self.config.save()

    def test_ignored_impossible_travel_countries_couples(self):
        """Test ignored_impossible_travel_countries_couples field"""
        self.config.ignored_impossible_travel_countries_couples = [
            ["Italy", "Italy"],
            ["India", "Canada"],
        ]
        self.config.save()
        self.config.refresh_from_db()
        self.assertEqual(
            len(self.config.ignored_impossible_travel_countries_couples), 2
        )
        self.assertIn(
            ["Italy", "Italy"], self.config.ignored_impossible_travel_countries_couples
        )

    def test_config_boolean_fields(self):
        """Test boolean fields work correctly"""
        self.assertFalse(self.config.alert_is_vip_only)
        self.assertTrue(self.config.ignore_mobile_logins)
        self.config.alert_is_vip_only = True
        self.config.save()
        self.config.refresh_from_db()
        self.assertTrue(self.config.alert_is_vip_only)
