import io
from unittest.mock import patch

from django.conf import settings
from django.core.management import CommandError, call_command
from django.db.models.fields import Field
from django.test import TestCase
from impossible_travel.constants import AlertDetectionType, UserRiskScoreType
from impossible_travel.management.commands.setup_config import Command, parse_field_value
from impossible_travel.models import (
    Config,
    User,
    get_default_allowed_countries,
    get_default_enabled_users,
    get_default_filtered_alerts_types,
    get_default_ignored_ips,
    get_default_ignored_ISPs,
    get_default_ignored_users,
    get_default_risk_score_increment_alerts,
    get_default_vip_users,
)


class ManagementCommandsTestCase(TestCase):
    def setUp(self):
        self.config, _ = Config.objects.get_or_create(id=1)

    # === Tests for setup_config.py mgmt command -

    def test_options_values_passed(self):
        parser = Command().create_parser("manage.py", "setup_config")
        options = parser.parse_args(["-o", "allowed_countries=[IT,RO]", "-r", "ignored_users=[admin]", "-a", "alert_is_vip_only=True"])
        self.assertEqual(options.override, ["allowed_countries=[IT,RO]"])
        self.assertEqual(options.remove, ["ignored_users=[admin]"])
        self.assertEqual(options.append, ["alert_is_vip_only=True"])

    def test_options_values_passed_2(self):
        # reset config
        Config.objects.all().delete()
        config = Config.objects.create(
            id=1,
            ignore_mobile_logins=False,
            filtered_alerts_types=[],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        # check initial state
        self.assertFalse(config.ignore_mobile_logins)
        self.assertListEqual(config.filtered_alerts_types, [])
        self.assertEqual(config.alert_minimum_risk_score, UserRiskScoreType.NO_RISK)
        self.assertEqual(config.threshold_user_risk_alert, UserRiskScoreType.NO_RISK)
        # simulate mgmt command parsing
        args = [
            "-o",
            "ignore_mobile_logins=True",
            "-o",
            "filtered_alerts_types=[New Device, User Risk Threshold]",
            "-o",
            "alert_minimum_risk_score=Medium",
            "-o",
            "threshold_user_risk_alert=Medium",
        ]
        parser = Command().create_parser("manage.py", "setup_config")
        options = parser.parse_args(args)
        # check that parser collected all overrides
        self.assertEqual(
            options.override,
            [
                "ignore_mobile_logins=True",
                "filtered_alerts_types=[New Device, User Risk Threshold]",
                "alert_minimum_risk_score=Medium",
                "threshold_user_risk_alert=Medium",
            ],
        )
        # execute command
        call_command("setup_config", *args)
        config.refresh_from_db()
        # check updated config values
        self.assertTrue(config.ignore_mobile_logins)
        self.assertListEqual(config.filtered_alerts_types, ["New Device", "User Risk Threshold"])
        self.assertEqual(config.alert_minimum_risk_score, UserRiskScoreType.MEDIUM)
        self.assertEqual(config.threshold_user_risk_alert, UserRiskScoreType.MEDIUM)

    def test_handle_set_default_values_force(self):
        # Testing the option --set-default-values (force mode)
        # Check that if new fields in the Config model have been added, they should be integrated into this test
        config_editable_fields = [f.name for f in Config._meta.get_fields() if isinstance(f, Field) and f.editable and not f.auto_created]
        self.assertEqual(22, len(config_editable_fields))
        # Put random values into fields
        self.config.ignored_users = ["blabla", "user2"]
        self.config.alert_is_vip_only = True
        self.config.alert_minimum_risk_score = UserRiskScoreType.MEDIUM
        self.config.risk_score_increment_alerts = [AlertDetectionType.NEW_COUNTRY, AlertDetectionType.ATYPICAL_COUNTRY]
        self.config.ignored_ips = ["9.9.9.9", "4.5.4.5"]
        self.config.ignored_ISPs = ["isp1"]
        self.config.atypical_country_days = 80
        self.config.save()
        self.config.refresh_from_db()
        # check that new random values have been correctly saved
        self.assertListEqual(self.config.ignored_users, ["blabla", "user2"])
        self.assertTrue(self.config.alert_is_vip_only)
        self.assertEqual(self.config.alert_minimum_risk_score, "Medium")
        self.assertListEqual(self.config.risk_score_increment_alerts, ["New Country", "Atypical Country"])
        self.assertListEqual(self.config.ignored_ips, ["9.9.9.9", "4.5.4.5"])
        self.assertListEqual(self.config.ignored_ISPs, ["isp1"])
        self.assertEqual(self.config.atypical_country_days, 80)
        self.assertEqual(self.config.user_learning_period, 14)
        # call the mgmt command with the --set-default-values option
        call_command("setup_config", "--set-default-values", "--force")
        self.config.refresh_from_db()
        # check the corrispondence with the default values
        self.assertListEqual(self.config.ignored_users, get_default_ignored_users())
        self.assertListEqual(self.config.enabled_users, get_default_enabled_users())
        self.assertListEqual(self.config.vip_users, get_default_vip_users())
        self.assertFalse(self.config.alert_is_vip_only)
        self.assertEqual(self.config.alert_minimum_risk_score, "Medium")
        self.assertListEqual(self.config.risk_score_increment_alerts, get_default_risk_score_increment_alerts())
        self.assertListEqual(self.config.ignored_ips, get_default_ignored_ips())
        self.assertListEqual(self.config.allowed_countries, get_default_allowed_countries())
        self.assertListEqual(self.config.ignored_ISPs, get_default_ignored_ISPs())
        self.assertTrue(self.config.ignore_mobile_logins)
        self.assertListEqual(self.config.filtered_alerts_types, get_default_filtered_alerts_types())
        self.assertEqual(self.config.threshold_user_risk_alert, "Medium")
        self.assertEqual(self.config.distance_accepted, settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED)
        self.assertEqual(self.config.vel_accepted, settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED)
        self.assertEqual(self.config.atypical_country_days, settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS)
        self.assertEqual(self.config.user_max_days, settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS)
        self.assertEqual(self.config.login_max_days, settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS)
        self.assertEqual(self.config.alert_max_days, settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS)
        self.assertEqual(self.config.ip_max_days, settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS)
        self.assertTrue(self.config.ignored_impossible_travel_all_same_country)
        self.assertEqual(self.config.ignored_impossible_travel_countries_couples, [])
        self.assertEqual(self.config.user_learning_period, settings.CERTEGO_BUFFALOGS_USER_LEARNING_PERIOD)

    def test_handle_set_default_values_safe(self):
        # Testing the option --set-default-values (safe mode)
        # Check that if new fields in the Config model have been added, they should be integrated into this test
        config_editable_fields = [f.name for f in Config._meta.get_fields() if isinstance(f, Field) and f.editable and not f.auto_created]
        self.assertEqual(22, len(config_editable_fields))
        # Put random values into fields
        self.config.ignored_users = ["blabla", "user2"]
        self.config.alert_is_vip_only = True
        self.config.alert_minimum_risk_score = UserRiskScoreType.MEDIUM
        self.config.risk_score_increment_alerts = [AlertDetectionType.NEW_COUNTRY, AlertDetectionType.ATYPICAL_COUNTRY]
        self.config.ignored_ips = ["9.9.9.9", "4.5.4.5"]
        self.config.ignored_ISPs = ["isp1"]
        self.config.atypical_country_days = 80
        self.config.user_learning_period = 20
        self.config.save()
        self.config.refresh_from_db()
        # check that new random values have been correctly saved
        self.assertListEqual(self.config.ignored_users, ["blabla", "user2"])
        self.assertTrue(self.config.alert_is_vip_only)
        self.assertEqual(self.config.alert_minimum_risk_score, "Medium")
        self.assertListEqual(self.config.risk_score_increment_alerts, ["New Country", "Atypical Country"])
        self.assertListEqual(self.config.ignored_ips, ["9.9.9.9", "4.5.4.5"])
        self.assertListEqual(self.config.ignored_ISPs, ["isp1"])
        self.assertEqual(self.config.atypical_country_days, 80)
        self.assertEqual(self.config.user_learning_period, 20)
        # call the mgmt command with the --set-default-values option (safe mode)
        call_command("setup_config", "--set-default-values")
        self.config.refresh_from_db()
        # check the corrispondence with the default values (not for already populated fields)
        self.assertListEqual(self.config.ignored_users, ["blabla", "user2"])
        self.assertListEqual(self.config.enabled_users, get_default_enabled_users())
        self.assertListEqual(self.config.vip_users, get_default_vip_users())
        self.assertTrue(self.config.alert_is_vip_only)
        self.assertEqual(self.config.alert_minimum_risk_score, "Medium")
        self.assertListEqual(self.config.risk_score_increment_alerts, [AlertDetectionType.NEW_COUNTRY, AlertDetectionType.ATYPICAL_COUNTRY])
        self.assertListEqual(self.config.ignored_ips, ["9.9.9.9", "4.5.4.5"])
        self.assertListEqual(self.config.allowed_countries, get_default_allowed_countries())
        self.assertListEqual(self.config.ignored_ISPs, ["isp1"])
        self.assertTrue(self.config.ignore_mobile_logins)
        self.assertListEqual(self.config.filtered_alerts_types, get_default_filtered_alerts_types())
        self.assertEqual(self.config.threshold_user_risk_alert, "Medium")
        self.assertEqual(self.config.distance_accepted, settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED)
        self.assertEqual(self.config.vel_accepted, settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED)
        self.assertEqual(self.config.atypical_country_days, 80)
        self.assertEqual(self.config.user_max_days, settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS)
        self.assertEqual(self.config.login_max_days, settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS)
        self.assertEqual(self.config.alert_max_days, settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS)
        self.assertEqual(self.config.ip_max_days, settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS)
        self.assertTrue(self.config.ignored_impossible_travel_all_same_country)
        self.assertEqual(self.config.ignored_impossible_travel_countries_couples, [])
        self.assertEqual(self.config.user_learning_period, 20)

    # === Tests for setup_config.py mgmt command - parse_field_value function ===

    def test_parse_field_value_CommandError(self):
        # Testing the parse_field_value function for the CommandError exception
        # 1. Single element missing "="
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "-a", "ignored_users lorygold")
        self.assertIn("Invalid syntax 'ignored_users lorygold': must be FIELD=VALUE", str(cm.exception))

        # 2. List missing "="
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "-a", "enabled_users [lorygold]")
        self.assertIn("Invalid syntax 'enabled_users [lorygold]': must be FIELD=VALUE", str(cm.exception))

        # 3. Field not existing
        with self.assertRaises(CommandError) as cm:
            call_command("setup_config", "-a", "nonexistent_field=lorygold")
        self.assertIn("Field 'nonexistent_field' does not exist", str(cm.exception))

    def test_parse_field_value_empty_list(self):
        # Testing the parse_field_value function with an empty list
        actual_field, actual_value = parse_field_value("enabled_users=[]")
        self.assertEqual(actual_field, "enabled_users")
        self.assertListEqual(actual_value, [])

    def test_parse_field_value_list_single_value_correct(self):
        # Testing the parse_field_value function with a str values for a list field
        actual_field_str, actual_value_str = parse_field_value("enabled_users=admin")
        self.assertEqual(actual_field_str, "enabled_users")
        self.assertEqual(actual_value_str, "admin")
        actual_field_list, actual_value_list = parse_field_value("ignored_users=[lorygold]")
        self.assertEqual(actual_field_list, "ignored_users")
        self.assertEqual(actual_value_list, ["lorygold"])
        actual_field_list2, actual_value_list2 = parse_field_value('vip_users=["lory", "gold"]')
        self.assertEqual(actual_field_list2, "vip_users")
        self.assertListEqual(actual_value_list2, ["lory", "gold"])

    def test_parse_field_value_list_multiple_values_correct(self):
        # Testing the parse_field_value function with multiple str/regex values for a str list field
        actual_field_list, actual_value_list = parse_field_value("enabled_users=[admin@gmaail.com, lory.gold, pluto123]")
        self.assertEqual(actual_field_list, "enabled_users")
        self.assertEqual(actual_value_list, ["admin@gmaail.com", "lory.gold", "pluto123"])
        actual_field_regex, actual_value_regex = parse_field_value("enabled_users=[*1.@*, *@acompany_name.com, pluto]")
        self.assertEqual(actual_field_regex, "enabled_users")
        self.assertEqual(actual_value_regex, ["*1.@*", "*@acompany_name.com", "pluto"])

    def test_parse_field_value_ignores_empty_values_in_list(self):
        # Testing the parse_field_value function with some empty strings to be ignored
        field, value = parse_field_value("key=[a, , b,,c ]")
        self.assertEqual(field, "key")
        self.assertEqual(value, ["a", "b", "c"])

    def test_parse_field_value_list_with_inner_whitespace(self):
        # Testing the parse_field_value function with inner whitespaces
        field, value = parse_field_value("ips=[ 127.0.0.1 , 192.168.1.1 ]")
        self.assertEqual(field, "ips")
        self.assertEqual(value, ["127.0.0.1", "192.168.1.1"])

    def test_parse_field_value_boolean(self):
        # Testing the parse_field_value function with boolean value
        field_lower, value_lower = parse_field_value("alert_is_vip_only=true")
        self.assertEqual(field_lower, "alert_is_vip_only")
        self.assertTrue(value_lower)
        field_big, value_big = parse_field_value("ignore_mobile_logins=True")
        self.assertEqual(field_big, "ignore_mobile_logins")
        self.assertTrue(value_big)

    def test_parse_field_value_numeric(self):
        # Testing the parse_field_value function with numeric value
        field_integer, value_integer = parse_field_value("distance_accepted=1000")
        self.assertEqual(field_integer, "distance_accepted")
        self.assertEqual(value_integer, 1000)
        field_float, value_float = parse_field_value("vel_accepted=55.7")
        self.assertEqual(field_float, "vel_accepted")
        self.assertEqual(value_float, 55.7)


class ResetUserRiskScoreCommandTests(TestCase):
    def setUp(self):
        User.objects.create(username="alice", risk_score="High")
        User.objects.create(username="bob", risk_score="Low")

    def test_update_single_user_success(self):
        out = io.StringIO()
        call_command("reset_user_risk_score", username="alice", risk_score="Medium", stdout=out)
        alice = User.objects.get(username="alice")
        bob = User.objects.get(username="bob")
        self.assertEqual(alice.risk_score, "Medium")
        # other users unchanged
        self.assertEqual(bob.risk_score, "Low")
        self.assertIn("Successfully updated risk_score for user 'alice' to 'Medium'.", out.getvalue())

    def test_bulk_update_success(self):
        out = io.StringIO()
        call_command("reset_user_risk_score", risk_score="No risk", stdout=out)
        self.assertEqual(User.objects.filter(risk_score="No risk").count(), 2)
        self.assertIn("Successfully updated risk_score for 2 users to 'No risk'.", out.getvalue())

    def test_invalid_risk_score_raises(self):
        with self.assertRaises(CommandError) as cm:
            call_command("reset_user_risk_score", risk_score="invalid-value")
        msg = str(cm.exception)
        self.assertIn("Invalid risk_score 'invalid-value'", msg)
        # ensureing valid values are listed in the error message
        for v in list(UserRiskScoreType.values):
            self.assertIn(v, msg)

    def test_nonexistent_user_raises(self):
        with self.assertRaises(CommandError) as cm:
            call_command("reset_user_risk_score", username="ghost", risk_score="Low")
        self.assertIn("User 'ghost' does not exist", str(cm.exception))

    def test_default_risk_score_used_for_bulk(self):
        out = io.StringIO()
        # default should be 'No risk'
        call_command("reset_user_risk_score", stdout=out)
        self.assertEqual(User.objects.filter(risk_score=UserRiskScoreType.NO_RISK.value).count(), 2)

    def test_single_user_triggers_save(self):
        with patch("impossible_travel.management.commands.reset_user_risk_score.User.save") as mock_save:
            call_command("reset_user_risk_score", username="alice", risk_score="Low")
            self.assertTrue(mock_save.called)

    def test_bulk_update_uses_update_not_save(self):
        with patch("impossible_travel.management.commands.reset_user_risk_score.User.save") as mock_save, patch(
            "impossible_travel.management.commands.reset_user_risk_score.User.objects.update"
        ) as mock_update:
            mock_update.return_value = 2
            out = io.StringIO()
            call_command("reset_user_risk_score", risk_score="Low", stdout=out)
            mock_update.assert_called_once_with(risk_score="Low")
            self.assertFalse(mock_save.called)
            self.assertIn("Successfully updated risk_score for 2 users to 'Low'.", out.getvalue())
