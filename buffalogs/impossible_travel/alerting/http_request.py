import os
from functools import partial

import requests
from django.conf.settings import HTTP_ALERT_TOKENS
from impossible_travel.alerting.base_alerter import BaseAlerting
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert

PERMITTED_ALERT_FIELD_LIST = ["user", "created", "description", "is_vip", "is_filtered", "filter_type"]
PERMITTED_LOGIN_FIELD_LIST = ["index", "lat", "lon", "country", "timestamp"]
ALERT_TYPE_LIST = [item.value for item in AlertDetectionType]


def parse_fields_value(field_value: str | list, field_name: str, supported_values: list):
    """
    Parse and validate a field value against a list of supported values.

    This function validates the provided field value against a predefined list of supported values.
    - If the field value is a string, it checks the following special cases:
        - If the value is '_all_' (case-insensitive), it returns the full list of supported values.
        - If the value is '_empty_' (case-insensitive), it returns an empty list.
        - Otherwise, it raises a ValueError.
    - If the field value is a list, each element is checked to ensure it exists in the supported values list.
        - If any element is not permitted, a ValueError is raised.

    Args:
        field_name (str): The name of the field being parsed (used for error messages).
        field_value (str or list): The value to be parsed; can be a single string or a list of values.
        supported_values (list): The list of allowed values for this field.

    Returns:
        A list of validated values corresponding to the field.

    Raises:
        ValueError: If the field value is unrecognized or contains elements not present in supported_values.
    """
    if isinstance(field_name, str):
        if field_value.lower() == "_all_":
            return supported_values
        if field_value.lower() == "_empty_":
            return []
        raise ValueError(f"Unkown option {field_value} for {field_name}")
    for _ in field_value:
        if _ not in supported_values:
            raise ValueError(f"{field_name} value {_} is not permitted or does not exists")


def get_alerts(names: list = [], get_all: bool = False):
    """
    Retrieve all alerts that have not been sent as notifications.

    If the parameter `names` is not an empty list, only alerts with names included in the list will be returned.
    If `names` is an empty list and `get_all` is True all alerts not notified will be returned
    Otherwise an empty list is returned

    Args:
        names   : list of valid AlertDetectionTypes values
        get_all : boolean flag that determines if all not notified alerts are retrivied
                : only effective if names is an empty list
    Returns:
        alerts  : list of Alert objects
    """
    if names:
        alerts = Alert.objects.filter(notified=False, name__in=names)
    elif get_all:
        alerts = Alert.objects.filter(notified=False)
    else:
        alerts = []
    return alerts


def generate_batch(items: list, batch_size: int):
    """
    Return list elements in batches.

    A generator function that yields the element of a list in batches
    Args:
        items (list) : list object to batch
        batch_size (int) : Max number of elements in a single batch
    """
    temp = []
    for item in items:
        temp.append(item)
        if len(temp) == batch_size:
            yield temp
            temp.clear()


class Option:
    "A class to parse and manage user options from alerter configuration."

    defaults = {"alert_types": "_all_", "fields": ["name", "user", "description"], "login_data": "_all_", "batch_size": 10}

    parsers = {
        "alert_types": partial(parse_fields_value, field_name="alert_types", supported_values=ALERT_TYPE_LIST),
        "fields": partial(parse_fields_value, field_name="fields", supported_values=PERMITTED_ALERT_FIELD_LIST),
        "login_data": partial(parse_fields_value, field_name="login_data", supported_values=PERMITTED_LOGIN_FIELD_LIST),
    }

    @classmethod
    def set_default(cls, option_name, default_value, parse_func: callable = None):
        """
        Add or update existing key in default dictionary.
        Sets the parse function if provided.

        Args:
            option_name (str) : Name of option to add or updated
            default_value (any): Value to be added as option
        """
        cls.default_dict[option_name] = default_value
        if parse_func:
            cls.parsers[option_name] = parse_func

    @classmethod
    def set_parser(cls, option_name: str, parse_func: callable):
        """
        Add or update existing key in parsers.

        Args:
            option_name(callable) : Name of option
            parse_func(callable) : A callable that takes the value of `option_name` as the only required parameter
                                    and returns a value to be set as the option for `option_name` or raises a ValueError
                                    which will be logged.
        """
        cls.parsers[option_name] = parse_func

    @classmethod
    def configure_from_dict(cls, name, option_dict):
        """
        Configure an Option instance from a dictionary.

        Args:
            name (str): The identifier for the options instance.
            option_dict (dict): A dictionary containing option values keyed by option names.

        Returns:
            obj: A configured instance of the Option class with attributes set based on the provided dictionary.
        """
        obj = cls()
        obj.name = name
        # get all configuration keys
        # using set to avoid duplicate keys
        # dictionary keys are hash-able
        keys = set(cls.defaults.keys()).union(set(option_dict.keys()))
        for key in keys:
            if key in option_dict:
                value = option_dict[key]
            else:
                value = cls.defaults[key]

            parser_func = cls.parsers.get(key, lambda value: value)
            value = parser_func(option_dict[key])
            setattr(obj, key, value)
        return obj


class HTTPRequestAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseAlerting class
    for alerting via HTTP request.
    """

    required_fields = ["name", "endpoint"]
    Option = Option

    def __init__(self, alert_config: dict):
        """Initialize HTTPRequestAlerter object."""
        super().__init__(self)
        self.alert_config = alert_config

    def serialize_alerts(self, alerts: list[Alert], fields: list, login_data_fields: list):
        """
        Serialize a collection of alerts into a list of dictionaries with selected fields.

        Iterates over each alert in the list and extracts the specified attributes defined
        by `fields` and `login_data_fields`.

        Args:
            alerts (list): A list of Alert objects to be serialized.
            fields (list): A list of field names to extract from each alert.
            login_data_fields (list): A list of field names to extract from each alert's login_raw_data.

        Returns:
            data : A list of dictionaries, each representing a serialized alert

        """
        data = []
        for alert in alerts:
            serialized_data = {}
            if "user" in fields:
                serialized_data["user"] = alert.user.username
                fields.remove("user")
            serialized_data.update(dict((field_name, getattr(alert, field_name)) for field_name in fields))
            if login_data_fields:
                alert_login_raw = alert.login_raw_data
                login = dict((field_name, alert_login_raw[field_name]) for field_name in login_data_fields)
                serialized_data.update(login)
            data.append(serialized_data)
        return data

    def get_token(self, token_variable_name: str):
        """
        Get token from environment variable.

        Return token if found else None.

        Args:
            token_variable_name (str) : Name of environment variable
        """
        return os.environ.get(token_variable_name, None)

    def send_notification(self, recipient_name: str, endpoint: str, data: dict, options: Option):
        """
        Send a notification to a specified endpoint using an HTTP POST request.

        This method retrieves the authentication token for recipient from `settings` HTTP_ALERT_TOKENS
        dictionary with `recipient_name` as the lookup key. If no token is found, request is sent without
        an authorization header.

        Args:
            recipient_name (str): The name of the recipient
            endpoint (str): The URL endpoint
            data (dict): serialized alert data
            options (Option): An instance of Option containing additional configuration for the notification.

        Returns:
            Response: The HTTP response object returned from the POST request.
        """

        token = self.get_token(options.token_variable_name)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            self.logger.debug("Token not found for: {recipient_name}")
        return requests.post(endpoint, json=data, headers=headers)

    def send_alert(self, recipient_name: str, endpoint: str, alerts: list[Alert], options: Option):
        """
        Send an alert notification.

        This method sends alert notification in batches determined by option.batch_size
        alert object in a batch are updated if notification is successful before moving
        to the next batch.

        Args:
            recipient_name (str): The name of the recipient for the alert.
            endpoint (str): The URL endpoint to which the alert should be sent.
            token (str): The authentication token used for sending the alert.
            data (list): List of dictionary containing the alert data payload.
            options (Option): An instance of Option containing configuration options.

        """
        for alert_batch in generate_batch(alerts, batch_size=options.batch_size):
            data = self.serialize_alerts(alert_batch, fields=options.fields, login_data=options.login_data)
            try:
                resp = self.send_notification(recipient_name, endpoint, data, options)
            except Exception as e:
                resp = None
                error_msg = str(e)

            for alert in alert_batch:
                if resp is None:
                    # Log error message to all alerts in the batch
                    self.logger.error(f"Alerting Failed: {alert.name} to: {recipient_name} endpoint: {endpoint} error: {error_msg}")
                elif resp.ok:
                    # Mark alerts as notified
                    alert.notified = True
                    alert.save()
                    self.logger.info(f"Notification sent: {alert.name} to: {recipient_name} endpoint: {endpoint} status: {resp.status}")
                else:
                    # Log error message for alerts in the batch
                    self.logger.error("Alerting Failed: {alert.name} to: {recipient_name} endpoint: {endpoint} status: {resp.status}")

    def validate_recipient(self, recipient: dict):
        """
        Validate that a recipient configuration contains all required fields.

        Checks if recipient dictionary has the all `required_fields`

        Args:
            recipient (dict): A dictionary representing the recipient configuration.

        Returns:
            bool: True if the recipient contains all required fields; False if any are missing.
        """
        missing_required_fields = [field for field in self.required_fields if field not in recipient]
        if missing_required_fields:
            name = recipient.get("name", "")
            self.logger.error(f"Improperly configured recipient: {name} missing required fields: {','.join(missing_required_fields)}")
            return False
        return True

    def notify_alerts(self):
        """Send notification to recipients specified in alert_config."""
        recipient_list = self.alert_config["recipients"]
        for recipient in recipient_list:
            if not self.validate_recipient(recipient):
                continue

            endpoint = recipient.get("endpoint")
            recipient_name = recipient.get("name")
            try:
                options = self.Option.configure_from_dict(recipient["options"])
            except ValueError as err:
                self.logger.error(f"Invalid Option For Recipient: {recipient_name} error: str(err)")
                continue
            alerts = get_alerts(options.alert_types, recipient_name)
            self.logger.info(f"Sending alert to: {recipient_name}")
            self.send_alert(recipient_name, endpoint, alerts, options)
