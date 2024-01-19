import logging

from django.conf import settings
from django.utils import timezone
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
        send_alert = False
        new_country = login_field["country"]
        if db_user.login_set.filter(country=new_country).count() == 0:
            # alert if there are no logins from that country before
            send_alert = True
        elif db_user.alert_set.filter(name="Login from new country", login_raw_data__country=new_country).exists():
            if (
                abs((timezone.now() - db_user.alert_set.filter(name="Login from new country", login_raw_data__country=new_country).last().created)).days
            ) >= settings.CERTEGO_BUFFALOGS_NEW_COUNTRY_ALERT_FILTER:
                # or... alert if last "new country" alert for that country is older than NEW_COUNTRY_FILTER days
                send_alert = True

        if send_alert is True:
            time = login_field["timestamp"]
            alert_info["alert_name"] = Alert.ruleNameEnum.NEW_COUNTRY
            alert_info["alert_desc"] = f"{alert_info['alert_name']} for User: {db_user.username}, at: {time}, from: {new_country}"
            return alert_info
