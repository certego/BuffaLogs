from collections import defaultdict

import backoff
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

    @backoff.on_exception(backoff.expo, Exception, max_tries=5, base=2)
    def send_message(self, alert, recipient_list, alert_title=None, alert_description=None):
        if alert_title is None and alert_description is None and alert:
            alert_title, alert_description = self.alert_message_formatter(alert)

        res = send_mail(
            alert_title,
            alert_description,
            self.email_config.get("DEFAULT_FROM_EMAIL"),
            recipient_list,
        )
        if res == 0:
            raise Exception(f"Email alert failed to send to {recipient_list}")
        return res

    def send_scheduled_summary(self, start_date, end_date, total_alerts, user_breakdown, alert_breakdown):
        summary_title, summary_description = self.alert_message_formatter(
            alert=None,
            template_path="alert_template_summary.jinja",
            start_date=start_date,
            end_date=end_date,
            total_alerts=total_alerts,
            user_breakdown=user_breakdown,
            alert_breakdown=alert_breakdown,
        )

        try:
            self.send_message(
                alert=None,
                recipient_list=self.recipient_list_admins,
                alert_title=summary_title,
                alert_description=summary_description,
            )
            self.logger.info(f"Email Summary Sent From: {start_date} To: {end_date}")
        except Exception as e:
            self.logger.exception(f"Email Summary Notification Failed: {str(e)}")

    def notify_alerts(self, start_date=None, end_date=None):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(Q(notified_status__email=False) | ~Q(notified_status__has_key="email"))
        if start_date is not None and end_date is not None:
            alerts = Alert.objects.filter((Q(notified_status__email=False) | ~Q(notified_status__has_key="email")) & Q(created__range=(start_date, end_date)))

        grouped = defaultdict(list)
        for alert in alerts:
            key = (alert.user.username, alert.name)
            grouped[key].append(alert)

        for (username, alert_name), group_alerts in grouped.items():
            if len(group_alerts) == 1:
                alert = group_alerts[0]
                # Email for admin
                try:
                    self.send_message(alert=alert, recipient_list=self.recipient_list_admins)  # 1 if sent,0 if not
                    self.logger.info(f"Email alert Sent: {alert.name} to {self.recipient_list_admins}")
                except Exception as e:
                    self.logger.exception(f"Email alert failed for {alert.name}: {str(e)}")

                # Email for user
                if username in list(self.recipient_list_users.keys()):
                    alert_title, alert_description = self.alert_message_formatter(alert, template_path=self.user_email_template_path)
                    try:
                        self.send_message(
                            alert=None,
                            alert_title=alert_title,
                            alert_description=alert_description,
                            recipient_list=[self.recipient_list_users[alert.user.username]],
                        )
                        self.logger.info(f"Email alert Sent: {alert.name} to {self.recipient_list_users[alert.user.username]}")
                    except Exception as e:
                        self.logger.exception(f"Email alert failed for {alert.name}: {str(e)}")

                alert.notified_status["email"] = True
                alert.save()

            else:
                alert = group_alerts[0]
                alert_title, alert_description = self.alert_message_formatter(
                    alert=alert,
                    template_path="alert_template_clubbed.jinja",
                    alerts=group_alerts,
                )

                try:
                    self.send_message(
                        alert=None,
                        recipient_list=self.recipient_list_admins,
                        alert_title=alert_title,
                        alert_description=alert_description,
                    )  # 1 if sent,0 if not
                    self.logger.info(f"Clubbed Email alert Sent: {alert_title} to {self.recipient_list_admins}")
                    for a in group_alerts:
                        a.notified_status["email"] = True
                        a.save()
                except Exception as e:
                    self.logger.exception(f"Clubbed Email Alert Failed for {group_alerts}: {str(e)}")
