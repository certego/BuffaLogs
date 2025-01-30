import logging
import re
from typing import Optional

from django.conf import settings
from impossible_travel.constants import AlertFilterType, UserRiskScoreType
from impossible_travel.models import Alert, Config, User
from ua_parser import parse

logger = logging.getLogger(__name__)


def match_filters(alert: Alert, app_config: Optional[Config] = None) -> Alert:
    if app_config:
        app_config = app_config
    else:
        app_config, _ = Config.objects.get_or_create(id=1)
    db_user = alert.user

    # Detection filters - users
    alert = _check_users_filters(db_alert=alert, app_config=app_config, db_user=db_user)

    # Detection filters - location
    if alert.login_raw_data.get("ip", "") in app_config.ignored_ips:
        logger.debug(
            f"Alert: {alert.id} filtered for user: {db_user.username} because the login IP: {alert.login_raw_data['ip']} is in the ignored_ips Config list"
        )
        alert.filter_type.append(AlertFilterType.IGNORED_IP_FILTER)  # alert filtered because the ip is in the ignored_ips list
    if alert.login_raw_data.get("country", "") in app_config.allowed_countries:
        logger.debug(
            f"Alert: {alert.id} filtered for user: {db_user.username} because the login IP: {alert.login_raw_data['country']} is in the allower_countries Config list"
        )
        alert.filter_type.append(AlertFilterType.ALLOWED_COUNTRY_FILTER)  # alert filtered because the country is in the allowed_countries list

    # Detection filters - devices
    if alert.login_raw_data.get("organization", "") in app_config.ignored_ISPs:
        logger.debug(
            f"Alert: {alert.id} filtered for user: {db_user.username} because the login ISP: {alert.login_raw_data['organization']} is in the ignored_ISPs Config list"
        )
        alert.filter_type.append(AlertFilterType.IGNORED_ISP_FILTER)
    if app_config.ignore_mobile_logins:
        ua_parsed = parse(alert.login_raw_data["agent"])
        if ua_parsed.os.family in settings.CERTEGO_BUFFALOGS_MOBILE_DEVICES:
            logger.debug(
                f"Alert: {alert.id} filtered for user: {db_user.username} because the login user-agent: {alert.login_raw_data['agent']} is a mobile device and Config.ignore_mobile_logins: {app_config.ignore_mobile_logins}"
            )
            alert.filter_type.append(AlertFilterType.IS_MOBILE_FILTER)

    # Detection filters - alerts
    if alert.name in app_config.filtered_alerts_types:
        alert.filter_type.append(AlertFilterType.FILTERED_ALERTS)

    # last, set alert.is_filtered if alert.filter_type not empty
    if alert.filter_type:
        alert.is_filtered = True
    return alert


def _check_users_filters(db_alert: Alert, app_config: Config, db_user: User) -> Alert:
    """Check all the filters relative to users.
    Rules:
    1. if ignored_users != [] and enabled_users != [] --> enabled_users wins
    2. if ignored_users != [] and enabled_users != [] and vip_users != [] but alert_is_vip_only = False --> enabled_users wins
    3. if ignored_users != [] and enabled_users != [] and vip_users != [] but alert_is_vip_only = True --> vip_users wins, BUT only for vip_users also in the enabled_users list
    """
    if app_config.alert_is_vip_only:
        if db_user.username not in app_config.vip_users or db_user.username not in app_config.enabled_users:
            logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} not in vip_users and enabled_users Config lists")
            db_alert.filter_type.append(AlertFilterType.IS_VIP_FILTER)  # alert filtered because alert_is_vip_only=True but username not in vip_users list
    else:
        # if alert_is_vip_only=False, check the other users constraints
        if app_config.enabled_users and not _check_username_list_regex(word=db_user.username, values_list=app_config.enabled_users):
            logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} not in the enabled_users Config list")
            db_alert.filter_type.append(
                AlertFilterType.IGNORED_USER_FILTER
            )  # alert filtered because enabled_users is not empty list and the username is not in that list
        # if enabled_users list is not empty, the ignored_users list will be ignored
        else:
            if _check_username_list_regex(word=db_user.username, values_list=app_config.ignored_users):
                logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} is in the ignored_users Config list")
                db_alert.filter_type.append(
                    AlertFilterType.IGNORED_USER_FILTER
                )  # alert filtered because enabled_users is empty, but the username is in the ignored_users list
    if not UserRiskScoreType.is_equal_or_higher(threshold=app_config.alert_minimum_risk_score, value=db_user.risk_score):
        logger.debug(
            f"Alert: {db_alert.id} filtered because user: {db_user.username} hsa risk_score: {db_user.risk_score}, but Config.alert_minimum_risk_score is set to {app_config.alert_minimum_risk_score}"
        )
        db_alert.filter_type.append(
            AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER
        )  # alert filtered because the user.risk_score level is lower than the config.alert_minimum_risk_score value
    return db_alert


def _check_username_list_regex(word: str, values_list: list) -> bool:
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
