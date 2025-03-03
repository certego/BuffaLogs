import logging
from datetime import datetime

from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Config, User
from impossible_travel.modules import impossible_travel

imp_travel = impossible_travel.Impossible_Travel()


class Login_New_Country:
    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def check_country(self, db_user: User, login_field: dict, app_config: Config) -> dict:
        """
        Check Login from new Country and send alert
        """
        alert_info = {}
        # check "New Country" alert
        if db_user.login_set.filter(country=login_field["country"]).count() == 0:
            alert_info["alert_name"] = AlertDetectionType.NEW_COUNTRY.value
            alert_info["alert_desc"] = (
                f"{AlertDetectionType.NEW_COUNTRY.label} for User: {db_user.username}, at: {login_field['timestamp']}, from: {login_field['country']}"
            )
        # check "Atypical Country" alert
        elif (
            datetime.fromisoformat(login_field["timestamp"]) - db_user.login_set.filter(country=login_field["country"]).last().timestamp
        ).days >= app_config.atypical_country_days:
            alert_info["alert_name"] = AlertDetectionType.ATYPICAL_COUNTRY.value
            alert_info["alert_desc"] = (
                f"{AlertDetectionType.ATYPICAL_COUNTRY.label} for User: {db_user.username}, at: {login_field['timestamp']}, from: {login_field['country']}"
            )
        return alert_info
