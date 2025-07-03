import logging
from argparse import RawTextHelpFormatter
from typing import Any, Tuple

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields import Field
from impossible_travel.models import Config

logger = logging.getLogger()


def parse_field_value(item: str) -> Tuple[str, Any]:
    """Parse a string of the form FIELD=VALUE or FIELD=[val1,val2]"""
    if "=" not in item:
        raise CommandError(f"Invalid syntax '{item}': must be FIELD=VALUE")

    field, value = item.split("=", 1)
    value = value.strip()

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        parsed = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
    else:
        parsed = value

    return field.strip(), parsed


class Command(BaseCommand):
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
        parser.add_argument("-o", "--override", nargs="+", metavar="FIELD=[VALUES]", help="Override field values")
        parser.add_argument("-r", "--remove", nargs="+", metavar="FIELD=[VALUES]", help="Remove values from list fields")
        parser.add_argument("-a", "--append", nargs="+", metavar="FIELD=[VALUES]", help="Append values to list fields or override non-list")
        parser.add_argument("--set-default-values", action="store_true", help="Reset all Config fields to their defaults")

    def handle(self, *args, **options):
        print(options)
        config, _ = Config.objects.get_or_create(id=1)

        # get customizable fields in the Config model dinamically
        fields_info = {f.name: f for f in Config._meta.get_fields() if isinstance(f, Field) and f.editable and not f.auto_created}

        if options["set_default_values"]:
            # set default values to fields
            for field_name, field_model in list(fields_info.items()):
                if hasattr(field_model, "default"):
                    setattr(config, field_name, field_model.default() if callable(field_model.default) else field_model.default)
            config.save()
            self.stdout.write("Config reset to default values.")
            return

        updates = []

        for mode, items in [("override", options["override"]), ("remove", options["remove"]), ("append", options["append"])]:
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

            # Validate values
            values_to_validate = value if is_list else [value]
            for val in values_to_validate:
                for validator in getattr(field_obj, "validators", []):
                    try:
                        validator(val)
                    except ValidationError as e:
                        raise CommandError(f"Validation error on field '{field}' with value '{val}': {e}")

            # Apply changes
            if is_list:
                current = current or []
                if mode == "append":
                    current += value
                elif mode == "override":
                    current = value
                elif mode == "remove":
                    current = [item for item in current if item not in value]
            else:
                if mode != "override":
                    raise CommandError(f"Field '{field}' is not a list. Use --override to set its value.")
                current = value

            setattr(config, field, current)

        config.save()
        self.stdout.write(self.style.SUCCESS("Config updated successfully."))
