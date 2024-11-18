import logging

from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert
from impossible_travel.modules import impossible_travel

imp_travel = impossible_travel.Impossible_Travel()


class Login_New_Country:
    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def check_country(self, db_user, login_field):
        """
        Check Login from new Country and send alert
        """
        alert_info = {}
        new_country = login_field["country"]
        if db_user.login_set.filter(country=new_country).count() == 0:
            time = login_field["timestamp"]
            alert_info["alert_name"] = AlertDetectionType.NEW_COUNTRY.value
            alert_info["alert_desc"] = f"{alert_info['alert_name']} for User: {db_user.username}, at: {time}, from: {new_country}"
            return alert_info
