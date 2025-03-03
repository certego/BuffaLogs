from django.test import TestCase
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Config, Login, User
from impossible_travel.modules import login_from_new_country


class TestLoginFromNewCountry(TestCase):

    new_country = login_from_new_country.Login_New_Country()

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(
            username="Lorena Goldoni",
            risk_score="Low",
        )
        user.save()
        login = Login.objects.create(
            user=user,
            timestamp="2023-03-08T17:08:33.358Z",
            latitude=14.5632,
            longitude=24.6542,
            country="Sudan",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",  # pylint: disable=line-too-long
        )
        Config.objects.create(id=1)
        login.save()

    def test_check_country_no_alerts(self):
        # testing function check_country with no alerts
        app_config = Config.objects.get(id=1)
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": 14.9876,
            "lon": 24.3456,
            "country": "Sudan",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        self.assertDictEqual({}, self.new_country.check_country(db_user, last_login_user_fields, app_config))

    def test_check_country_new_country_alert(self):
        # testing function check_country with "New Country" alert
        app_config = Config.objects.get(id=1)
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": 44.4937,
            "lon": 11.3430,
            "country": "Italy",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        alert_result = self.new_country.check_country(db_user, last_login_user_fields, app_config)
        self.assertEqual("New Country", alert_result["alert_name"])
        self.assertEqual(AlertDetectionType.NEW_COUNTRY.value, alert_result["alert_name"])
        self.assertEqual("Login from new country for User: Lorena Goldoni, at: 2023-03-08T17:10:33.358Z, from: Italy", alert_result["alert_desc"])

    def test_check_country_atypical_country_alert(self):
        # testing function check_country with "Atypical Country" alert
        app_config = Config.objects.get(id=1)
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2023-04-18T17:10:33.358Z",
            "lat": 44.4937,
            "lon": 11.3430,
            "country": "Sudan",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        alert_result = self.new_country.check_country(db_user, last_login_user_fields, app_config)
        self.assertEqual("Atypical Country", alert_result["alert_name"])
        self.assertEqual(AlertDetectionType.ATYPICAL_COUNTRY.value, alert_result["alert_name"])
        self.assertEqual("Login from an atypical country for User: Lorena Goldoni, at: 2023-04-18T17:10:33.358Z, from: Sudan", alert_result["alert_desc"])
