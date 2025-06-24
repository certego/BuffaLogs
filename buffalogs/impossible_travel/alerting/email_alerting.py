from django.conf import settings
from django.core.mail import send_mail
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
        self.recipient_list = alert_config.get("recipient_list")
        self.email_config = alert_config
        self._configure_email_settings()

        if not self.recipient_list or not self.email_config:
            self.logger.error("Email Alerter configuration is missing required fields.")
            raise ValueError("Email Alerter configuration is missing required fields.")

    def _configure_email_settings(self):
        """Dynamically set Django email settings without reconfiguring."""

        email_settings = {
            "EMAIL_BACKEND": self.email_config.get("email_backend"),
            "EMAIL_HOST": self.email_config.get("email_server"),
            "EMAIL_PORT": self.email_config.get("email_port"),
            "EMAIL_USE_TLS": self.email_config.get("email_use_tls"),
            "EMAIL_HOST_USER": self.email_config.get("email_host_user"),
            "EMAIL_HOST_PASSWORD": self.email_config.get("email_host_password"),
            "DEFAULT_FROM_EMAIL": self.email_config.get("default_from_email"),
        }

        # Apply each setting dynamically
        for key, value in email_settings.items():
            setattr(settings, key, value)

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)

            # Email for admin
            try:
                send_mail(alert_title, alert_description, self.email_config.get("DEFAULT_FROM_EMAIL"), self.recipient_list)  # 1 if sent,0 if not
                self.logger.info(f"Email alert Sent: {alert.name} to {self.recipient_list}")
                alert.notified = True
                alert.save()
            except Exception as e:
                self.logger.exception(f"Email alert failed for {alert.name}: {str(e)}")

            # Email for user
            if alert.user.email:
                alert_title = f"BuffaLogs - Login Anomaly Alert: {alert.name}"
                alert_description = (
                    f"Dear {alert.user.username},\nAn unusual login activity has been detected:\n\n"
                    f"Alert type: {alert.name}\n"
                    f"Description: {alert.description}\n"
                    f"Please check your account for any suspicious activity.\n\n"
                    "Stay Safe,\nBuffalogs"
                )
                try:
                    send_mail(
                        alert_title,
                        alert_description,
                        self.email_config.get("DEFAULT_FROM_EMAIL"),
                        [alert.user.email],
                    )
                    self.logger.info(f"Email alert Sent: {alert.name} to {alert.user.email}")
                except Exception as e:
                    self.logger.exception(f"Email alert failed for user {alert.user.username}: {str(e)}")
