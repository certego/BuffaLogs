from django.test import TestCase
from impossible_travel.models import Config
from impossible_travel.utils.utils import check_ignored_ips


class TestTasks(TestCase):
    def test_check_ignored_ips(self):
        Config.objects.create(ignored_ips=["0.0.0.0", "192.168.1.0/27", "172.16.1.0/24"])
        self.assertTrue(check_ignored_ips("0.0.0.0"))
        self.assertTrue(check_ignored_ips("192.168.1.15"))
        self.assertTrue(check_ignored_ips("172.16.1.100"))
        self.assertFalse(check_ignored_ips("1.2.3.4"))
        self.assertFalse(check_ignored_ips("192.168.2.1"))
        self.assertTrue(check_ignored_ips(None))
        self.assertTrue(check_ignored_ips("192.168.1.XXX"))
