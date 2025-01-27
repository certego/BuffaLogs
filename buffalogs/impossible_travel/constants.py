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
    def get_risk_level(cls, value: int):
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

    @classmethod
    def is_equal_or_higher(cls, threshold, value):
        # check if the value is equal or higher than the threshold
        if UserRiskScoreType.values.index(value) >= UserRiskScoreType.values.index(threshold):
            return True
        return False


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
    ATYPICAL_COUNTRY = "Atypical Country", _("Login from an atypical country")

    @classmethod
    def get_label_from_value(cls, value):
        for item in cls:
            if item.value == value:
                return item.name
        return None


class AlertFilterType(models.TextChoices):
    """Types of possible detection filter applied on alerts to be ignored

    * IGNORED_USER_FILTER: Alert filtered because the user is ignored - the user is in the Config.ignored_users list or Config.enabled_users list is populated
    * IGNORED_IP_FILTER: Alert filtered because the IP is ignored - the ip is in the Config.ignored_ips list
    * ALLOWED_COUNTRY_FILTER: Alert filtered because the country is whitelisted - the country is in the Config.allowed_countries list
    * IS_VIP_FILTER: Alert filtered because the user is not vip - Config.alert_is_vip_only is True and the usre is not in the Config.vip_users list
    * ALERT_MINIMUM_RISK_SCORE_FILTER: Alert filtered because the User.risk_score is lower than the threshold set in Config.alert_minimum_risk_score
    * FILTERED_ALERTS: Alert filtered because this detection type is excluded - the Alert.name detection type is in the Config.filtered_alerts_types list
    * IS_MOBILE_FILTER: Alert filtered because the login is from a mobile device - Config.ignore_mobile_logins is True
    * IGNORED_ISP_FILTER: Alert filtered because the ISP is whitelisted - The ISP is in the Config.ignored_ISPs list
    """

    IGNORED_USER_FILTER = "ignored_users filter", _(
        "Alert filtered because the user is ignored - the user is in the Config.ignored_users list or Config.enabled_users list is populated"
    )
    IGNORED_IP_FILTER = "ignored_ips filter", _("Alert filtered because the IP is ignored - the ip is in the Config.ignored_ips list")
    ALLOWED_COUNTRY_FILTER = "allowed_countries filter", _(
        "Alert filtered because the country is whitelisted - the country is in the Config.allowed_countries list"
    )
    IS_VIP_FILTER = "is_vip_filter", _(
        "Alert filtered because the user is not vip - Config.alert_is_vip_only is True and the usre is not in the Config.vip_users list"
    )
    ALERT_MINIMUM_RISK_SCORE_FILTER = "alert_minimum_risk_score filter", _(
        "Alert filtered because the User.risk_score is lower than the threshold set in Config.alert_minimum_risk_score"
    )
    FILTERED_ALERTS = "filtered_alerts_types filter", _(
        "Alert filtered because this detection type is excluded - the Alert.name detection type is in the Config.filtered_alerts_types list"
    )
    IS_MOBILE_FILTER = "ignore_mobile_logins filter", _("Alert filtered because the login is from a mobile device - Config.ignore_mobile_logins is True")
    IGNORED_ISP_FILTER = "ignored_ISPs filter", _("Alert filtered because the ISP is whitelisted - The ISP is in the Config.ignored_ISPs list")
