from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from impossible_travel.models import Config


class ManagementCommandsTestCase(TestCase):
    def setUp(self):
        # Ensure a Config instance with id=1 exists before each test
        self.config, _ = Config.objects.get_or_create(id=1)

    # Testing the setup_config mgmt command
    def test_append_to_list_field(self):
        # Test appending a value to a list field (default action for lists)
        out = StringIO()
        call_command("setup_config", "ignored_users=admin", stdout=out)
        self.config.refresh_from_db()
        self.assertIn("admin", self.config.ignored_users)
        self.assertIn("Config updated successfully", out.getvalue())

    def test_override_non_list_field(self):
        # Test overriding a non-list field (e.g. boolean)
        out = StringIO()
        call_command("setup_config", "-o", "alert_is_vip_only=True", stdout=out)
        self.config.refresh_from_db()
        self.assertTrue(self.config.alert_is_vip_only)
        self.assertIn("Config updated successfully", out.getvalue())

    def test_append_non_list_field_raises(self):
        # Appending to a non-list field should raise a CommandError
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "alert_is_vip_only=True")
        self.assertIn("Append (-a) operation allowed only on list fields", str(cm.exception))

    def test_remove_from_list_field(self):
        # Test removing a value from a list field
        self.config.ignored_users = ["admin", "bot"]
        self.config.save()
        out = StringIO()
        call_command("setup_config", "-r", "ignored_users=admin", stdout=out)
        self.config.refresh_from_db()
        self.assertNotIn("admin", self.config.ignored_users)
        self.assertIn("bot", self.config.ignored_users)
        self.assertIn("Config updated successfully", out.getvalue())

    def test_override_list_field(self):
        # Test overriding a list field completely
        out = StringIO()
        call_command("setup_config", "-o", "ignored_users=[admin,bot]", stdout=out)
        self.config.refresh_from_db()
        self.assertEqual(set(self.config.ignored_users), {"admin", "bot"})
        self.assertIn("Config updated successfully", out.getvalue())

    def test_invalid_field_raises(self):
        # Using a non-existent field name should raise an error
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "non_existing_field=value")
        self.assertIn("does not exist in Config model", str(cm.exception))

    def test_invalid_choice_value_raises(self):
        # Using an invalid choice for a CharField with choices should raise an error
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "-o", "alert_minimum_risk_score=InvalidChoice")
        self.assertIn("Invalid choice", str(cm.exception))

    def test_validator_error_raises(self):
        # Using invalid values that violate validators should raise an error
        # Example: invalid IP in ignored_ips assuming validator raises ValidationError
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "-o", "ignored_ips=[invalid_ip]")
        self.assertIn("Validation error for field", str(cm.exception))

    def test_set_default_values_resets_all_fields(self):
        # Test that --set-default-values resets all Config fields to default values
        self.config.ignored_users = ["admin"]
        self.config.alert_is_vip_only = True
        self.config.save()

        out = StringIO()
        call_command("setup_config", "--set-default-values", stdout=out)
        self.config.refresh_from_db()

        # Check that values were reset to default
        self.assertFalse(self.config.alert_is_vip_only)
        self.assertNotIn("admin", self.config.ignored_users or [])
        self.assertIn("Config reset to default values successfully", out.getvalue())

    def test_help_output_includes_fields(self):
        # Check that the help output includes the list of Config fields and usage info
        out = StringIO()
        call_command("setup_config", "--help", stdout=out)
        output = out.getvalue()
        self.assertIn("ignored_users", output)
        self.assertIn("alert_is_vip_only", output)
        self.assertIn("Usage:", output)
