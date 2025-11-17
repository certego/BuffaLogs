from datetime import datetime

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from impossible_travel.constants import ( # type: ignore
    AlertDetectionType,
    AlertFilterType,
    AlertTagValues,
    ExecutionModes,
    UserRiskScoreType,
)
from impossible_travel.validators import ( # type: ignore
    validate_countries_names,
    validate_country_couples_list,
    validate_ips_or_network,
    validate_string_or_regex,
    validate_tags,
)


# -------------------------------------------------------------------
# USER
# -------------------------------------------------------------------
class User(models.Model):
    risk_score = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        null=False,
        default=UserRiskScoreType.NO_RISK,
    )
    username = models.TextField(unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User object ({self.id}) - {self.username}"


# -------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------
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

    STATUS_CHOICES = (
        ("success", "Success"),
        ("failure", "Failure"),
        ("unknown", "Unknown"),
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="success",
        db_index=True,
    )

    failure_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    @classmethod
    def apply_filters(cls, **kwargs):
        query = cls.objects.all().order_by("-timestamp")

        username = kwargs.get("username")
        ip = kwargs.get("ip")
        user_agent = kwargs.get("user_agent")
        login_start_time = kwargs.get("login_start_time")
        login_end_time = kwargs.get("login_end_time")
        country = kwargs.get("country")
        index = kwargs.get("index")
        limit = kwargs.get("limit")
        offset = kwargs.get("offset")

        if username:
            query = query.filter(user__username__icontains=username)
        if ip:
            query = query.filter(ip=ip)
        if user_agent:
            query = query.filter(user_agent__icontains=user_agent)
        if login_start_time:
            query = query.filter(timestamp__gte=login_start_time)
        if login_end_time:
            query = query.filter(timestamp__lte=login_end_time)
        if country:
            query = query.filter(country__iexact=country)
        if index:
            query = query.filter(index__iexact=index)

        if limit:
            query = query[offset : offset + limit]

        return query


# -------------------------------------------------------------------
# ALERT
# -------------------------------------------------------------------
class Alert(models.Model):
    name = models.CharField(choices=AlertDetectionType.choices, max_length=30)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_raw_data = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    description = models.TextField()
    is_vip = models.BooleanField(default=False)

    # FIX: ArrayField → JSONField
    filter_type = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="List of filters that disabled the related alert",
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        null=True,
        validators=[validate_tags],
        help_text="List of tags for alert classification",
    )

    notified_status = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tracks each active_alerter status",
    )

    @property
    def is_filtered(self):
        return bool(self.filter_type)

    @admin.display(description="is_filtered", boolean=True)
    def is_filtered_field_display(self):
        return self.is_filtered


# -------------------------------------------------------------------
# USERS IP
# -------------------------------------------------------------------
class UsersIP(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()


# -------------------------------------------------------------------
# TASK SETTINGS
# -------------------------------------------------------------------
class TaskSettings(models.Model):
    task_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    execution_mode = models.CharField(
        max_length=20,
        choices=ExecutionModes.choices,
        default="automatic",
    )


# -------------------------------------------------------------------
# DEFAULT VALUE HELPERS
# -------------------------------------------------------------------
def get_default_ignored_users():
    return list(settings.CERTEGO_BUFFALOGS_IGNORED_USERS)


def get_default_enabled_users():
    return list(settings.CERTEGO_BUFFALOGS_ENABLED_USERS)


def get_default_ignored_ips():
    return list(settings.CERTEGO_BUFFALOGS_IGNORED_IPS)


def get_default_ignored_ISPs():
    return list(settings.CERTEGO_BUFFALOGS_IGNORED_ISPS)


def get_default_allowed_countries():
    return list(settings.CERTEGO_BUFFALOGS_ALLOWED_COUNTRIES)


def get_default_vip_users():
    return list(settings.CERTEGO_BUFFALOGS_VIP_USERS)


def get_default_risk_score_increment_alerts():
    return list(settings.CERTEGO_BUFFALOGS_RISK_SCORE_INCREMENT_ALERTS)


def get_default_filtered_alerts_types():
    return list(settings.CERTEGO_BUFFALOGS_FILTERED_ALERTS_TYPES)


# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
class Config(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # FIX: ALL ARRAYFIELDS → JSONFIELDS
    ignored_users = models.JSONField(
        default=get_default_ignored_users,
        blank=True,
        null=True,
        validators=[validate_string_or_regex],
    )

    enabled_users = models.JSONField(
        default=get_default_enabled_users,
        blank=True,
        null=True,
        validators=[validate_string_or_regex],
    )

    vip_users = models.JSONField(
        default=get_default_vip_users,
        blank=True,
        null=True,
    )

    alert_is_vip_only = models.BooleanField(default=False)

    alert_minimum_risk_score = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        default=UserRiskScoreType.MEDIUM,
    )

    risk_score_increment_alerts = models.JSONField(
        default=get_default_risk_score_increment_alerts,
    )

    ignored_ips = models.JSONField(
        default=get_default_ignored_ips,
        blank=True,
        null=True,
        validators=[validate_ips_or_network],
    )

    allowed_countries = models.JSONField(
        default=get_default_allowed_countries,
        blank=True,
        null=True,
        validators=[validate_countries_names],
    )

    ignored_ISPs = models.JSONField(
        default=get_default_ignored_ISPs,
        blank=True,
        null=True,
    )

    ignore_mobile_logins = models.BooleanField(default=True)

    filtered_alerts_types = models.JSONField(
        default=get_default_filtered_alerts_types,
        blank=True,
        null=True,
    )

    threshold_user_risk_alert = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        default=UserRiskScoreType.MEDIUM,
    )

    ignored_impossible_travel_countries_couples = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_country_couples_list],
    )

    ignored_impossible_travel_all_same_country = models.BooleanField(default=True)

    distance_accepted = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED,
    )
    vel_accepted = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED,
    )
    atypical_country_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS,
    )
    user_learning_period = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_USER_LEARNING_PERIOD,
    )
    user_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS,
    )
    login_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS,
    )
    alert_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS,
    )
    ip_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS,
    )

    def clean(self):
        if not self.pk and Config.objects.exists():
            raise ValidationError("A Config object already exist")
        self.pk = 1

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
