from django.db import IntegrityError
from django.test import TestCase
from impossible_travel.models import User, UserRiskScoreType


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
    # TODO
    pass


class TaskSettingsModelTest(TestCase):
    # TODO
    pass


class ConfigModelTest(TestCase):
    # TODO
    pass
