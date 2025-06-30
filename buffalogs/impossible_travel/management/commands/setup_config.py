import logging
from argparse import RawTextHelpFormatter
from typing import Any, Tuple

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields import Field
from impossible_travel.models import Config

logger = logging.getLogger()


def parse_field_value(item: str) -> Tuple[str, Any]:
    """
    Parse a string of the form FIELD=VALUE or FIELD=[val1,val2] into a tuple.

    :param item: string like 'field=value' or 'field=[val1,val2]'
    :return: tuple(field, parsed_value)
    """
    if "=" not in item:
        raise CommandError(f"Invalid syntax '{item}': must be FIELD=VALUE")

    field, value = item.split("=", 1)
    value = value.strip()

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if inner:
            parsed = [v.strip() for v in inner.split(",") if v.strip()]
        else:
            parsed = []
    else:
        parsed = value

    return field.strip(), parsed


def normalize_choice_value(field, input_value):
    """
    Normalize input_value to one of the choices defined in the field.

    Raises CommandError if no match found.
    """
    choices = getattr(field, "choices", None)
    if not choices:
        return input_value

    choice_map = {str(choice[0]).lower(): choice[0] for choice in choices}
    key = str(input_value).lower()

    if key not in choice_map:
        raise CommandError(f"Invalid choice '{input_value}' for field '{field.name}'. " f"Valid choices: {[c[0] for c in choices]}")
    return choice_map[key]


def validate_value_with_validators(field, value):
    """
    Validate a value or list of values with the field's validators.

    Raises CommandError if validation fails.
    """
    validators = getattr(field, "validators", [])
    if not validators:
        return

    values = value if isinstance(value, list) else [value]

    for val in values:
        for validator in validators:
            try:
                validator(val)
            except ValidationError as e:
                raise CommandError(f"Validation error for field '{field.name}' with value '{val}': {e}")


class Command(BaseCommand):
    def create_parser(self, *args, **kwargs):
        # Get all editable fields in Config model dynamically
        config_fields = [f.name for f in Config._meta.get_fields() if isinstance(f, Field) and f.editable and not f.auto_created]

        help_text = f"""
        Update one or more values in the Config model.

        Available fields:
        {', '.join(config_fields)}

        Usage:
        -a FIELD=VALUE    (default for list fields) Append VALUE to the list field
        -o FIELD=VALUE    Override the field with the specified VALUE (default for non-list fields)
        -r FIELD=VALUE    Remove VALUE from the list field

        Examples:
        ./manage.py setup_config -o allowed_countries=[IT,RO]
        ./manage.py setup_config -r ignored_users=[admin]
        ./manage.py setup_config alert_is_vip_only=True
        ./manage.py setup_config -o allowed_countries=[IT] -r ignored_users=[bot] ignored_users=audit

        Additional options:
        --set-default-values   Reset all fields in Config to their default values
        """
        parser = super().create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        parser.description = help_text.strip()
        return parser

    def add_arguments(self, parser):
        parser.add_argument("-o", "--override", nargs="+", metavar="FIELD=[VALUES]", help="Override specified fields")
        parser.add_argument("-r", "--remove", nargs="+", metavar="FIELD=[VALUES]", help="Remove values from specified list fields")
        parser.add_argument(
            "append", nargs="*", metavar="FIELD=VALUE", help="Append values to specified list fields (default for list fields), override for others"
        )
        parser.add_argument("--set-default-values", action="store_true", help="Reset all fields in Config to their default values")

    def handle(self, *args, **options):
        config, _ = Config.objects.get_or_create(id=1)

        if options.get("set_default_values"):
            # Reset all fields to their default values
            for field in Config._meta.get_fields():
                if not isinstance(field, Field) or field.auto_created or not field.editable:
                    continue
                # Use default value or default callable if any
                if callable(field.default):
                    default_value = field.default()
                else:
                    default_value = field.default
                setattr(config, field.name, default_value)
            config.save()
            self.stdout.write(self.style.SUCCESS("Config reset to default values successfully."))
            return

        updates = []

        # Collect all updates from override, remove, append
        for mode, items in [
            ("override", options.get("override")),
            ("remove", options.get("remove")),
            ("append", options.get("append")),
        ]:
            if not items:
                continue
            for item in items:
                field, value = parse_field_value(item)
                updates.append((field, mode, value))

        for field, mode, value in updates:
            if not hasattr(config, field):
                raise CommandError(f"Field '{field}' does not exist in Config model.")

            field_obj = Config._meta.get_field(field)
            current = getattr(config, field)

            # Normalize choices
            if getattr(field_obj, "choices", None):
                if isinstance(value, list):
                    value = [normalize_choice_value(field_obj, v) for v in value]
                else:
                    value = normalize_choice_value(field_obj, value)

            # Validate with validators if any
            validate_value_with_validators(field_obj, value)

            is_list_field = hasattr(field_obj, "base_field")  # True for ArrayField

            # If mode is append but field is not a list, error
            if mode == "append" and not is_list_field:
                raise CommandError(f"Append (-a) operation allowed only on list fields, '{field}' is not a list.")

            # Apply update depending on field type and mode
            if is_list_field:
                current = current or []
                if mode == "append":
                    if isinstance(value, list):
                        current += value
                    else:
                        current.append(value)
                elif mode == "override":
                    current = value if isinstance(value, list) else [value]
                elif mode == "remove":
                    to_remove = value if isinstance(value, list) else [value]
                    current = [item for item in current if item not in to_remove]
            else:
                # Non-list fields support only override
                if mode != "override":
                    raise CommandError(f"Only override (-o) allowed for non-list fields like '{field}'.")
                current = value

            setattr(config, field, current)

        config.save()
        self.stdout.write(self.style.SUCCESS("Config updated successfully."))
