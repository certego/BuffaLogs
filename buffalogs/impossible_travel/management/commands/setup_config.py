import logging
from argparse import RawTextHelpFormatter
from typing import Any, Tuple

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db.models.fields import Field
from impossible_travel.constants import AlertDetectionType
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


def parse_field_value(item: str) -> Tuple[str, Any]:
    """Parse a string of the form FIELD=VALUE or FIELD=[val1,val2]

    Supports multiple formats:
    - FIELD=value (single value)
    - FIELD=[val1,val2,val3] (list without spaces in values)
    - FIELD=['val 1','val 2'] (list with quoted values containing spaces)
    - FIELD=["val 1","val 2"] (list with double-quoted values)
    - FIELD=[val 1, val 2] (list with spaces, no quotes - legacy support)

    IMPORTANT: When brackets [...] are present, ALWAYS returns a list,
    even for single elements. This is required for ArrayField validation.
    """
    if "=" not in item:
        raise CommandError(f"Invalid syntax '{item}': must be FIELD=VALUE")

    field, value = item.split("=", 1)
    value = value.strip()

    if value.startswith("[") and value.endswith("]"):
        # This is a list - must ALWAYS return a list type
        inner = value[1:-1].strip()
        if not inner:
            # Empty list case: []
            parsed = []
        else:
            # Check if the input has any quotes
            has_quotes = ("'" in inner) or ('"' in inner)

            if has_quotes:
                # Manual parsing for quoted values (handles all cases reliably)
                parsed_values = []
                current = ""
                in_quotes = False
                quote_char = None

                for char in inner:
                    if char in ('"', "'") and (not in_quotes or char == quote_char):
                        in_quotes = not in_quotes
                        quote_char = char if in_quotes else None
                        current += char
                    elif char == "," and not in_quotes:
                        # Found a comma outside quotes - this is a separator
                        if current.strip():
                            parsed_values.append(current.strip())
                        current = ""
                    else:
                        current += char

                # Don't forget the last value
                if current.strip():
                    parsed_values.append(current.strip())

                # Now cast each value (this also strips quotes)
                parsed = [_cast_value(v) for v in parsed_values if v.strip()]
            else:
                # No quotes - split by comma (handles both "a,b,c" and "a, b, c")
                parsed = [_cast_value(v.strip()) for v in inner.split(",") if v.strip()]

        # CRITICAL: Always return a list when brackets are present
        # This ensures ArrayField validators receive the correct type
        return field.strip(), parsed
    else:
        # Single value without brackets - can be a non-list type
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
        ./manage.py setup_config -o allowed_countries=["Italy","Romania"]
        ./manage.py setup_config -r ignored_users=[admin]
        ./manage.py setup_config -a alert_is_vip_only=True
        ./manage.py setup_config -o allowed_countries=["Italy"] -r ignored_users="bot" -r ignored_users=["audit"] -a filtered_alerts_types=["New Device"]

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

            # Validate the value (validators expect the full value, not individual elements)
            for validator in getattr(field_obj, "validators", []):
                try:
                    validator(value)
                except ValidationError as e:
                    # Extract detailed error messages from ValidationError
                    error_details = "; ".join(e.messages) if hasattr(e, "messages") else str(e)
                    raise CommandError(f"Validation error on field '{field}' with value '{value}': {error_details}")

            # Apply changes
            if is_list:
                current = current or []
                if mode == "append":
                    # Only append values that don't already exist (make it idempotent)
                    new_values = [v for v in value if v not in current]
                    current += new_values
                elif mode == "override":
                    current = value
                elif mode == "remove":
                    current = [item for item in current if item not in value]
            else:
                if mode != "override":
                    raise CommandError(f"Field '{field}' is not a list. Use --override to set its value.")
                current = value

            setattr(config, field, current)

        # Validate filtered_alerts_types before saving
        if hasattr(config, "filtered_alerts_types") and config.filtered_alerts_types:
            valid_choices = [choice[0] for choice in AlertDetectionType.choices]
            invalid_values = [val for val in config.filtered_alerts_types if val not in valid_choices]

            if invalid_values:
                raise CommandError(f"Invalid values in 'filtered_alerts_types': {invalid_values}. " f"Valid choices are: {valid_choices}")

        config.save()
        self.stdout.write(self.style.SUCCESS("Config updated successfully."))
