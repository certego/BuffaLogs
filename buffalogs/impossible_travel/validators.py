import re
from ipaddress import AddressValueError, IPv4Address, IPv4Network

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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
    Loads country data from countries.json and returns a set of valid country names.
    """
    from impossible_travel.views.utils import load_data

    try:
        data = load_data("countries")
        return set(data.keys())
    except FileNotFoundError:
        return set()


def validate_countries_names(value):
    """
    Validator for the allowed_countries field.
    Ensures each entry is a valid ISO 3166-1 country name only.
    """
    VALID_COUNTRY_NAMES = get_valid_country_names()

    if not isinstance(value, list):
        raise ValidationError(_("allowed_countries must be a list."))

    invalid_entries = []
    for country in value:
        if country not in VALID_COUNTRY_NAMES:
            invalid_entries.append(country)

    if invalid_entries:
        readable_invalids = ", ".join(invalid_entries)
        raise ValidationError(_(f"The following entries are not valid country names: {readable_invalids}"))
