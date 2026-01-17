from datetime import datetime, timezone
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from impossible_travel.constants import AlertDetectionType, AlertFilterType, UserRiskScoreType
from impossible_travel.models import Alert, Config, User
from impossible_travel.modules import alert_filter


class TestAlertFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        db_user1 = User.objects.create(id=1, username="Lorena Goldoni")
        db_user2 = User.objects.create(id=2, username="Lorygold")
        # force created datetime otherwise the alerts will be filtered by the user_learning_period filter
        db_user1.created = datetime(2025, 10, 1, 12, 34, 37, tzinfo=timezone.utc)
        db_user1.save(update_fields=["created"])
        db_user2.created = datetime(2025, 10, 1, 12, 34, 37, tzinfo=timezone.utc)
        db_user2.save(update_fields=["created"])
        # create an alert for user "Lorena Goldoni"
        Alert.objects.create(
            id=1,
            user=db_user1,
            name=AlertDetectionType.NEW_DEVICE,
            description="Login from new device for User: Lorena Goldoni, at: 2025-01-20T08:00:00.000Z",
            login_raw_data={
                "id": 1,
                "ip": "1.2.3.4",
                "lat": 35.2196,
                "lon": 137.062,
                "agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0",
                "index": "cloud",
                "country": "Italy",
                "organization": "ISP1",
                "timestamp": "2025-01-20T08:00:00.000Z",
            },
        )
        # create an alert for user "Lorygold"
        Alert.objects.create(
            id=2,
            user=db_user2,
            name=AlertDetectionType.NEW_COUNTRY,
            description="Login from new country for User: Aisha Delgado, at: 2025-01-20T08:01:00.000Z, from: Japan",
            login_raw_data={
                "id": 2,
                "ip": "5.6.7.8",
                "lat": 35.2196,
                "lon": 137.062,
                "agent": "Mozilla/5.0 (Linux; Android 13; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
                "index": "cloud",
                "country": "Japan",
                "organization": "ISP2",
                "timestamp": "2025-01-20T08:01:00.000Z",
            },
        )

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Config.objects.all().delete()
        super().tearDownClass()

    def test_match_filters_default_config_values(self):
        # check correct default values population in Config object
        db_config = Config.objects.create(id=1)
        self.assertListEqual(db_config.ignored_users, ["Not Available", "N/A"])
        self.assertEqual(db_config.ignored_users, settings.CERTEGO_BUFFALOGS_IGNORED_USERS)
        self.assertListEqual(db_config.enabled_users, [])
        self.assertEqual(db_config.enabled_users, settings.CERTEGO_BUFFALOGS_ENABLED_USERS)
        self.assertListEqual(db_config.ignored_ips, ["127.0.0.1"])
        self.assertEqual(db_config.ignored_ips, settings.CERTEGO_BUFFALOGS_IGNORED_IPS)
        self.assertListEqual(db_config.ignored_ISPs, [])
        self.assertEqual(db_config.ignored_ISPs, settings.CERTEGO_BUFFALOGS_IGNORED_ISPS)
        self.assertListEqual(db_config.allowed_countries, [])
        self.assertEqual(db_config.allowed_countries, settings.CERTEGO_BUFFALOGS_ALLOWED_COUNTRIES)
        self.assertListEqual(db_config.vip_users, [])
        self.assertEqual(db_config.vip_users, settings.CERTEGO_BUFFALOGS_VIP_USERS)
        self.assertFalse(db_config.alert_is_vip_only)
        self.assertEqual(db_config.alert_minimum_risk_score, "Medium")
        self.assertEqual(db_config.threshold_user_risk_alert, "Medium")
        self.assertListEqual(db_config.filtered_alerts_types, ["User Risk Threshold", "New Device"])
        self.assertTrue(db_config.ignore_mobile_logins)
        self.assertTrue(db_config.ignored_impossible_travel_all_same_country)
        self.assertListEqual(db_config.ignored_impossible_travel_countries_couples, [])
        self.assertEqual(db_config.distance_accepted, 100)
        self.assertEqual(db_config.distance_accepted, settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED)
        self.assertEqual(db_config.vel_accepted, 300)
        self.assertEqual(db_config.vel_accepted, settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED)
        self.assertEqual(db_config.atypical_country_days, 30)
        self.assertEqual(
            db_config.atypical_country_days,
            settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS,
        )
        self.assertEqual(db_config.user_max_days, 60)
        self.assertEqual(db_config.user_max_days, settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS)
        self.assertEqual(db_config.login_max_days, 45)
        self.assertEqual(db_config.login_max_days, settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS)
        self.assertEqual(db_config.alert_max_days, 45)
        self.assertEqual(db_config.alert_max_days, settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS)
        self.assertEqual(db_config.ip_max_days, 45)
        self.assertEqual(db_config.ip_max_days, settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS)
        db_alert1 = Alert.objects.get(id=1)
        # change db_config values to filter alert1
        db_config.alert_minimum_risk_score = UserRiskScoreType.NO_RISK
        db_config.filtered_alerts_types = []
        db_config.ignore_mobile_logins = False
        db_config.threshold_user_risk_alert = UserRiskScoreType.NO_RISK
        db_config.save()
        alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        # self.assertTrue(db_alert1.is_filtered)
        self.assertListEqual([], db_alert1.filter_type)
        db_alert2 = Alert.objects.get(id=2)
        alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        # self.assertTrue(db_alert2.is_filtered)
        self.assertListEqual([], db_alert2.filter_type)

    def test_match_filters_users_ignored(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"]
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            ignore_mobile_logins=False,
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], db_alert.filter_type)
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_users_ignored_regex(self):
        # test with: Config.ignored_users = ["^[\w.-]+@stores\.company\.com$"]
        db_config = Config.objects.create(
            id=1,
            ignored_users=[r"^[\w.-]+@stores\.company\.com$", "Lorena Goldoni"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        db_user = User.objects.create(id=3, username="h.hesse@stores.company.com")
        db_user.created = datetime(2025, 10, 1, 12, 34, 37, tzinfo=timezone.utc)
        db_user.save(update_fields=["created"])
        db_alert = Alert.objects.create(
            id=3,
            user=db_user,
            name=AlertDetectionType.NEW_DEVICE,
            login_raw_data={"test": "ok"},
        )
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], db_alert.filter_type)
        db_user = User.objects.create(id=4, username="test-user123@stores.company.com")
        db_user.created = datetime(2025, 10, 1, 12, 34, 37, tzinfo=timezone.utc)
        db_user.save(update_fields=["created"])
        db_alert = Alert.objects.create(
            id=4,
            user=db_user,
            name=AlertDetectionType.NEW_DEVICE,
            login_raw_data={"test": "ok"},
        )
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        db_user = User.objects.create(id=5, username="hermann@company.com")
        db_user.created = datetime(2025, 10, 1, 12, 34, 37, tzinfo=timezone.utc)
        db_user.save(update_fields=["created"])
        db_alert = Alert.objects.create(
            id=5,
            user=db_user,
            name=AlertDetectionType.NEW_DEVICE,
            login_raw_data={"test": "ok"},
        )
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], db_alert.filter_type)
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_users_enabled_ignored(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"] + Config.enabled_users = ["Lorygold"]
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorygold"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because user not in enabled_users
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], db_alert.filter_type)
        # alert not filtered because user is in enabled_users
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_false(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorygold"],
            vip_users=["Lorena Goldoni"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because user is not in the enabled_users
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], db_alert.filter_type)
        # alert not filtered because user in the enabled_users
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_wrong(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorena Goldoni"],
            vip_users=["Lorygold"],
            alert_is_vip_only=True,
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because user not in vip_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertTrue(db_alert1.is_filtered)
        self.assertListEqual(["is_vip_filter"], db_alert1.filter_type)
        # alert filtered because user not in vip_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertFalse(db_alert2.is_filtered)
        self.assertListEqual([], db_alert2.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_correct1(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorygold"],
            vip_users=["Lorena Goldoni"],
            alert_is_vip_only=True,
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            ignore_mobile_logins=False,
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        db_config.vip_users.append("Lory")
        # alert not filtered because user is in vip_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertFalse(db_alert1.is_filtered)
        self.assertListEqual([], db_alert1.filter_type)
        # alert not filtered because user not in vip_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertTrue(db_alert2.is_filtered)
        self.assertListEqual(["is_vip_filter"], db_alert2.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_correct2(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorygold"],
            vip_users=["Lorena Goldoni"],
            alert_is_vip_only=True,
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            ignore_mobile_logins=False,
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        db_config.vip_users.append("Lorygold")
        db_config.enabled_users.append("Lorena Goldoni")
        # alert filtered because user is in vip_users but not in enabled_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertFalse(db_alert1.is_filtered)
        self.assertListEqual([], db_alert1.filter_type)
        # alert not filtered because user in vip_users and in enabled_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertFalse(db_alert2.is_filtered)
        self.assertListEqual([], db_alert2.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_correct3(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorygold"],
            vip_users=["Lorena Goldoni"],
            alert_is_vip_only=True,
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            ignore_mobile_logins=False,
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        db_config.vip_users.append("Lorygold")
        db_config.enabled_users.extend(["Lorena Goldoni", "Lore"])
        # alert filtered because user is in vip_users but not in enabled_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertFalse(db_alert1.is_filtered)
        self.assertListEqual([], db_alert1.filter_type)
        # alert not filtered because user in vip_users and in enabled_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertFalse(db_alert2.is_filtered)
        self.assertListEqual([], db_alert2.filter_type)

    def test_match_filters_users_minimum_risk_score_filter(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorena Goldoni"],
            vip_users=["Lorena Goldoni"],
            alert_is_vip_only=True,
            alert_minimum_risk_score=UserRiskScoreType.MEDIUM,
            ignore_mobile_logins=False,
            filtered_alerts_types=[],
        )
        # alert not filtered because user risk_score is >= alert_minimum_risk_score
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        db_alert.user.risk_score = UserRiskScoreType.HIGH
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)
        # alert filtered because user not vip and user risk_score is < alert_minimum_risk_score
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["is_vip_filter", "alert_minimum_risk_score filter"], db_alert.filter_type)

    def test_match_filters_location_ignored_ips(self):
        # test filter with: ignored_ips = ["1.2.3.4"]
        db_config = Config.objects.create(
            id=1,
            ignored_ips=["1.2.3.4"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because IP in ignored_ips
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_ips filter"], db_alert.filter_type)
        # alert not filtered because IP not in ignored_ips
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_location_allowed_countries(self):
        # test filter with: allowed_countries = ["Italy"]
        db_config = Config.objects.create(
            id=1,
            allowed_countries=["Italy"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because country in allowed_countries
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["allowed_countries filter"], db_alert.filter_type)
        # alert not filtered because country in allowed_countries
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_devices_ignored_isps(self):
        # test filter with: ignored_ISPs = ["ISP1"]
        db_config = Config.objects.create(
            id=1,
            ignored_ISPs=["ISP1"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because organization ISP in ignored_ISPs
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_ISPs filter"], db_alert.filter_type)
        # alert not filtered because organization ISP not in ignored_ISPs
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_devices_ignore_mobile_logins(self):
        # test filter with: ignore_mobile_logins = True
        db_config = Config.objects.create(
            id=1,
            ignore_mobile_logins=True,
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        # alert not filtered because the agent is not a mobile device
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)
        # alert filtered because the agent is a mobile device
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignore_mobile_logins filter"], db_alert.filter_type)

    def test_match_filters_alerts_filtered_alerts_types(self):
        # test filter with: filtered_alerts_types = ["Imp Travel", "New Device"]
        db_config = Config.objects.create(
            id=1,
            filtered_alerts_types=["Imp Travel", "New Device"],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        # alert filtered because the alert name type is "New Device"
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["filtered_alerts_types filter"], db_alert.filter_type)
        # alert not filtered because the alert name type is "New Country" (not in filtered_alerts_type)
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)

    def test_match_filters_multiple_random_filters(self):
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorygold"],
            enabled_users=["Lorena Goldoni", "Lorygold"],
            vip_users=["Lorena", "Lorygold"],
            alert_is_vip_only=True,
            alert_minimum_risk_score="Medium",
            ignored_ips=["5.6.7.8", "1.2.1.2"],
            allowed_countries=["Italy", "Romania", "UK"],
            ignored_ISPs=["ISP1", "ISP2"],
            ignore_mobile_logins=True,
            filtered_alerts_types=["New Device", "Imp Travel"],
        )
        # alert filtered because: user not in vip_users (and alert_is_vip_only=True)
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        # both lists are correct
        self.assertCountEqual(
            [
                "is_vip_filter",
                "alert_minimum_risk_score filter",
                "allowed_countries filter",
                "ignored_ISPs filter",
                "filtered_alerts_types filter",
            ],
            db_alert.filter_type,
        )
        self.assertCountEqual(
            [
                AlertFilterType.IS_VIP_FILTER,
                AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER,
                AlertFilterType.ALLOWED_COUNTRY_FILTER,
                AlertFilterType.IGNORED_ISP_FILTER,
                AlertFilterType.FILTERED_ALERTS,
            ],
            db_alert.filter_type,
        )
        # alert filtered because: user risk_score: "No Risk" (and alert_minimum_risk_score = "Medium")
        db_alert = Alert.objects.get(user__username="Lorygold")
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        # both lists are correct
        self.assertCountEqual(
            [
                "alert_minimum_risk_score filter",
                "ignored_ips filter",
                "ignored_ISPs filter",
                "ignore_mobile_logins filter",
            ],
            db_alert.filter_type,
        )
        self.assertCountEqual(
            [
                AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER,
                AlertFilterType.IGNORED_IP_FILTER,
                AlertFilterType.IGNORED_ISP_FILTER,
                AlertFilterType.IS_MOBILE_FILTER,
            ],
            db_alert.filter_type,
        )

    def test_match_filters_uaparsed_none_os(self):
        # test with a user_agent that has "None" as os
        db_config = Config.objects.create(id=1)
        none_agent = "Mozilla/5.0 (compatible; MSAL 1.0) PKeyAuth/1.0"
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        db_alert.login_raw_data["agent"] = none_agent
        alert_filter.match_filters(alert=db_alert, app_config=db_config)

    @patch("impossible_travel.modules.detection.update_risk_level")
    def test_match_filters_ignored_impossible_travel_all_same_country(self, mock_update_risk_level):
        # test with ignored_impossible_travel_all_same_country = True
        db_config = Config.objects.create(
            ignored_impossible_travel_all_same_country=True,
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
        )
        db_user = User.objects.get(username="Lorena Goldoni")
        db_alert = Alert.objects.create(
            id=6,
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            description="test",
            login_raw_data={
                "id": "test-1",
                "index": "cloud",
                "ip": "9.10.11.12",
                "lat": 43.3178,
                "lon": -5.4125,
                "country": "Italy",
                "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
                "buffalogs": {
                    "avg_speed": 810,
                    "start_lat": 41.3178,
                    "start_lon": -7.4125,
                    "start_country": "Italy",
                },
                "timestamp": "2025-008-28T09:06:11.000Z",
                "organization": "ISP3",
            },
        )
        self.assertFalse(db_alert.is_filtered)
        self.assertListEqual([], db_alert.filter_type)
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["ignored_all_same_country"], db_alert.filter_type)
        mock_update_risk_level.assert_not_called()

    @patch("impossible_travel.modules.detection.update_risk_level")
    def test_match_filters_ignored_country_couple(self, mock_update_risk_level):
        # test with ignored_country_couple = [["Germany", "Italy"], ["Romania", "Romania"]]
        db_config = Config.objects.create(
            ignored_impossible_travel_all_same_country=False,
            ignored_impossible_travel_countries_couples=[
                ["Germany", "Italy"],
                ["Romania", "Romania"],
            ],
            alert_minimum_risk_score=UserRiskScoreType.NO_RISK,
            filtered_alerts_types=[],
            threshold_user_risk_alert=UserRiskScoreType.NO_RISK,
            ignore_mobile_logins=False,
        )
        db_user = User.objects.get(username="Lorena Goldoni")
        # create alert imp_travel Italy-Italy -> it should be not filtered
        db_alert1 = Alert.objects.create(
            id=7,
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            description="test",
            login_raw_data={
                "id": "test-1",
                "country": "Italy",
                "buffalogs": {"start_country": "Italy"},
                "timestamp": "2025-008-28T09:06:11.000Z",
            },
        )
        self.assertFalse(db_alert1.is_filtered)
        self.assertListEqual([], db_alert1.filter_type)
        alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertFalse(db_alert1.is_filtered)
        self.assertListEqual([], db_alert1.filter_type)
        # create alert imp_travel Germany-Italy -> it should be filtered
        db_alert2 = Alert.objects.create(
            id=8,
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            description="test",
            login_raw_data={
                "id": "test-2",
                "country": "Italy",
                "buffalogs": {"start_country": "Germany"},
                "timestamp": "2025-008-28T09:06:11.000Z",
            },
        )
        alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertTrue(db_alert2.is_filtered)
        self.assertListEqual(["ignored_country_couple"], db_alert2.filter_type)
        # create alert imp_travel Romania-Italy -> it should not be filtered
        db_alert3 = Alert.objects.create(
            id=9,
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            description="test",
            login_raw_data={
                "id": "test-3",
                "country": "Italy",
                "buffalogs": {"start_country": "Romania"},
                "timestamp": "2025-008-28T09:06:11.000Z",
            },
        )
        alert_filter.match_filters(alert=db_alert3, app_config=db_config)
        self.assertFalse(db_alert3.is_filtered)
        self.assertListEqual([], db_alert3.filter_type)
        # create alert imp_travel Romania-Romania -> it should be filtered
        db_alert4 = Alert.objects.create(
            id=10,
            user=db_user,
            name=AlertDetectionType.IMP_TRAVEL,
            description="test",
            login_raw_data={
                "id": "test-3",
                "country": "Romania",
                "buffalogs": {"start_country": "Romania"},
                "timestamp": "2025-008-28T09:06:11.000Z",
            },
        )
        alert_filter.match_filters(alert=db_alert4, app_config=db_config)
        self.assertTrue(db_alert4.is_filtered)
        self.assertListEqual(["ignored_country_couple"], db_alert4.filter_type)
        mock_update_risk_level.assert_not_called()

    @patch("impossible_travel.modules.detection.update_risk_level")
    def test_match_filters_user_learning_period(self, mock_update_risk_level):
        # test default value (14 days) as user behavior learning period
        db_config = Config.objects.create()
        self.assertEqual(14, db_config.user_learning_period)
        db_user = User.objects.create(id=6, username="l_goldoni", risk_score="High")
        db_alert = Alert.objects.create(
            id=8,
            user=db_user,
            login_raw_data={"test": 1},
            name="New Country",
            description="test",
        )
        alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(db_alert.is_filtered)
        self.assertListEqual(["user_learning_period"], db_alert.filter_type)
        # check that if the alert is filtered, the mock_update_risk_level function is not called
        mock_update_risk_level.assert_not_called()
