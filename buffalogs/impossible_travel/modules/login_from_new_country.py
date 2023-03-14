import logging

from impossible_travel.models import Alert
from impossible_travel.modules import impossible_travel

imp_travel = impossible_travel.Impossible_Travel()


class Login_New_Country:
    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def check_country(self, db_user, login_field):
        """Check Login from new Country

        :param db_user: user from db    
        :type db_user: object
        :param login_field: dictionary login from elastic
        :type login_field: dict
        :return: a dict representing this alert
        :rtype: dict
        """
        alert_info = {}
        if db_user.login_set.filter(country=login_field["country"]).count() == 0:
            timestamp_validated = imp_travel.validate_timestamp(login_field["timestamp"])
            alert_info["alert_name"] = Alert.ruleNameEnum.NEW_COUNTRY
            alert_info[
                "alert_desc"
            ] = f"{alert_info['alert_name']}\
                for User: {db_user.username},\
                at: {timestamp_validated}"
            return alert_info
