import logging

from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert
from impossible_travel.modules import impossible_travel

imp_travel = impossible_travel.Impossible_Travel()


class Login_New_Device:
    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def exec_task(self, username):
        self.process_user(username)

    def check_new_device(self, db_user, login_field):
        """
        Check Login from new Device and send alert
        """
        alert_info = {}
        if db_user.login_set.filter(user_agent=login_field["agent"]).count() == 0:
            timestamp = login_field["timestamp"]
            alert_info["alert_name"] = AlertDetectionType.NEW_DEVICE.value
            alert_info["alert_desc"] = f"{AlertDetectionType.NEW_DEVICE.label} for User: {db_user.username}, at: {timestamp}"
            return alert_info
