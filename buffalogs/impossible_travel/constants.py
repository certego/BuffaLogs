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
    def get_risk_threshold(cls, value: str):
        threshold = {cls.NO_RISK: 0, cls.LOW: 3, cls.MEDIUM: 6, cls.HIGH: 7}
        return threshold[cls(value.strip().title())]

    @classmethod
    def get_risk_level(cls, value: int):
        # map risk value
        if value == 0:
            return cls.NO_RISK.value
        if 1 <= value <= 3:
            return cls.LOW.value
        if 4 <= value <= 6:
            return cls.MEDIUM.value
        if value >= 7:
            return cls.HIGH.value
        raise ValueError("Risk value not valid")

    @classmethod
    def get_range(cls, *, min_value: int | str = None, max_value: int | str = None):
        min_value = min_value or 0
        max_value = max_value or 8
        if isinstance(min_value, str):
            min_value = cls.get_risk_threshold(min_value)
        if isinstance(max_value, str):
            max_value = cls.get_risk_threshold(max_value)
        risk_range = set(cls.get_risk_level(value) for value in range(min_value, max_value))
        return risk_range

    @classmethod
    def compare_risk(cls, threshold, value) -> str:
        """Function to check if the given value (risk_score in string) is lower, equal or higher than a given threshold

        :param threshold: the threshold to exceed
        :type threshold: UserRiskScoreType.value (str)
        :param value: the value to check
        :type value: UserRiskScoreType.value (str)

        :return : "lower", "equal" or "higher"
        :rtype: RiskComparisonType Enum
        """
        if UserRiskScoreType.values.index(value) < UserRiskScoreType.values.index(threshold):
            return ComparisonType.LOWER
        if UserRiskScoreType.values.index(value) == UserRiskScoreType.values.index(threshold):
            return ComparisonType.EQUAL
        return ComparisonType.HIGHER


class AlertDetectionType(models.TextChoices):
    """Types of possible alert detections in the format (name=value,label)

    * NEW_DEVICE: Login from a new user-agent used by the user
    * IMP_TRAVEL: Alert if the user logs into the system from a significant distance in a short time
    * NEW_COUNTRY: The user made a login from a country where they have never logged in before
    * USER_RISK_THRESHOLD: Alert if the user.risk_score value is equal or higher than the Config.alert_minimum_risk_score
    * ANONYMOUS_IP_LOGIN: Alert if the login has been made from an anonymous IP
    * ATYPICAL_COUNTRY: Alert if the login has been made from a country not visited recently
    """

    NEW_DEVICE = "New Device", _("Login from new device")
    IMP_TRAVEL = "Imp Travel", _("Impossible Travel detected")
    NEW_COUNTRY = "New Country", _("Login from new country")
    USER_RISK_THRESHOLD = "User Risk Threshold", _("User risk_score increased")
    ANONYMOUS_IP_LOGIN = "Anonymous IP Login", _("Login from an anonymous IP")
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
    * IS_VIP_FILTER: Alert filtered because the user is not vip - Config.alert_is_vip_only is True and the user is not in the Config.vip_users list
    * ALERT_MINIMUM_RISK_SCORE_FILTER: Alert filtered because the User.risk_score is lower than the threshold set in Config.alert_minimum_risk_score
    * FILTERED_ALERTS: Alert filtered because this detection type is excluded - the Alert.name detection type is in the Config.filtered_alerts_types list
    * IS_MOBILE_FILTER: Alert filtered because the login is from a mobile device - Config.ignore_mobile_logins is True
    * IGNORED_ISP_FILTER: Alert filtered because the ISP is whitelisted - The ISP is in the Config.ignored_ISPs list
    * IGNORED_IMP_TRAVEL_ALL_SAME_COUNTRY:
    * IGNORED_IMP_TRAVEL_COUNTRIES_COUPLE:
    """

    IGNORED_USER_FILTER = "ignored_users filter", _(
        "Alert filtered because the user is ignored - the user is in the Config.ignored_users list or Config.enabled_users list is populated"
    )
    IGNORED_IP_FILTER = "ignored_ips filter", _("Alert filtered because the IP is ignored - the ip is in the Config.ignored_ips list")
    ALLOWED_COUNTRY_FILTER = "allowed_countries filter", _(
        "Alert filtered because the country is whitelisted - the country is in the Config.allowed_countries list"
    )
    IS_VIP_FILTER = "is_vip_filter", _(
        "Alert filtered because the user is not vip - Config.alert_is_vip_only is True and the user is not in the Config.vip_users list"
    )
    ALERT_MINIMUM_RISK_SCORE_FILTER = "alert_minimum_risk_score filter", _(
        "Alert filtered because the User.risk_score is lower than the threshold set in Config.alert_minimum_risk_score"
    )
    FILTERED_ALERTS = "filtered_alerts_types filter", _(
        "Alert filtered because this detection type is excluded - the Alert.name detection type is in the Config.filtered_alerts_types list"
    )
    IS_MOBILE_FILTER = "ignore_mobile_logins filter", _("Alert filtered because the login is from a mobile device - Config.ignore_mobile_logins is True")
    IGNORED_ISP_FILTER = "ignored_ISPs filter", _("Alert filtered because the ISP is whitelisted - The ISP is in the Config.ignored_ISPs list")
    IGNORED_IMP_TRAVEL_ALL_SAME_COUNTRY = "ignored_all_same_country", _(
        "Alert filtered because impossible travel alerts with the same origin and destination country are configured to be ignored (Config.ignored_impossible_travel_all_same_country)"
    )
    IGNORED_IMP_TRAVEL_COUNTRIES_COUPLE = "ignored_country_couple", _(
        "Alert filtered because the specific origin–destination country pair is listed in the configuration, regardless of order (Config.ignored_impossible_travel_countries_couples)"
    )


class ComparisonType(models.TextChoices):
    """Types of possible results in some comparisons

    * LOWER: the value is lower than the given threshold
    * EQUAL: the value and the given threshold are equal
    * HIGHER: the value is higher than the given threshold
    """

    LOWER = "lower", _("The value is lower than the given threshold")
    EQUAL = "equal", _("The value and the given threshold are equal")
    HIGHER = "higher", _("The value is higher than the given threshold")
