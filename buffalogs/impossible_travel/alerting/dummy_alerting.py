from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class DummyAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for DummyAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Dummy Alerter query object.
        """
        super().__init__()
        # here we can access the alert_config to get the configuration for the alerter
        self.alert_config = alert_config

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for a in alerts:
            # in a real alerters, this would be the place to send the alert
            self.logger.info("Alerting %s", a.name)
            a.notified = True
            a.save()
            
