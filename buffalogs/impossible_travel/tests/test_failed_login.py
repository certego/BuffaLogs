from django.test import TestCase
from django.utils import timezone
from impossible_travel.models import User, Login # type: ignore


class TestFailedLogin(TestCase):

    def test_failed_login_stored(self):
        u = User.objects.create(username="rohan", risk_score="Low")

        login = Login.objects.create(
            user=u,
            ip="1.2.3.4",
            status="failure",
            failure_reason="invalid_credentials",
            event_id="EV123",
            index="IDX123",
            country="IN",
            timestamp=timezone.now(),
        )

        self.assertEqual(login.status, "failure")
        self.assertEqual(login.failure_reason, "invalid_credentials")
