from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from impossible_travel.models import Alert, AlertDetectionType, AlertFilterType, User, UserRiskScoreType


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
        expected_fields = ["id", "risk_score", "username", "created", "updated", "login", "alert", "usersip"]
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
    # TODO
    pass


class UsersIPModelTest(TestCase):
    # TODO
    pass


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
    # TODO
    pass


class ConfigModelTest(TestCase):
    # TODO
    pass
