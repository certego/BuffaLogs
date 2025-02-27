import re
from ipaddress import AddressValueError, IPv4Address, IPv4Network

from django.core.exceptions import ValidationError


def validate_string_or_regex(value):
    """Validator for list models' fields that can contain strings and regex (es. Config.enabled_users list)"""
    if not isinstance(value, list):
        raise ValidationError(f"The value '{value}' must be a list")

    for item in value:
        if not isinstance(item, str):
            raise ValidationError(
                f"The single element '{item}' in the '{value}' list field must be a string"
            )

        try:
            re.compile(item)
        except re.error:
            raise ValidationError(
                f"The single element '{item}' in the '{value}' list field is not a valid regex pattern"
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
