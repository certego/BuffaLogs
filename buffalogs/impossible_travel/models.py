from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from impossible_travel.constants import AlertDetectionType, AlertFilterType, UserRiskScoreType


class User(models.Model):
    risk_score = models.CharField(choices=UserRiskScoreType.choices, max_length=30, null=False, default=UserRiskScoreType.NO_RISK)
    username = models.TextField(unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Login(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    country = models.TextField(blank=True)
    user_agent = models.TextField(blank=True)
    index = models.TextField()
    event_id = models.TextField()
    ip = models.TextField()


class Alert(models.Model):
    name = models.CharField(
        choices=AlertDetectionType.choices,
        max_length=30,
        null=False,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_raw_data = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    description = models.TextField()
    is_vip = models.BooleanField(default=False)
    is_filtered = models.BooleanField(default=False, help_text="Show if the alert has been filtered because of some filter (listed in the filter_type field)")
    filter_type = ArrayField(
        models.CharField(max_length=50, choices=AlertFilterType.choices, blank=True),
        blank=True,
        default=list,
        help_text="List of filters that disabled the related alert",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                # Check that the Alert.name is one of the value in the Enum AlertDetectionType
                check=models.Q(name__in=[choice[0] for choice in AlertDetectionType.choices]),
                name="valid_alert_name_choice",
            ),
            models.CheckConstraint(
                # Check that each element in the Alert.filter_type is in the Enum AlertFilterType
                check=models.Q(filter_type__contained_by=AlertFilterType.choices),
                name="valid_alert_filter_type_choices",
            ),
        ]


class UsersIP(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()


class TaskSettings(models.Model):
    task_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


def get_default_ignored_users():
    return list(settings.CERTEGO_BUFFALOGS_IGNORED_USERS)


def get_default_enabled_users():
    return list(settings.CERTEGO_BUFFALOGS_ENABLED_USERS)


def get_default_ignored_ips():
    return list(settings.CERTEGO_BUFFALOGS_IGNORED_IPS)


def get_default_allowed_countries():
    return list(settings.CERTEGO_BUFFALOGS_ALLOWED_COUNTRIES)


def get_default_vip_users():
    return list(settings.CERTEGO_BUFFALOGS_VIP_USERS)


class Config(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ignored_users = ArrayField(
        models.CharField(max_length=50), blank=True, default=get_default_ignored_users, help_text="List of users to be ignored from the detection"
    )
    enabled_users = ArrayField(
        models.CharField(max_length=50), blank=True, default=get_default_enabled_users, help_text="List of selected users on which the detection will perform"
    )
    ignored_ips = ArrayField(models.CharField(max_length=50), blank=True, default=get_default_ignored_ips, help_text="List of IPs to remove from the detection")
    allowed_countries = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=get_default_allowed_countries,
        help_text="List of countries to exclude from the detection, because 'trusted' for the customer",
    )
    vip_users = ArrayField(models.CharField(max_length=50), blank=True, default=get_default_vip_users, help_text="List of users considered more sensitive")
    alert_is_vip_only = models.BooleanField(default=False, help_text="Flag to send alert only related to the users in the vip_users list")
    alert_minimum_risk_score = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        blank=False,
        default=UserRiskScoreType.NO_RISK,
        help_text="Select the risk_score that users should have at least to send alert",
    )
    filtered_alerts_types = ArrayField(
        models.CharField(max_length=50, choices=AlertDetectionType.choices, blank=True),
        default=list,
        blank=True,
        help_text="List of alerts' types to exclude from the alerting",
    )
    ignore_mobile_logins = models.BooleanField(default=False, help_text="Flag to ignore mobile devices from the detection")
    distance_accepted = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED,
        help_text="Minimum distance (in Km) between two logins after which the impossible travel detection starts",
    )
    vel_accepted = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED,
        help_text="Minimum velocity (in Km/h) between two logins after which the impossible travel detection starts",
    )
    user_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS, help_text="Days after which the users will be removed from the db"
    )
    login_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS, help_text="Days after which the logins will be removed from the db"
    )
    alert_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS, help_text="Days after which the alerts will be removed from the db"
    )
    ip_max_days = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS, help_text="Days after which the IPs will be removed from the db")

    def clean(self):
        if not self.pk and Config.objects.exists():
            raise ValidationError("A Config object already exist - it is possible just to modify it, not to create a new one")
        else:
            # Config.id=1 always
            self.pk = 1

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                # Check that the Config.alert_minimum_risk_score is one of the value in the Enum UserRiskScoreType
                check=models.Q(alert_minimum_risk_score__in=[choice[0] for choice in UserRiskScoreType.choices]),
                name="valid_config_alert_minimum_risk_score_choice",
            ),
            models.CheckConstraint(
                # Check that each element in the Config.filtered_alerts_types is in the Enum AlertFilterType
                check=models.Q(filtered_alerts_types__contained_by=AlertFilterType.choices),
                name="valid_alert_filters_choices",
            ),
        ]
