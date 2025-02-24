from django.core.mail import send_mail, get_connection
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class EmailAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for EmailAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Email Alerter query object.
        """
        super().__init__()
        self._validate_config(alert_config)
        self.config = alert_config

    def _validate_config(self, config: dict):
        """
        Ensure all required configuration parameters exist
        """
        required_keys = {
            "email_server",
            "email_host_user",
            "email_host_password",
            "default_from_email",
            "recipient_list",
        }
        missing = required_keys - config.keys()
        if missing:
            raise ValueError(f"Missing email configuration keys: {', '.join(missing)}")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            self.send_email(alert)
            self.logger.info("Alerting %s", alert.name)
            alert.notified = True
            alert.save()

    def send_email(self, alert):
        subject = f"Alert: {alert.name}"  # TODO: Construct a clear and descriptive email subject line.
        body = f"Hello, {alert.user.username}\n\n{alert.description}\n\nThank you."  # TODO: Construct a clear and descriptive email body.
        from_email = self.config.get("default_from_email")
        recipient_list = self.config.get("recipient_list", [])
        if not recipient_list:
            self.logger.warning("No recipients configured for email alerts.")
            return
        connection = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=self.config.get("email_server"),
            port=self.config.get("email_port"),
            username=self.config.get("email_host_user"),
            password=self.config.get("email_host_password"),
            use_tls=self.config.get("email_use_tls"),
        )

        try:
            send_mail(subject, body, from_email, recipient_list, connection=connection)
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            raise
        finally:
            connection.close()
