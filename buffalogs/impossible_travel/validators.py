import re
from ipaddress import AddressValueError, IPv4Address, IPv4Network

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from impossible_travel.views.utils import read_config


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
    Example Config.allowed_countries list: ['Italy', 'Romania']
    Example Config.ignored_impossible_travel_countries_couples list of lists: [['Italy', 'Italy'], ['Italy', 'Spain']]
    Supports both flat lists and lists of pairs (for specific config fields).
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
