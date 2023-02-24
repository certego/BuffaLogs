import logging

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
        Check Login from new Device
        """
        alert_info = {}
        if db_user.login_set.filter(user_agent=login_field["agent"]).count() == 0:
            timestamp_validated = imp_travel.validate_timestamp(login_field["timestamp"])
            alert_info["alert_name"] = Alert.ruleNameEnum.NEW_DEVICE
            alert_info[
                "alert_desc"
            ] = f"LOGIN FROM NEW DEVICE\
                for User: {db_user.username},\
                at: {timestamp_validated}"
            return alert_info
