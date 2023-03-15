from django.test import TestCase
from impossible_travel.models import Login, User
from impossible_travel.modules import impossible_travel, login_from_new_country


class TestLoginFromNewCountry(TestCase):

    new_country = login_from_new_country.Login_New_Country()

    @classmethod
    def setUpTestData(self):
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
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
        )
        login.save()

    def test_check_country(self):
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "14.9876",
            "lon": "24.3456",
            "country": "Sudan",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        self.assertIsNone(self.new_country.check_country(db_user, last_login_user_fields))

    def test_check_country_alert(self):
        db_user = User.objects.get(username="Lorena Goldoni")
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "44.4937",
            "lon": "11.3430",
            "country": "Italy",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        alert_result = self.new_country.check_country(db_user, last_login_user_fields)
        self.assertEqual("Login from new country", alert_result["alert_name"].value)
