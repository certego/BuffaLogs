from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
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
        self.user_email_template_path = "alert_template_user_email.jinja"
        self.recipient_list_admins = alert_config.get("recipient_list_admins")
        self.recipient_list_users = alert_config.get("recipient_list_users")
        self.email_config = alert_config
        self._configure_email_settings()

        if not self.recipient_list_admins or not self.email_config:
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
        alerts = Alert.objects.filter(Q(notified_status__email=False) | ~Q(notified_status__has_key="email"))
        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)

            # Email for admin
            try:
                send_mail(alert_title, alert_description, self.email_config.get("DEFAULT_FROM_EMAIL"), self.recipient_list_admins)  # 1 if sent,0 if not
                self.logger.info(f"Email alert Sent: {alert.name} to {self.recipient_list_admins}")
            except Exception as e:
                self.logger.exception(f"Email alert failed for {alert.name}: {str(e)}")

            # Email for user
            if alert.user.username in list(self.recipient_list_users.keys()):
                alert_title, alert_description = self.alert_message_formatter(alert, template_path=self.user_email_template_path)
                try:
                    send_mail(alert_title, alert_description, self.email_config.get("DEFAULT_FROM_EMAIL"), [self.recipient_list_users[alert.user.username]])
                    self.logger.info(f"Email alert Sent: {alert.name} to {self.recipient_list_users[alert.user.username]}")
                except Exception as e:
                    self.logger.exception(f"Email alert failed for {alert.name}: {str(e)}")

            alert.notified_status["email"] = True
            alert.save()
