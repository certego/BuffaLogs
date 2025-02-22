from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert
import smtplib
from email.message import EmailMessage

class EmailAlerting(BaseAlerting):
    def __init__(self, alert_config: dict):
        super().__init__()
        self.config = alert_config.get("email", {})
        self.validate_config()

    def validate_config(self):
        required_field = ['host', 'port', 'sender', 'recipient']
        missing_field = [field for field in required_field if not self.config.get(field)]
        if missing_field:
            raise ValueError(f"Missing required email config field: {missing_field}")
        
    def _create_email_message(self, alert: Alert) -> EmailMessage:
        msg = EmailMessage()
        msg['Subject'] = f"[Buffalogs] New Security Alert: {alert.name}"
        msg['From'] = self.config['sender']
        msg['To'] = self.config['recipient']

        body = f"""
        New security alert detected:
        
        User: {alert.user.username}
        Alert Type: {alert.name}
        Description: {alert.description}
        Risk Score: {alert.login_raw_data.get('risk_score', 'N/A')}
        Timestamp: {alert.created.isoformat()}
        """
        msg.set_content(body.strip())
        return msg

    def notify_alerts(self):
        alerts = Alert.objects.filter(notified=False)
        
        try:
            if self.config.get('use_ssl'):
                server = smtplib.SMTP_SSL(self.config['host'], self.config['port'])
            else:
                server = smtplib.SMTP(self.config['host'], self.config['port'])

            if self.config.get('use_tls'):
                server.starttls()

            if self.config.get('username') and self.config.get('password'):
                server.login(self.config['username'], self.config['password'])

            for alert in alerts:
                msg = self._create_email_message(alert)
                server.send_message(msg)
                alert.notified = True
                alert.save()
                self.logger.info(f"Sent email alert for {alert.name} to {self.config['recipient']}")

            server.quit()
        except Exception as e:
            self.logger.error(f"Email alert failed: {str(e)}")
            raise
