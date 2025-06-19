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
        if not alerts.exists():
            return

        try:
            for alert in alerts:
                subject = f"Login Anomaly Alert: {alert.name}"
                body = f"Dear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"

                send_mail(subject, body, self.email_config.get("DEFAULT_FROM_EMAIL"), self.recipient_list)  # 1 if sent,0 if not
                self.logger.info(f"Email alert Sent: {alert.name} to {self.recipient_list}")
                alert.notified = True
                alert.save()

        except Exception as e:
            self.logger.error(f"Email alert failed for {alert.name}: {str(e)}")
