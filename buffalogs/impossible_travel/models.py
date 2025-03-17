from django.conf import settings
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from impossible_travel.constants import AlertDetectionType, AlertFilterType, UserRiskScoreType
from impossible_travel.validators import validate_ips_or_network, validate_string_or_regex


class User(models.Model):
    risk_score = models.CharField(choices=UserRiskScoreType.choices, max_length=30, null=False, default=UserRiskScoreType.NO_RISK)
    username = models.TextField(unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User object ({self.id}) - {self.username}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                # Check that the User.risk_score is one of the value in the Enum UserRiskScoreType --> ['No risk', 'Low', 'Medium', 'High']
                check=models.Q(risk_score__in=[choice[0] for choice in UserRiskScoreType.choices]),
                name="valid_user_risk_score_choice",
            )
        ]


class Login(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(default=timezone.now)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    country = models.TextField(blank=True)
    user_agent = models.TextField(blank=True)
    index = models.TextField()
    event_id = models.TextField()
    ip = models.TextField()


class Alert(models.Model):
    name = models.CharField(choices=AlertDetectionType.choices, max_length=30, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_raw_data = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    description = models.TextField()
    is_vip = models.BooleanField(default=False)
    filter_type = ArrayField(
        models.CharField(max_length=50, choices=AlertFilterType.choices, blank=True),
        blank=True,
        default=list,
        help_text="List of filters that disabled the related alert",
    )
    notified = models.BooleanField(help_text="True when the alert has been notified by alerter", default=False)

    @property
    def is_filtered(self):
        """Returns if the alert is filtered based on the filter_type field"""
        if self.filter_type:
            return True
        return False

    @admin.display(description="is_filtered", boolean=True)
    def is_filtered_field_display(self):
        return self.is_filtered

    class Meta:
        constraints = [
            models.CheckConstraint(
                # Check that the Alert.name is one of the value in the Enum AlertDetectionType
                check=models.Q(name__in=[choice[0] for choice in AlertDetectionType.choices]),
                name="valid_alert_name_choice",
            ),
            models.CheckConstraint(
                # Check that each element in the Alert.filter_type is in the Enum AlertFilterType
                check=models.Q(filter_type__contained_by=[choice[0] for choice in AlertFilterType.choices]) | models.Q(filter_type=[]),
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


def get_default_ignored_ISPs():  # pylint: disable=invalid-name
    return list(settings.CERTEGO_BUFFALOGS_IGNORED_ISPS)


def get_default_allowed_countries():
    return list(settings.CERTEGO_BUFFALOGS_ALLOWED_COUNTRIES)


def get_default_vip_users():
    return list(settings.CERTEGO_BUFFALOGS_VIP_USERS)


class Config(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    # Detection filters - users
    ignored_users = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        null=True,
        default=get_default_ignored_users,
        validators=[validate_string_or_regex],
        help_text="List of users (strings or regex patterns) to be ignored from the detection",
    )
    enabled_users = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        null=True,
        default=get_default_enabled_users,
        validators=[validate_string_or_regex],
        help_text="List of selected users (strings or regex patterns) on which the detection will perform",
    )
    vip_users = ArrayField(
        models.CharField(max_length=50), blank=True, null=True, default=get_default_vip_users, help_text="List of users considered more sensitive"
    )
    alert_is_vip_only = models.BooleanField(default=False, help_text="Flag to send alert only related to the users in the vip_users list")
    alert_minimum_risk_score = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        blank=False,
        default=UserRiskScoreType.NO_RISK,
        help_text="Select the risk_score that users should have at least to send the alerts",
    )

    # Detection filters - location
    ignored_ips = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        null=True,
        default=get_default_ignored_ips,
        validators=[validate_ips_or_network],
        help_text="List of IPs to remove from the detection",
    )
    allowed_countries = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        null=True,
        default=get_default_allowed_countries,
        help_text="List of countries to exclude from the detection, because 'trusted' for the customer",
    )

    # Detection filters - devices
    ignored_ISPs = ArrayField(
        models.CharField(max_length=50), blank=True, null=True, default=get_default_ignored_ISPs, help_text="List of ISPs names to remove from the detection"
    )
    ignore_mobile_logins = models.BooleanField(default=False, help_text="Flag to ignore mobile devices from the detection")

    # Detection filters - alerts
    filtered_alerts_types = ArrayField(
        models.CharField(max_length=50, choices=AlertDetectionType.choices, blank=True),
        default=list,
        blank=True,
        null=True,
        help_text="List of alerts' types to exclude from the alerting",
    )
    threshold_user_risk_alert = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        blank=False,
        default=UserRiskScoreType.NO_RISK,
        help_text="Select the risk_score that a user should overcome to send the 'USER_RISK_THRESHOLD' alert",
    )

    distance_accepted = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED,
        help_text="Minimum distance (in Km) between two logins after which the impossible travel detection starts",
    )
    vel_accepted = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED,
        help_text="Minimum velocity (in Km/h) between two logins after which the impossible travel detection starts",
    )
    atypical_country_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS, help_text="Days after which a login from a country is considered atypical"
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
                # Check that each element in the Config.filtered_alerts_types is blank or it's in the Enum AlertFilterType
                check=models.Q(filtered_alerts_types__contained_by=[choice[0] for choice in AlertDetectionType.choices])
                | models.Q(filtered_alerts_types__isnull=True),
                name="valid_alert_filters_choices",
            ),
        ]
