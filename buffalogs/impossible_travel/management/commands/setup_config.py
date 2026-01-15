import logging
import pycountry

from argparse import RawTextHelpFormatter
from typing import Any, Iterable, List, Sequence, Tuple

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db.models.fields import Field
from impossible_travel.management.commands.base_command import TaskLoggingCommand
from impossible_travel.models import Config


logger = logging.getLogger()

def _normalize_country_payload(values):
    """
    Accepts ISO2 or full country names and always returns ISO2 codes.
    """
    import pycountry

    normalized = []
    for value in values:
        value = value.strip()

        # Already ISO2
        if len(value) == 2 and value.isalpha():
            normalized.append(value.upper())
            continue

        # Try resolving full name → ISO2
        try:
            country = pycountry.countries.lookup(value)
            normalized.append(country.alpha_2)
        except LookupError:
            normalized.append(value)

    return normalized


def _normalize_country_values(values: list[str]) -> list[str]:
    normalized = []
    for v in values:
        country = pycountry.countries.get(alpha_2=v.upper())
        normalized.append(country.name if country else v)
    return normalized

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
    """Parse a string of the form FIELD=VALUE or FIELD=[val1,val2]"""
    if "=" not in item:
        raise CommandError(f"Invalid syntax '{item}': must be FIELD=VALUE")

    field, value = item.split("=", 1)
    value = value.strip()

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        parsed = [_cast_value(v) for v in inner.split(",") if v.strip()]
    else:
        parsed = _cast_value(value)

    return field.strip(), parsed


OPTION_DISPLAY = {
    "override": "-o/--override",
    "remove": "-r/--remove",
    "append": "-a/--append",
}


def parse_option_group(raw_values: Sequence[str], mode: str) -> Tuple[str, Any, List[Any]]:
    if not raw_values:
        raise CommandError("Missing FIELD=VALUE argument.")

    # argparse returns nested lists when using nargs="+"; normalize here
    if isinstance(raw_values, str):
        values = [raw_values]
    else:
        values = list(raw_values)

    field, value = parse_field_value(values[0])

    additional_values = []
    for extra in values[1:]:
        if "=" in extra:
            flag = OPTION_DISPLAY.get(mode, "the same option")
            raise CommandError(f"Invalid syntax '{extra}'. Each FIELD=VALUE must be preceded by {flag}.")
        additional_values.append(_cast_value(extra))

    return field, value, additional_values


def _deduplicate_preserving_order(values: Iterable[Any]) -> List[Any]:
    result: List[Any] = []
    for item in values:
        if item not in result:
            result.append(item)
    return result


def _normalize_list_payload(value: Any, extra_values: Sequence[Any]) -> List[Any]:
    normalized: List[Any] = []

    def _append_if_valid(val: Any):
        if isinstance(val, str):
            trimmed = val.strip()
            if not trimmed:
                return
            normalized.append(trimmed)
        elif val is not None:
            normalized.append(val)

    if isinstance(value, list):
        for item in value:
            _append_if_valid(item)
    elif value is not None:
        _append_if_valid(value)

    for extra in extra_values:
        _append_if_valid(extra)

    return normalized


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
        ./manage.py setup_config -a allowed_countries=Italy Romania Spain
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
        parser.add_argument("-o", "--override", action="append", nargs="+", metavar="FIELD [VALUES]", help="Override field values")
        parser.add_argument("-r", "--remove", action="append", nargs="+", metavar="FIELD [VALUES]", help="Remove values from list fields")
        parser.add_argument(
            "-a",
            "--append",
            action="append",
            nargs="+",
            metavar="FIELD [VALUES]",
            help="Append values to list fields or override non-list",
        )
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
                    field, value, extra_values = parse_option_group(item, mode)
                    updates.append((field, mode, value, extra_values))

        for field, mode, value, extra_values in updates:
            if field not in fields_info:
                raise CommandError(f"Field '{field}' does not exist in Config model.")

            field_obj = fields_info[field]
            is_list = isinstance(field_obj, ArrayField)
            current = getattr(config, field)

            # -------- Normalize input ----------
            if is_list:
                normalized_values = _normalize_list_payload(value, extra_values)

                if field == "allowed_countries":
                    normalized_values = _normalize_country_payload(normalized_values)

                values_to_validate = normalized_values
            else:
                if extra_values:
                    raise CommandError(f"Field '{field}' does not accept multiple values in a single command.")
                normalized_values = value
                values_to_validate = [value]

            # -------- Validate ----------
            validators = getattr(field_obj, "validators", [])

            try:
                if is_list:
                    for validator in validators:
                        validator(values_to_validate)
                else:
                    for validator in validators:
                        validator(values_to_validate[0])
            except ValidationError as e:
                raise CommandError(
                    f"Validation error on field '{field}' with value '{values_to_validate}': {e}"
                )


            # -------- Apply changes ----------
            if is_list:
                current = current or []
                if mode == "append":
                    current = _deduplicate_preserving_order([*current, *normalized_values])
                elif mode == "override":
                    current = _deduplicate_preserving_order(normalized_values)
                elif mode == "remove":
                    current = _deduplicate_preserving_order(
                        [item for item in current if item not in normalized_values]
                    )
            else:
                if mode != "override":
                    raise CommandError(f"Field '{field}' is not a list. Use --override to set its value.")
                current = normalized_values

            setattr(config, field, current)

        config.save()
        self.stdout.write(self.style.SUCCESS("Config updated successfully."))

