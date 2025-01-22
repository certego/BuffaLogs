import re

from django.core.exceptions import ValidationError


def validate_string_or_regex(value):
    """Validators for list models' fields that can contain strings and regex (es. Config.enabled_users list)"""
    if not isinstance(value, list):
        raise ValidationError(f"The value '{value}' must be a list")

    for item in value:
        if not isinstance(item, str):
            raise ValidationError(f"The single element '{item}' in the '{value}' list field is not a valid string")

        try:
            re.compile(item)
        except re.error:
            raise ValidationError(f"The single element '{item}' in the '{value}' list field is not a valid regex pattern")
