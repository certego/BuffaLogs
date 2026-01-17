from typing import List

import pycountry
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def is_valid_country(value: str) -> bool:
    """
    Check whether a value is a valid ISO2 country code or full country name.
    """
    value = value.strip()

    if not value:
        return False

    # ISO2 country code check
    if pycountry.countries.get(alpha_2=value.upper()):
        return True

    # Full country name check
    try:
        pycountry.countries.lookup(value)
        return True
    except LookupError:
        return False


def validate_countries_names(values: List[str]) -> None:
    """
    Validate a list of country identifiers.

    Accepted values:
    - ISO2 country codes (e.g. "IT", "RO")
    - Full country names (e.g. "Italy", "Nepal")
    """
    if not isinstance(values, list):
        raise ValidationError(_("Value must be a list."))

    invalid_entries: List[str] = []

    for value in values:
        if not isinstance(value, str):
            invalid_entries.append(str(value))
            continue

        if not is_valid_country(value):
            invalid_entries.append(value)

    if invalid_entries:
        raise ValidationError(
            _("The following country identifiers are invalid:")
            % {
                "countries": ", ".join(invalid_entries),
            }
        )
