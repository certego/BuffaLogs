import logging
import re
from argparse import RawTextHelpFormatter
from typing import Any, List, Tuple

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db.models.fields import Field
from impossible_travel.management.commands.base_command import TaskLoggingCommand
from impossible_travel.models import Config

logger = logging.getLogger()


def _cast_value(val: str) -> Any:
    val = val.strip().strip('"').strip("'")
    # Try to cast to int
    if val.isdigit():
        return int(val)
    # Try to cast to float
    try:
        return float(val)
    except ValueError:
        pass
    # Try to cast to boolean
    if val.lower() == "true":
        return True
    elif val.lower() == "false":
        return False
    return val


def _parse_list_values(inner: str) -> List[Any]:
    """Parse comma-separated values, respecting quoted strings.

    Handles values like:
    - 'New Device', 'User Risk Threshold', 'Anonymous IP Login'
    - "New Device", "User Risk Threshold"
    - New Device, User Risk
    - Mixed: 'New Device', "User Risk", Plain Value
    """
    if not inner.strip():
        return []

    # Pattern to match quoted strings (single or double) or unquoted values
    # This regex matches:
    # - Single-quoted strings: 'value with spaces'
    # - Double-quoted strings: "value with spaces"
    # - Unquoted values: value_without_spaces (until comma or end)
    pattern = r"""
        '([^']*)'        |  # Single-quoted string (group 1)
        "([^"]*)"        |  # Double-quoted string (group 2)
        ([^,\[\]'"]+)       # Unquoted value (group 3)
    """

    values = []
    for match in re.finditer(pattern, inner, re.VERBOSE):
        # Get the matched group (whichever one matched)
        value = match.group(1) or match.group(2) or match.group(3)
        if value is not None:
            value = value.strip()
            if value:  # Skip empty values
                values.append(_cast_value(value))

    return values


def parse_field_value(item: str) -> Tuple[str, Any]:
    """Parse a string of the form FIELD=VALUE or FIELD=[val1,val2]

    Supports multiple values for list fields:
    - FIELD=['Value 1', 'Value 2', 'Value 3']
    - FIELD=["Value 1", "Value 2"]
    - FIELD=[Value1, Value2]
    """
    if "=" not in item:
        raise CommandError(f"Invalid syntax '{item}': must be FIELD=VALUE")

    field, value = item.split("=", 1)
    value = value.strip()

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        parsed = _parse_list_values(inner)
    else:
        parsed = _cast_value(value)

    return field.strip(), parsed


class Command(TaskLoggingCommand):
    def create_parser(self, *args, **kwargs):
        config_fields = [f.name for f in Config._meta.get_fields() if isinstance(f, Field) and f.editable and not f.auto_created]

        help_text = f"""
        Update values in the Config model.

        Available fields:
        {', '.join(config_fields)}

        Usage:
        -a FIELD=VALUE    Append VALUE to list field (only for list fields)
        -o FIELD=VALUE    Override value (always for non-list fields)
        -r FIELD=VALUE    Remove the specified VALUE from list values

        Examples:
        # Override with multiple values (use quotes around the entire argument)
        ./manage.py setup_config -o "allowed_countries=['Italy', 'Romania', 'Germany']"

        # Append multiple values to a list field
        ./manage.py setup_config -a "filtered_alerts_types=['New Device', 'User Risk Threshold', 'Anonymous IP Login']"

        # Remove multiple values from a list field
        ./manage.py setup_config -r "ignored_users=['admin', 'bot', 'audit']"

        # Mixed operations
        ./manage.py setup_config -o "allowed_countries=['Italy']" -r "ignored_users=['bot']" -a "filtered_alerts_types=['New Device', 'Impossible Travel']"

        # Non-list field override
        ./manage.py setup_config -a alert_is_vip_only=True

        Note: When passing values with spaces, wrap the entire argument in quotes.

        Additional options:
        --set-default-values   Reset all fields in Config to their default values
        """
        parser = super().create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        parser.description = help_text.strip()
        return parser

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("-o", "--override", action="append", metavar="FIELD=[VALUES]", help="Override field values")
        parser.add_argument("-r", "--remove", action="append", metavar="FIELD=[VALUES]", help="Remove values from list fields")
        parser.add_argument("-a", "--append", action="append", metavar="FIELD=[VALUES]", help="Append values to list fields or override non-list")
        parser.add_argument(
            "--set-default-values", action="store_true", help="Initialize configuration fields with default values (already populated values are not modified)"
        )
        parser.add_argument("--force", action="store_true", help="Force overwrite existing values with defaults (use with caution)")

    def handle(self, *args, **options):
        config, _ = Config.objects.get_or_create(id=1)

        # get customizable fields in the Config model dinamically
        fields_info = {f.name: f for f in Config._meta.get_fields() if isinstance(f, Field) and f.editable and not f.auto_created}

        # MODE: --set-default-values
        if options.get("set_default_values"):
            force = options.get("force", False)
            updated_fields = []

            for field_name, field_model in list(fields_info.items()):
                if hasattr(field_model, "default"):
                    default_value = field_model.default() if callable(field_model.default) else field_model.default
                    current_value = getattr(config, field_name)

                    # Safe mode --> update field only if it's empty
                    if not force:
                        if current_value in (None, "", [], {}):
                            setattr(config, field_name, default_value)
                            updated_fields.append(field_name)
                    # Force mode → overwrite all fields values
                    else:
                        setattr(config, field_name, default_value)
                        updated_fields.append(field_name)

            config.save()

            msg = (
                f"BuffaLogs Config: all {len(updated_fields)} fields reset to defaults (FORCED)."
                if force
                else f"BuffaLogs Config: updated {len(updated_fields)} empty fields with defaults."
            )
            self.stdout.write(self.style.SUCCESS(msg))
            return

        # MODE: manual updates (--override, --append, --remove)
        updates = []

        for mode, items in [
            ("override", options["override"]),
            ("remove", options["remove"]),
            ("append", options["append"]),
        ]:
            if items:
                for item in items:
                    # item is a string "field_name=value" to be parsed
                    field, value = parse_field_value(item)
                    updates.append((field, mode, value))

        for field, mode, value in updates:
            if field not in fields_info:
                raise CommandError(f"Field '{field}' does not exist in Config model.")

            field_obj = fields_info[field]
            is_list = isinstance(field_obj, ArrayField)
            current = getattr(config, field)

            # Normalize value for ArrayFields
            if is_list and not isinstance(value, list):
                value = [value]

            # Apply changes first (before validation)
            if is_list:
                current = current or []
                if mode == "append":
                    new_value = current + value
                elif mode == "override":
                    new_value = value
                elif mode == "remove":
                    new_value = [item for item in current if item not in value]
            else:
                if mode != "override":
                    raise CommandError(f"Field '{field}' is not a list. Use --override to set its value.")
                new_value = value

            # Validate the final computed value
            # For ArrayFields, validators expect the complete list (not individual items)
            for validator in getattr(field_obj, "validators", []):
                try:
                    validator(new_value)
                except ValidationError as e:
                    raise CommandError(f"Validation error on field '{field}' with value '{new_value}': {e}")

            setattr(config, field, new_value)

        config.save()
        self.stdout.write(self.style.SUCCESS("Config updated successfully."))
