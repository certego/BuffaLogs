import re
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from typing import Any, Dict, Optional, Union

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware
from django.utils.translation import gettext_lazy as _
from impossible_travel.constants import AlertTagValues
from impossible_travel.views.utils import read_config

ALLOWED_RISK_STRINGS = ["High", "Medium", "Low", "No Risk"]


def validate_string_or_regex(value):
    """Validator for list models' fields that can contain strings and regex (es. Config.enabled_users list)"""
    if not isinstance(value, list):
        raise ValidationError(f"The value '{value}' must be a list")

    for item in value:
        if not isinstance(item, str):
            raise ValidationError(f"The single element '{item}' in the '{value}' list field must be a string")

        try:
            re.compile(item)
        except re.error:
            raise ValidationError(f"The single element '{item}' in the '{value}' list field is not a valid regex pattern")


def validate_regex_patterns(patterns_list):
    """Validator for regex patterns - rejects unsafe patterns that could cause ReDoS attacks.

    Args:
        patterns_list: List of regex pattern strings

    Raises:
        ValidationError: If any pattern is unsafe
    """
    if not patterns_list:
        return

    if not isinstance(patterns_list, list):
        raise ValidationError("Must be a list of patterns")

    from impossible_travel.modules.alert_filter import _is_safe_regex

    unsafe = [p for p in patterns_list if not _is_safe_regex(p)]
    if unsafe:
        raise ValidationError(
            f"The following regex patterns are unsafe and have been rejected: {unsafe}. "
            "Patterns must not exceed 100 characters, contain more than 50 special characters, "
            "or contain nested quantifiers like (a+)+, (a*)*, or (a|ab)*."
        )


def validate_ips_or_network(value):
    """Validator for models' fields list that must have IPs or networks"""
    for item in value:
        if not isinstance(item, str):
            raise ValidationError(f"The IP address {item} must be a string")
        try:
            IPv4Address(item)
        except AddressValueError:
            try:
                IPv4Network(item)
            except AddressValueError:
                raise ValidationError(f"The IP address {item} is not a valid IP")


def get_valid_country_names():
    """
    Loads country data from countries_list.json and returns a set of valid country names.
    """

    try:
        data = read_config("countries_list.json")
        return set(data.keys())
    except FileNotFoundError:
        return set()


def validate_countries_names(value):
    """
    Validator for country-related fields.
    Ensures all entries are valid ISO 3166-1 country names.
    """
    VALID_COUNTRY_NAMES = get_valid_country_names()

    if not isinstance(value, list):
        raise ValidationError(_("Value must be a list."))

    # Flatten the input if it's a list of lists (example: [['Italy', 'France']])
    flattened = [country for pair in value for country in pair] if all(isinstance(item, list) for item in value) else value

    invalid_entries = [country for country in flattened if country not in VALID_COUNTRY_NAMES]

    if invalid_entries:
        raise ValidationError(_(f"The following country names are invalid: {', '.join(invalid_entries)}"))


def validate_country_couples_list(value):
    """
    Validator for list of lists field containing country-related fields.
    Example Config.ignored_impossible_travel_countries_couples list of lists: [['Italy', 'Italy'], ['Italy', 'Spain']]
    """
    if not isinstance(value, list):
        raise ValidationError(_("Value must be a list."))

    for country_couple in value:
        if not isinstance(country_couple, list) or len(country_couple) != 2:
            raise ValidationError(_("Each single value must be a list of 2 elements (list of lists)."))
        # check that each country is a valid country name
        validate_countries_names(country_couple)


def validate_risk_score(value: Optional[Union[str, int]] = None):
    "Validates risk score value."
    if value is None:
        return None

    if isinstance(value, int) or value.isnumeric():
        value = int(value)
        if not (0 <= value <= 7):
            raise ValidationError("risk score value is out of range. Value must be in the range of 0-7")
    else:
        value = value.title()
        if value not in ALLOWED_RISK_STRINGS:
            raise ValidationError(f"Risk score must be an integer 0-7 or one of: {', '.join(ALLOWED_RISK_STRINGS)}")
    return value


def validate_datetime_str(value: Optional[str] = None):
    if not value:
        return

    dt_obj = parse_datetime(value)
    if dt_obj is None:
        raise ValidationError(f"{value} is not a valid datetime format. Please use ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ).")
    if is_naive(dt_obj):
        dt_obj = make_aware(dt_obj)
    return dt_obj


def validate_boolean_str(value: Optional[str] = None):
    if not value:
        return
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    raise ValidationError(f"Notification status must be true or false, got {value}")


def validate_alert_query(query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Validates the query dictionary of a request to Alert API"""
    try:
        limit = int(query_dict.get("limit", 0))
        offset = int(query_dict.get("offset", 0))
    except ValueError:
        raise ValidationError("Limit/Offset must be valid integers or numeric strings")
    start_date = validate_datetime_str(query_dict.get("start", ""))
    end_date = validate_datetime_str(query_dict.get("end", ""))
    notified = validate_boolean_str(query_dict.get("notified", ""))
    risk_score = validate_risk_score(query_dict.get("risk_score"))
    min_risk_score = validate_risk_score(query_dict.get("min_risk_score"))
    max_risk_score = validate_risk_score(query_dict.get("max_risk_score"))
    is_vip = validate_boolean_str(query_dict.get("is_vip"))

    return dict(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
        notified=notified,
        risk_score=risk_score,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        ip=query_dict.get("ip"),
        name=query_dict.get("name"),
        username=query_dict.get("user"),
        is_vip=is_vip,
        country_code=query_dict.get("country_code"),
        login_start_time=query_dict.get("login_start_date"),
        login_end_time=query_dict.get("login_end_date"),
        user_agent=query_dict.get("user_agent"),
    )


def validate_login_query(query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Validates the query dictionary of a GET request to Login API"""
    try:
        limit = int(query_dict.get("limit", 0))
        offset = int(query_dict.get("offset", 0))
    except ValueError:
        raise ValidationError("Limit/Offset must be valid integers or numeric strings")
    username = query_dict.get("user")
    country = query_dict.get("country")
    login_start_time = query_dict.get("login_start_date")
    login_end_time = query_dict.get("login_end_date")
    ip = query_dict.get("ip")
    user_agent = query_dict.get("user_agent")
    return {
        "limit": limit,
        "offset": offset,
        "username": username,
        "country": country,
        "login_start_time": login_start_time,
        "login_end_time": login_end_time,
        "ip": ip,
        "user_agent": user_agent,
    }


def validate_tags(value):
    """Ensure all tags are valid and unique."""
    if not isinstance(value, list):
        raise ValidationError(_("Tags must be provided as a list."))
    valid_tags = [choice[0] for choice in AlertTagValues.choices]
    invalid = [t for t in value if t not in valid_tags]
    if invalid:
        raise ValidationError(_(f"Invalid tags: {', '.join(invalid)}. Must be one of: {', '.join(valid_tags)}."))
    if len(value) != len(set(value)):
        raise ValidationError(_("Duplicate tags are not allowed."))
