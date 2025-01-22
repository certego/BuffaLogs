import logging
import re
from typing import Optional

from django.conf import settings
from impossible_travel.constants import AlertFilterType, UserRiskScoreType
from impossible_travel.models import Alert, Config
from ua_parser import parse


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
        # Detection filters - devices
        if self.alert.login_raw_data.get("organization", "") in self.app_config.ignored_ISPs:
            self.alert.filter_type.append(AlertFilterType.IGNORED_ISP_FILTER)
        if self.app_config.ignore_mobile_logins:
            ua_parsed = parse(self.alert.login_raw_data["agent"])
            if ua_parsed.os.family in settings.CERTEGO_BUFFALOGS_MOBILE_DEVICES:
                self.alert.filter_type.append(AlertFilterType.IS_MOBILE_FILTER)
        # Detection filters - alerts
        if self.alert.name in self.app_config.filtered_alerts_types:
            self.alert.filter_type.append(AlertFilterType.FILTERED_ALERTS)

        # last, set alert.is_filtered if alert.filter_type not empty
        if self.alert.filter_type:
            self.alert.is_filtered = True
        return self.alert

    def _check_users_filters(self):
        """Check all the filters relative to users.
        Rules:
        1. if ignored_users != [] and enabled_users != [] --> enabled_users wins
        2. if ignored_users != [] and enabled_users != [] and vip_users != [] but alert_is_vip_only = False --> enabled_users wins
        3. if ignored_users != [] and enabled_users != [] and vip_users != [] but alert_is_vip_only = True --> vip_users wins, BUT only for vip_users also in the enabled_users list"""
        if self.app_config.alert_is_vip_only:
            if self.user.username not in self.app_config.vip_users or self.user.username not in self.app_config.enabled_users:
                self.logger.debug(f"Alert: {self.alert.id} filtered because user: {self.user.id} not in vip_users and enabled-users Config lists")
                self.alert.filter_type.append(AlertFilterType.IS_VIP_FILTER)  # alert filtered because alert_is_vip_only=True but username not in vip_users list
        else:
            # if alert_is_vip_only=False, check the other users constraints
            if self.app_config.enabled_users and not self._check_username_list_regex(word=self.user.username, values_list=self.app_config.enabled_users):
                self.alert.filter_type.append(
                    AlertFilterType.IGNORED_USER_FILTER
                )  # alert filtered because enabled_users is not empty list and the username is not in that list
                # if enabled_users list is not empty, the ignored_users list will be ignored
            else:
                if self._check_username_list_regex(word=self.user.username, values_list=self.app_config.ignored_users):
                    self.alert.filter_type.append(
                        AlertFilterType.IGNORED_USER_FILTER
                    )  # alert filtered because enabled_users is empty, but the username is in the ignored_users list
        if not UserRiskScoreType.is_equal_or_higher(threshold=self.app_config.alert_minimum_risk_score, value=self.user.risk_score):
            self.alert.filter_type.append(
                AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER
            )  # alert filtered because the user.risk_score level is lower than the config.alert_minimum_risk_score value

    def _check_username_list_regex(self, word: str, values_list: list):
        """Function to check if a string value is inside a list of string or match a regex in the list"""
        for item in values_list:
            if word == item:
                # check if the word is exacly a value in the list
                return True
            else:
                # else, check if the item in the list is a regex that matches the word
                regexp = re.compile(item)
                if regexp.search(word):
                    return True
        return False
