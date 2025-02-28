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
        self.assertEqual(db_config.alert_minimum_risk_score, "No risk")
        self.assertListEqual(db_config.filtered_alerts_types, [])
        self.assertFalse(db_config.ignore_mobile_logins)
        self.assertEqual(db_config.distance_accepted, 100)
        self.assertEqual(db_config.distance_accepted, settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED)
        self.assertEqual(db_config.vel_accepted, 300)
        self.assertEqual(db_config.vel_accepted, settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED)
        self.assertEqual(db_config.atypical_country_days, 30)
        self.assertEqual(db_config.atypical_country_days, settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS)
        self.assertEqual(db_config.user_max_days, 60)
        self.assertEqual(db_config.user_max_days, settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS)
        self.assertEqual(db_config.login_max_days, 45)
        self.assertEqual(db_config.login_max_days, settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS)
        self.assertEqual(db_config.alert_max_days, 45)
        self.assertEqual(db_config.alert_max_days, settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS)
        self.assertEqual(db_config.ip_max_days, 45)
        self.assertEqual(db_config.ip_max_days, settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS)
        db_alert = Alert.objects.get(id=1)
        res_alert = alert_filter.match_filters(alert=db_alert)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_ignored(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"]
        db_config = Config.objects.create(id=1, ignored_users=["Lorena Goldoni", "Lorena"])
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], res_alert.filter_type)
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_ignored_regex(self):
        # test with: Config.ignored_users = ["^[\w.-]+@stores\.company\.com$"]
        db_config = Config.objects.create(id=1, ignored_users=[r"^[\w.-]+@stores\.company\.com$", "Lorena Goldoni"])
        db_user = User.objects.create(id=3, username="h.hesse@stores.company.com")
        db_alert = Alert.objects.create(id=3, user=db_user, name=AlertDetectionType.NEW_DEVICE, login_raw_data={"test": "ok"})
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], res_alert.filter_type)
        db_user = User.objects.create(id=4, username="test-user123@stores.company.com")
        db_alert = Alert.objects.create(id=4, user=db_user, name=AlertDetectionType.NEW_DEVICE, login_raw_data={"test": "ok"})
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        db_user = User.objects.create(id=5, username="hermann@company.com")
        db_alert = Alert.objects.create(id=5, user=db_user, name=AlertDetectionType.NEW_DEVICE, login_raw_data={"test": "ok"})
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], res_alert.filter_type)
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_enabled_ignored(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"] + Config.enabled_users = ["Lorygold"]
        db_config = Config.objects.create(id=1, ignored_users=["Lorena Goldoni", "Lorena"], enabled_users=["Lorygold"])
        # alert filtered because user not in enabled_users
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], res_alert.filter_type)
        # alert not filtered because user is in enabled_users
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_false(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"] + Config.enabled_users = ["Lorygold"], Config.vip_users = ["Lorena Goldoni"] (but Config.alert_is_vip_only=False)
        db_config = Config.objects.create(id=1, ignored_users=["Lorena Goldoni", "Lorena"], enabled_users=["Lorygold"], vip_users=["Lorena Goldoni"])
        # alert filtered because user is not in the enabled_users
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_users filter"], res_alert.filter_type)
        # alert not filtered because user in the enabled_users
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_wrong(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"], Config.enabled_users = ["Lorygold"], Config.vip_users = ["Lorena Goldoni"] + Config.alert_is_vip_only=True (BUT enabled_users != vip_users)
        db_config = Config.objects.create(
            id=1, ignored_users=["Lorena Goldoni", "Lorena"], enabled_users=["Lorygold"], vip_users=["Lorena Goldoni"], alert_is_vip_only=True
        )
        # alert filtered because user is in vip_users but not in enabled_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["is_vip_filter"], res_alert.filter_type)
        # alert filtered because user not in vip_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["is_vip_filter"], res_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_correct1(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"], Config.enabled_users = ["Lorygold"], Config.vip_users = ["Lorena Goldoni", "Lorygold"] + Config.alert_is_vip_only=True (with enabled_users <= vip_users)
        db_config = Config.objects.create(
            id=1, ignored_users=["Lorena Goldoni", "Lorena"], enabled_users=["Lorygold"], vip_users=["Lorena Goldoni"], alert_is_vip_only=True
        )
        db_config.vip_users.append("Lorygold")
        # alert filtered because user is in vip_users but not in enabled_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["is_vip_filter"], res_alert.filter_type)
        # alert not filtered because user in vip_users and in enabled_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_correct2(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"], Config.enabled_users = ["Lorygold", "Lorena Goldoni"], Config.vip_users = ["Lorena Goldoni", "Lorygold"] + Config.alert_is_vip_only=True (with enabled_users == vip_users)
        db_config = Config.objects.create(
            id=1, ignored_users=["Lorena Goldoni", "Lorena"], enabled_users=["Lorygold"], vip_users=["Lorena Goldoni"], alert_is_vip_only=True
        )
        db_config.vip_users.append("Lorygold")
        db_config.enabled_users.append("Lorena Goldoni")
        # alert filtered because user is in vip_users but not in enabled_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)
        # alert not filtered because user in vip_users and in enabled_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_enabled_ignored_vip_true_correct3(self):
        # test filter with: Config.ignored_users = ["Lorena Goldoni", "Lorena"], Config.enabled_users = ["Lorygold", "Lorena Goldoni", "Lore"], Config.vip_users = ["Lorena Goldoni", "Lorygold"] + Config.alert_is_vip_only=True (with enabled_users >= vip_users)
        db_config = Config.objects.create(
            id=1, ignored_users=["Lorena Goldoni", "Lorena"], enabled_users=["Lorygold"], vip_users=["Lorena Goldoni"], alert_is_vip_only=True
        )
        db_config.vip_users.append("Lorygold")
        db_config.enabled_users.extend(["Lorena Goldoni", "Lore"])
        # alert filtered because user is in vip_users but not in enabled_users
        db_alert1 = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert1, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)
        # alert not filtered because user in vip_users and in enabled_users
        db_alert2 = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert2, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_users_minimum_risk_score_filter(self):
        # test filter with: ignored_users = ["Lorena Goldoni", "Lorena"], enabled_users = ["Lorena Goldoni"], vip_users = ["Lorena Goldoni"] + alert_is_vip_only=True + alert_minimum_risk_score = "Medium"
        db_config = Config.objects.create(
            id=1,
            ignored_users=["Lorena Goldoni", "Lorena"],
            enabled_users=["Lorena Goldoni"],
            vip_users=["Lorena Goldoni"],
            alert_is_vip_only=True,
            alert_minimum_risk_score=UserRiskScoreType.MEDIUM,
        )
        # alert not filtered because user risk_score is >= alert_minimum_risk_score
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        db_alert.user.risk_score = UserRiskScoreType.MEDIUM
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)
        # alert filtered because user not vip and user risk_score is < alert_minimum_risk_score
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["is_vip_filter", "alert_minimum_risk_score filter"], res_alert.filter_type)

    def test_match_filters_location_ignored_ips(self):
        # test filter with: ignored_ips = ["1.2.3.4"]
        db_config = Config.objects.create(id=1, ignored_ips=["1.2.3.4"])
        # alert filtered because IP in ignored_ips
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_ips filter"], res_alert.filter_type)
        # alert not filtered because IP not in ignored_ips
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_location_allowed_countries(self):
        # test filter with: allowed_countries = ["Italy"]
        db_config = Config.objects.create(id=1, allowed_countries=["Italy"])
        # alert filtered because country in allowed_countries
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["allowed_countries filter"], res_alert.filter_type)
        # alert not filtered because country in allowed_countries
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_devices_ignored_ISPs(self):
        # test filter with: ignored_ISPs = ["ISP1"]
        db_config = Config.objects.create(id=1, ignored_ISPs=["ISP1"])
        # alert filtered because organization ISP in ignored_ISPs
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignored_ISPs filter"], res_alert.filter_type)
        # alert not filtered because organization ISP not in ignored_ISPs
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_devices_ignore_mobile_logins(self):
        # test filter with: ignore_mobile_logins = True
        db_config = Config.objects.create(id=1, ignore_mobile_logins=True)
        # alert not filtered because the agent is not a mobile device
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)
        # alert filtered because the agent is a mobile device
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["ignore_mobile_logins filter"], res_alert.filter_type)

    def test_match_filters_alerts_filtered_alerts_types(self):
        # test filter with: filtered_alerts_types = ["Imp Travel", "New Device"]
        db_config = Config.objects.create(id=1, filtered_alerts_types=["Imp Travel", "New Device"])
        # alert filtered because the alert name type is "New Device"
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        self.assertListEqual(["filtered_alerts_types filter"], res_alert.filter_type)
        # alert not filtered because the alert name type is "New Country" (not in filtered_alerts_type)
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertFalse(res_alert.is_filtered)
        self.assertListEqual([], res_alert.filter_type)

    def test_match_filters_multiple_random_filters(self):
        # test filter with: ignored_users = ["Lorena Goldoni", "Lorygold"], enabled_users = ["Lorena Goldoni"], vip_users = ["Lorena", "Lorygold"] + alert_is_vip_only=True + alert_minimum_risk_score = "Medium" + ignored_ips = ["5.6.7.8", "1.2.1.2"] + allowed_countries = ["Italy", "Romania", "UK"] + ignored_ISPs = ["ISP1", "ISP2"] + ignore_mobile_logins = True + filtered_alerts_types = ["New Device", "Imp Travel"]
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
        # alert filtered because: user not in vip_users (and alert_is_vip_only=True) + user risk_score: "No Risk" (and alert_minimum_risk_score = "Medium") + country: Italy (and allowed_countries = ["Italy", "Romania", "UK"]) + organization ISP: "ISP1" (and ignored_ISPs = ["ISP1", "ISP2"]) + alert "New Device" (and filtered_alerts_types = ["New Device", "Imp Travel"])
        db_alert = Alert.objects.get(user__username="Lorena Goldoni")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        self.assertTrue(res_alert.is_filtered)
        # both lists are correct
        self.assertCountEqual(
            ["is_vip_filter", "alert_minimum_risk_score filter", "allowed_countries filter", "ignored_ISPs filter", "filtered_alerts_types filter"],
            res_alert.filter_type,
        )
        self.assertCountEqual(
            [
                AlertFilterType.IS_VIP_FILTER,
                AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER,
                AlertFilterType.ALLOWED_COUNTRY_FILTER,
                AlertFilterType.IGNORED_ISP_FILTER,
                AlertFilterType.FILTERED_ALERTS,
            ],
            res_alert.filter_type,
        )
        # alert filtered because: user risk_score: "No Risk" (and alert_minimum_risk_score = "Medium") + alert ip: "5.6.7.8" (and ignored_ips = ["5.6.7.8", "1.2.1.2"]) + organization ISP: "ISP2" (and ignored_ISPs = ["ISP1", "ISP2"]) + user-agent is a mobile device
        db_alert = Alert.objects.get(user__username="Lorygold")
        res_alert = alert_filter.match_filters(alert=db_alert, app_config=db_config)
        # both lists are correct
        self.assertCountEqual(
            ["alert_minimum_risk_score filter", "ignored_ips filter", "ignored_ISPs filter", "ignore_mobile_logins filter"], res_alert.filter_type
        )
        self.assertCountEqual(
            [
                AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER,
                AlertFilterType.IGNORED_IP_FILTER,
                AlertFilterType.IGNORED_ISP_FILTER,
                AlertFilterType.IS_MOBILE_FILTER,
            ],
            res_alert.filter_type,
        )
