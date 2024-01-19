from django.test import TestCase
from django.utils import timezone
from impossible_travel.models import Alert, Login, User
from impossible_travel.modules import login_from_new_country


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
        """Test to check that no new_country alert is sent if a login from that country already exists in the Login model"""
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
        """Test new_country alert to be sent"""
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

    def test_check_country_days_filter(self):
        """Test that checks that if the last new_country alert was triggered before than 30 days, it will be sent again"""
        # insert previous new_country alert with created time > 30 days before
        db_user = User.objects.get(username="Lorena Goldoni")
        new_login = {
            "timestamp": "2023-07-25T12:00:00+00:00",
            "lat": "44.4937",
            "lon": "11.3430",
            "country": "Italy",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        creation_mock_time = timezone.datetime(2023, 7, 25, 12, 0, tzinfo=timezone.utc)
        login = Login.objects.create(
            user=db_user,
            timestamp=new_login["timestamp"],
            latitude=new_login["lat"],
            longitude=new_login["lon"],
            country=new_login["country"],
            user_agent=new_login["user_agent"],
        )
        login.created = creation_mock_time
        login.save()
        alert = Alert.objects.create(
            user_id=db_user.id,
            login_raw_data=new_login,
            name="Login from new country",
            description=f"Login from new country for User: {db_user.username}, at: {new_login['timestamp']}, from: {new_login['country']}",
        )
        # Set a created time before 30 days
        alert.created = creation_mock_time
        alert.save()
        # add new login from Italy that should triggered a new_country alert
        last_login_user_fields = {
            "timestamp": timezone.now(),
            "lat": "44.4937",
            "lon": "11.3430",
            "country": "Italy",
            "user_agent": "Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8",
        }
        alert_result = self.new_country.check_country(db_user, last_login_user_fields)
        # it returns the alert because the last new_country alert from Italy is before 30 days
        self.assertEqual("Login from new country", alert_result["alert_name"].value)
