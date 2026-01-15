import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from django.conf import settings
from impossible_travel.constants import (
    AlertDetectionType,
    AlertFilterType,
    ComparisonType,
    UserRiskScoreType,
)
from impossible_travel.models import Alert, Config, User
from impossible_travel.validators import _is_safe_regex
from ua_parser import parse

logger = logging.getLogger(__name__)


def match_filters(alert: Alert, app_config: Config) -> Alert:
    db_user = alert.user

    # Detection filters - users
    alert = _update_users_filters(db_alert=alert, app_config=app_config, db_user=db_user)

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
    if app_config.ignore_mobile_logins and alert.login_raw_data.get("agent", ""):
        ua_parsed = parse(alert.login_raw_data["agent"])
        if ua_parsed.os and ua_parsed.os.family in settings.CERTEGO_BUFFALOGS_MOBILE_DEVICES:
            logger.debug(
                f"Alert: {alert.id} filtered for user: {db_user.username} because the login user-agent: {alert.login_raw_data['agent']} is a mobile device and Config.ignore_mobile_logins: {app_config.ignore_mobile_logins}"
            )
            alert.filter_type.append(AlertFilterType.IS_MOBILE_FILTER)

    # Detection filters - alerts
    if alert.name in app_config.filtered_alerts_types:
        alert.filter_type.append(AlertFilterType.FILTERED_ALERTS)

    if alert.name == AlertDetectionType.IMP_TRAVEL:
        # check ignored_impossible_travel_countries_couples and ignored_impossible_travel_all_same_country config filters
        if app_config.ignored_impossible_travel_all_same_country and alert.login_raw_data["country"] == alert.login_raw_data["buffalogs"]["start_country"]:
            alert.filter_type.append(AlertFilterType.IGNORED_IMP_TRAVEL_ALL_SAME_COUNTRY)
        couple_country = [
            alert.login_raw_data["country"],
            alert.login_raw_data["buffalogs"]["start_country"],
        ]
        # using Counter to ignore the order: ["Italy", "Germany"] == ["Germany", "Italy"] and check only if the coutry couple is present in the ignored couples
        for ignored_country_couple in app_config.ignored_impossible_travel_countries_couples:
            if Counter(ignored_country_couple) == Counter(couple_country):
                alert.filter_type.append(AlertFilterType.IGNORED_IMP_TRAVEL_COUNTRIES_COUPLE)

    alert.save()


def _update_users_filters(db_alert: Alert, app_config: Config, db_user: User) -> Alert:
    """Check all the filters relative to users (enabled_users, ignored_users, vip_users).
    Rules of alert filtering, in the check order:
    1. if Config.alert_is_vip_only == True
        a. if user not in [Config.vip_users] --> IS_VIP_FILTER
    else:
    2. if Config.enabled_users != []
        b. if user not in [Config.enabled_users] --> IGNORED_USER_FILTER
      3. else: if user in [Config.ignored_users] --> IGNORED_USER_FILTER
    4. if user.risk_score < Config.alert_minimum_risk_score --> ALERT_MINIMUM_RISK_SCORE_FILTER
    5. if now-user.created < Config.user_learning_period --> USER_LEARNING_PERIOD
    """
    now = datetime.now(timezone.utc)

    if app_config.alert_is_vip_only:
        # 1. if the flag Config.is_vip_only is True, check only if the user is in the config.vip_users list
        if db_user.username not in app_config.vip_users:
            logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} not in vip_users and enabled_users Config lists")
            db_alert.filter_type.append(AlertFilterType.IS_VIP_FILTER)  # alert filtered because alert_is_vip_only=True but username not in vip_users list
    else:
        if app_config.enabled_users and not _check_username_list_regex(word=db_user.username, values_list=app_config.enabled_users):
            # 2. alert filtered because the user is not in the enabled_users list
            logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} not in the enabled_users Config list")
            db_alert.filter_type.append(AlertFilterType.IGNORED_USER_FILTER)
        else:
            if _check_username_list_regex(word=db_user.username, values_list=app_config.ignored_users):
                # 3. if the user is in the Config.ignored_users list, the user is immediately ignored
                logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} is in the ignored_users Config list")
                db_alert.filter_type.append(AlertFilterType.IGNORED_USER_FILTER)

    # 4. check that if the user has a risk_score lower than the alert_minimum_risk_score threshold filter, the alert is filtered
    if UserRiskScoreType.compare_risk(threshold=app_config.alert_minimum_risk_score, value=db_user.risk_score) == ComparisonType.LOWER:
        logger.debug(
            f"Alert: {db_alert.id} filtered because user: {db_user.username} has risk_score: {db_user.risk_score}, but Config.alert_minimum_risk_score is set to {app_config.alert_minimum_risk_score}"
        )
        db_alert.filter_type.append(AlertFilterType.ALERT_MINIMUM_RISK_SCORE_FILTER)
    # 5. check if the User is quite new in the BuffaLogs system, so if the learning period has to be completed yet
    if (now - db_user.created) < timedelta(days=app_config.user_learning_period):
        logger.debug(f"Alert: {db_alert.id} filtered because user: {db_user.username} is still into the learning period")
        db_alert.filter_type.append(AlertFilterType.USER_LEARNING_PERIOD)
    return db_alert


def _check_username_list_regex(word: str, values_list: list) -> bool:
    """
    Function to check if a string value is inside a list of strings or matches a regex in the list.
    Includes ReDoS protection through pattern validation.

    Args:
        word: String to check
        values_list: List of strings or regex patterns

    Returns:
        True if word matches any item in the list, False otherwise
    """
    for item in values_list:
        # First, try exact match (fast path)
        if word == item:
            return True

        # Validate regex pattern before compilation
        if not _is_safe_regex(item):
            logger.warning(f"Skipping unsafe or invalid regex pattern: {item[:50]}...")
            continue

        try:
            # Compile and search with validated pattern
            regexp = re.compile(item)
            if regexp.search(word):
                return True
        except re.error as e:
            logger.error(f"Invalid regex pattern '{item}': {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing regex '{item}': {e}")
            continue

    return False
