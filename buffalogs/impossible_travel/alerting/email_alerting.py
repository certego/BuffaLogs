from django.conf import settings
from django.core.mail import send_mail
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class EmailAlerting(BaseAlerting):
    """
    Implementation of the BaseAlerting class for Email Alerts.
    """

    def __init__(self, alert_config: dict):
        """
        Initialize the Email Alerting class with email settings.
        """
        super().__init__()
        self.recipient_list = ["RECEIVER_EMAIL_ADDRESS"]
        self.email_config = alert_config
        self._configure_email_settings()

    def _configure_email_settings(self):
        """Dynamically set Django email settings without reconfiguring."""

        email_settings = {
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
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
        Send email alerts for anomalies.
        """
        alerts = Alert.objects.filter(notified=False)
        if not alerts.exists():
            return

        # Establish SMTP connection
        try:
            for alert in alerts:
                subject = f"Login Anomaly Alert: {alert.name}"
                body = f"Dear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"

                send_mail(subject, body, self.email_config.get("DEFAULT_FROM_EMAIL"), self.recipient_list)  # 1 if sent,0 if not
                self.logger.info(f"Email Alert Sent: {alert.name} to {self.recipient_list}")
                alert.notified = True
                alert.save()

        except Exception as e:
            self.logger.error(f"Error sending email alert: {str(e)}")
