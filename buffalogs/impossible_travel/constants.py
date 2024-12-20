from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRiskScoreType(models.TextChoices):
    """Possible types of user risk scores, based on number of alerts that they have triggered

    * No risk: the user has triggered 0 alerts
    * Low: the user has triggered 1 or 2 alerts
    * Medium: the user has triggered 3 or 4 alerts
    * High: the user has triggered more than 4 alerts
    """

    NO_RISK = "No risk", _("User has no risk")
    LOW = "Low", _("User has a low risk")
    MEDIUM = "Medium", _("User has a medium risk")
    HIGH = "High", _("User has a high risk")

    @classmethod
    def get_risk_level(cls, value):
        # map risk value
        if value == 0:
            return cls.NO_RISK.value
        elif 1 <= value <= 2:
            return cls.LOW.value
        elif 3 <= value <= 4:
            return cls.MEDIUM.value
        elif value >= 5:
            return cls.HIGH.value
        else:
            raise ValueError("Risk value not valid")


class AlertDetectionType(models.TextChoices):
    """Types of possible alert detections in the format (name=value,label)

    * NEW_DEVICE: Login from a new user-agent used by the user
    * IMP_TRAVEL: Alert if the user logs into the system from a significant distance () within a range of time that cannot be covered by conventional means of transport
    * NEW_COUNTRY: The user made a login from a country where they have never logged in before
    * USER_RISK_THRESHOLD: Alert if the user.risk_score value is equal or higher than the Config.alert_minimum_risk_score
    * LOGIN_ANONYMIZER_IP: Alert if the login has been made from an anonymizer IP
    * ATYPICAL_COUNTRY: Alert if the login has been made from a country not visited recently
    """

    NEW_DEVICE = "New Device", _("Login from new device")
    IMP_TRAVEL = "Imp Travel", _("Impossible Travel detected")
    NEW_COUNTRY = "New Country", _("Login from new country")
    USER_RISK_THRESHOLD = "User Risk Threshold", _("User risk higher than threshold")
    LOGIN_ANONYMIZER_IP = "Login Anonymizer Ip", _("Login from an anonymizer IP")
    ATYPICAL_COUNTRY = "Atypical Country", _("Login from a country not visited recently")

    @classmethod
    def get_label_from_value(cls, value):
        for item in cls:
            if item.value == value:
                return item.name
        return None


class AlertFilterType(models.TextChoices):
    """Types of possible detection filter applied on alerts to be ignored

    * ISP_FILTER: exclude from the detection a list of whitelisted ISP
    * IS_MOBILE_FILTER: if Config.ignore_mobile_logins flag is checked, exclude from the detection the mobile devices
    * IS_VIP_FILTER: if Config.alert_is_vip_only flag is checked, only the vip users (in the Config.vip_users list) send alerts
    * ALLOWED_COUNTRY_FILTER: if the country of the login is in the Config.allowed_countries list, the alert isn't sent
    * IGNORED_USER_FILTER: if the user is in the Config.ignored_users list OR the user is not in the Config.enabled_users list, the alert isn't sent
    * ALERT_MINIMUM_RISK_SCORE_FILTER: if the user hasn't, at least, a User.risk_score equals to the one sets in Config.alert_minimum_risk_score,
    * FILTERED_ALERTS: if the alert type (AlertDetectionType) is in the Config.filtered_alerts, the alert isn't sent
    """

    ISP_FILTER = "isp_filter", _("Alert filtered because the ISP is whitelisted")
    IS_MOBILE_FILTER = "is_mobile_filter", _("Alert filtered because login from a mobile device")
    IS_VIP_FILTER = "is_vip_filter", _("Alert filtered because the user is not vip")
    ALLOWED_COUNTRY_FILTER = "allowed_country_filter", _("Alert filtered because the country is whitelisted")
    IGNORED_USER_FILTER = "ignored_user_filter", _("Alert filtered because the user is ignored")
    ALERT_MINIMUM_RISK_SCORE_FILTER = "alert_minimum_risk_score_filter", _("Alert filtered because the risk_score is lower than the threshold")
    FILTERED_ALERTS = "filtered_alerts", _("Alert filtered because this detection type is excluded")
