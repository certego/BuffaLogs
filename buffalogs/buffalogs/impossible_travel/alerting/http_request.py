import os
from functools import partial

try:
    import requests
except ImportError:
    pass
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Alert

PERMITTED_ALERT_FIELD_LIST = ["name", "user", "created", "description", "is_vip", "is_filtered", "filter_type"]
PERMITTED_LOGIN_FIELD_LIST = ["index", "lat", "lon", "country", "timestamp"]
ALERT_TYPE_LIST = [item.value for item in AlertDetectionType]


def parse_fields_value(field_value: str | list, field_name: str, supported_values: list, default: list | None = None):
    """
    Parse and validate a field value against a list of supported values.

    This function validates the provided field value against a predefined list of supported values.
    If the given option contains an invalid option, it is simply bypassed and the default is selected

    Valid options:
        - string : specifies if all or non of the supported_values should be returned
            - '_all_' (case-insensitive) : returns the full list of supported values.
            - '_empty_' (case-insensitive) : returns an empty list.
        - list : specifies a subset of supported_values to return, if an element is not in the supported_values it is skipped.

    Args:
        field_name (str): The name of the field being parsed (used for error messages).
        field_value (str or list): The value to be parsed; can be a single string or a list of values.
        supported_values (list): The list of allowed values for this field.

    Returns:
        tuple - of a string for logging and a list of validated values of the field.
    """
    if default is None:
        default = supported_values
    if isinstance(field_value, str):
        if field_value.lower() == "_all_":
            return None, supported_values
        if field_value.lower() == "_empty_":
            return None, []
        return f"Unsupported value: {field_value} for {field_name}, using defaults", default
    invalid_values = []
    msg = None
    # using copy to allow modification
    # of field_value during iteration
    value_iterator = iter(field_value[:])
    for value in value_iterator:
        if value not in supported_values:
            invalid_values.append(value)
            field_value.remove(value)

    if invalid_values:
        msg = f"Unsupported values {', '.join(invalid_values)} in {field_name}"
    return msg, field_value


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
        alerts = Alert.objects.filter(notified_status__http_request=False, name__in=names)
    elif get_all:
        alerts = Alert.objects.filter(notified_status__http_request=False)
    else:
        alerts = []
    return alerts


def check_variable_exists(variable_name: str, default: str = ""):
    """
    Check if variable is an environment variable.

    Args:
        variable_name : name to look up
        default : value to return if name is not a environment variable
    """
    if not variable_name:
        return None, default
    elif variable_name not in os.environ:
        return None, os.environ[variable_name]
    else:
        return "Variable name {variable_name} is not set as Environment variable", default


def generate_batch(items: list, batch_size: int):
    """
    Return list elements in batches.

    A generator function that yields the element of a list in batches
    Args:
        items (list) : list object to batch
        batch_size (int) : Max number of elements in a single batch
    """
    if batch_size == -1:
        yield from items
        return
    start = 0
    end = len(items)
    while start < end:
        yield items[start : start + batch_size]
        start += batch_size


class HTTPRequestAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseAlerting class
    for alerting via HTTP request.
    """

    required_fields = ["name", "endpoint"]

    extra_option_parsers = {"token_variable_name": check_variable_exists}
    extra_options = {"token_variable_name": ""}
    default_options = {
        "alert_types": "_all_",
        "fields": ["name", "user", "description", "created"],
        "login_data": "_all_",
        "token_variable_name": "",
        "batch_size": -1,
    }
    option_parsers = {
        "alert_types": partial(parse_fields_value, field_name="alert_types", supported_values=ALERT_TYPE_LIST),
        "fields": partial(
            parse_fields_value, field_name="fields", supported_values=PERMITTED_ALERT_FIELD_LIST, default=["name", "user", "description", "created"]
        ),
        "login_data": partial(parse_fields_value, field_name="login_data", supported_values=PERMITTED_LOGIN_FIELD_LIST),
    }

    def __init__(self, alert_config: dict):
        """Initialize HTTPRequestAlerter object."""
        super().__init__()
        if self.extra_options:
            self.default_options.update(self.extra_options)
        if self.extra_option_parsers:
            self.option_parsers.update(self.extra_option_parsers)
        self.configure(alert_config)

    def parse_option(self, key: str, value: str | list):
        def fake_parser(value):
            return None, value

        if key in self.option_parsers:
            parser = self.option_parsers[key]
        else:
            parser = fake_parser
        msg, value = parser(value)
        if msg:
            self.logger.debug(msg)
        return value

    def get_valid_options(self, options: dict):
        if options is None:
            self.logger.debug("config is missing 'options', using defaults.")
            options = self.default_options.copy()

        all_options = set(options.keys()).union(set(self.default_options.keys()))
        for key in all_options:
            value = options.get(key)
            if value is None:
                value = self.default_options.get(key)
            options[key] = self.parse_option(key, value)
        return options

    def configure(self, config: dict):
        """
        Validate and set alert configuration

        Args:
            config (dict): A dictionary representing the recipient configuration.
        """
        # check for required fileds
        missing_required_fields = [field for field in self.required_fields if field not in config]
        if missing_required_fields:
            self.logger.error(f"Improperly configuration: missing required fields: {','.join(missing_required_fields)}")
            raise ValueError("Missing required values for {','.join(missing_required_fields)}")
        self.alert_config = dict((field, config[field]) for field in self.required_fields)

        # check for optional fields
        options = config.get("options", None)
        options = self.get_valid_options(options)
        self.alert_config.update(options)

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
            serialized_data.update(dict((field_name, getattr(alert, field_name)) for field_name in fields if field_name != "user"))
            if login_data_fields:
                alert_login_raw = alert.login_raw_data
                login = dict((field_name, alert_login_raw[field_name]) for field_name in login_data_fields)
                serialized_data.update(login)
            data.append(serialized_data)
        return data

    def get_token(self):
        """
        Get token from environment variable.

        Return token if found else None.

        Args:
            token_variable_name (str) : Name of environment variable
        """
        token_variable_name = self.alert_config["token_variable_name"]
        return os.environ.get(token_variable_name)

    def send_notification(self, recipient_name: str, endpoint: str, data: dict):
        """
        Send a notification to a specified endpoint using an HTTP POST request.

        This method retrieves the authentication token from environment variable.
        If no token is found, request is sent without an authorization header.

        Args:
            recipient_name (str): The name of the recipient
            endpoint (str): The URL endpoint
            data (dict): serialized alert data

        Returns:
            Response: The HTTP response object returned from the POST request.
        """

        token = self.get_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return requests.post(endpoint, json=data, headers=headers)

    def send_alert(self, recipient_name: str, endpoint: str, alerts: list[Alert]):
        """
        Send an alert notification.

        This method sends alert notification in batches determined by option.batch_size
        alert object in a batch are updated if notification is successful before moving
        to the next batch.

        Args:
            recipient_name (str): The name of the recipient for the alert.
            endpoint (str): The URL endpoint to which the alert should be sent.
            token (str): The authentication token used for sending the alert.
            alerts (list): List of Alert objects.
        """
        batch_size = self.alert_config["batch_size"]
        fields = self.alert_config["fields"]
        login_data = self.alert_config["login_data"]
        for alert_batch in generate_batch(alerts, batch_size):
            data = self.serialize_alerts(alert_batch, fields=fields, login_data_fields=login_data)
            try:
                resp = self.send_notification(recipient_name, endpoint, data)
            except Exception as e:
                resp = None
                error_msg = str(e)

            for alert in alert_batch:
                if resp is None:
                    # Log error message to all alerts in the batch
                    self.logger.error(f"Alerting Failed: {alert.name} to: {recipient_name} endpoint: {endpoint} error: {error_msg}")
                elif resp.ok:
                    # Mark alerts as notified
                    alert.notified_status["http_request"] = True
                    alert.save()
                    self.logger.info(f"Notification sent: {alert.name} to: {recipient_name} endpoint: {endpoint} status: {resp.status_code}")
                else:
                    # Log error message for alerts in the batch
                    self.logger.error(
                        f"Alerting Failed: {alert.name} to: {recipient_name} endpoint: {endpoint} status: {resp.status_code} message: {resp.content}"
                    )

    def notify_alerts(self):
        """Send notification to recipients specified in alert_config."""
        endpoint = self.alert_config.get("endpoint")
        recipient_name = self.alert_config.get("name")
        alert_types = self.alert_config["alert_types"]
        alerts = get_alerts(alert_types)
        self.logger.info(f"Sending alert to: {recipient_name}")
        self.send_alert(recipient_name, endpoint, alerts)
