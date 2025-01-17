import logging
from typing import Optional

from impossible_travel.constants import AlertFilterType, UserRiskScoreType
from impossible_travel.models import Alert, Config


class AlertFilter:
    def __init__(self, alert: Alert, logger: Optional[logging.Logger] = None, app_config: Optional[Config] = None) -> None:
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if app_config:
            self.app_config = app_config
        else:
            self.app_config = Config.objects.get(id=1)
        self.alert = alert
        self.user = alert.user

    def match_filters(self) -> Alert:
        # Detection filters - users
        self._check_users_filters()
        # Detection filters - location
        if self.alert.login_raw_data.get("ip", "") in self.app_config.ignored_ips:
            self.alert.filter_type.append(AlertFilterType.IGNORED_IP_FILTER)  # alert filtered because the ip is in the ignored_ips list
        if self.alert.login_raw_data.get("country", "") in self.app_config.allowed_countries:
            self.alert.filter_type.append(AlertFilterType.ALLOWED_COUNTRY_FILTER)  # alert filtered because the country is in the allowed_countries list

        # last, set alert.is_filtered
        if self.alert.filter_type:
            self.alert.is_filtered = True
        return self.alert

    def _check_users_filters(self):
        """Check all the filters relative to users"""
        if self.app_config.alert_is_vip_only:
            if self.user.username not in self.app_config.vip_users:
                self.alert.filter_type.append(AlertFilterType.IS_VIP_FILTER)  # alert filtered because alert_is_vip_only=True but username not in vip_users list
        else:
            # if alert_is_vip_only=False, check the other users constraints
            if self.app_config.enabled_users:
                if self.user.username not in self.app_config.enabled_users:
                    self.alert.filter_type.append(
                        AlertFilterType.IGNORED_USER_FILTER
                    )  # alert filtered because enabled_users is not empty list and the username is not in that list
                # if enabled_users list is not empty, the ignored_users list will be ignored
            else:
                if self.user.username in self.app_config.ignored_users:
                    self.alert.filter_type.append(
                        AlertFilterType.IGNORED_USER_FILTER
                    )  # alert filtered because enabled_users is empty, but the username is in the ignored_users list
        if not UserRiskScoreType.is_equal_or_higher(threshold=self.app_config.alert_minimum_risk_score, value=self.user.risk_score):
            self.alert.filter_type.append(
                AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER
            )  # alert filtered because the user.risk_score level is lower than the config.alert_minimum_risk_score value
