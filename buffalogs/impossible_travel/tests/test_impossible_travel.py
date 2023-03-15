from impossible_travel.models import Login, User
from impossible_travel.modules import impossible_travel
from django.test import TestCase


class TestImpossibleTravel(TestCase):
    imp_travel = impossible_travel.Impossible_Travel()

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

    def test_calc_distance(self):
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:10:33.358Z",
            "lat": "14.9876",
            "lon": "24.3456",
            "country": "Sudan",
        }
        db_user = User.objects.get(username="Lorena Goldoni")
        prev_login = Login.objects.get(user_id=db_user.id)
        result = self.imp_travel.calc_distance(db_user, prev_login, last_login_user_fields)
        self.assertIsNone(result)

    def test_calc_distance_alert(self):
        last_login_user_fields = {
            "timestamp": "2023-03-08T17:08:33.358Z",
            "lat": "15.9876",
            "lon": "25.3456",
            "country": "Sudan",
        }
        db_user = User.objects.get(username="Lorena Goldoni")
        prev_login = Login.objects.get(id=db_user.id)
        result = self.imp_travel.calc_distance(db_user, prev_login, last_login_user_fields)
        self.assertEqual("Impossible Travel detected", result["alert_name"].value)

    def test_validate_timestamp(self):
        time = "2023-03-08T17:08:33.358Z"
        result = self.imp_travel.validate_timestamp(time)
        self.assertEqual(2023, result.year)
        self.assertEqual(3, result.month)
        self.assertEqual(8, result.day)
        self.assertEqual(17, result.hour)
        self.assertEqual(8, result.minute)
        self.assertEqual(33, result.second)
        self.assertIsNotNone("UTC", result.tzinfo)

    def test_validate_timestamp_exceptions(self):
        time = "2023-03-08 17:08:33"
        result = self.imp_travel.validate_timestamp(time)
        self.assertEqual(2023, result.year)
        self.assertEqual(3, result.month)
        self.assertEqual(8, result.day)
        self.assertEqual(17, result.hour)
        self.assertEqual(8, result.minute)
        self.assertEqual(33, result.second)
        self.assertIsNotNone("UTC", result.tzinfo)

    def test_validate_timestamp_notvalid(self):
        time = "2023-03-08"
        self.assertRaises(ValueError, self.imp_travel.validate_timestamp, time)
