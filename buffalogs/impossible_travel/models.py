from datetime import datetime 
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from impossible_travel.constants import AlertDetectionType, AlertFilterType, UserRiskScoreType
from impossible_travel.validators import validate_countries_names, validate_country_couples_list, validate_ips_or_network, validate_string_or_regex
from django.contrib.postgres.fields import ArrayField  # add this import

class AlertTagType(models.TextChoices):
    SUSPICIOUS_IP = "suspicious_ip", "Suspicious IP"
    TOR_EXIT_NODE = "tor_exit_node", "TOR Exit Node"
    IMPOSSIBLE_TRAVEL = "impossible_travel", "Impossible Travel"
    VPN = "vpn", "VPN"


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

    @classmethod
    def apply_filters(
        cls,
        *,
        username: str = None,
        country: str = None,
        login_start_time: datetime = None,
        login_end_time: datetime = None,
        ip: str = None,
        user_agent: str = None,
        index: str = None,
        limit: int = 0,
        offset: int = 0,
    ):
        """
        Filters Login objects based on various criteria and applies
        offset/limit pagination.
        """

        query = cls.objects.all().order_by("-timestamp")

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
            start = offset
            end = offset + limit
            query = query[start:end]

        return query


class Alert(models.Model):
    name = models.CharField(choices=AlertDetectionType.choices, max_length=30, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_raw_data = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    description = models.TextField()
    is_vip = models.BooleanField(default=False)

    tags = ArrayField(
        models.CharField(
            max_length=50,
            choices=AlertTagType.choices,
        ),
        default=list,
        blank=True,
        help_text="Select one or more tags",
    )

    filter_type = models.JSONField(
    default=list,
    blank=True,
    help_text="List of filters that disabled the related alert",
 )

    notified_status = models.JSONField(default=dict, blank=True, help_text="Tracks each active_alerter status")

    @property
    def is_filtered(self):
        """Returns if the alert is filtered based on the filter_type field"""
        if self.filter_type:
            return True
        return False

    @admin.display(description="is_filtered", boolean=True)
    def is_filtered_field_display(self):
        return self.is_filtered

    @classmethod
    def apply_filters(
        cls,
        *,
        start_date: datetime = None,
        end_date: datetime = None,
        name: str = None,
        username: str = None,
        is_vip: bool = None,
        notified: bool = None,
        country_code: str = None,
        login_start_time: datetime = None,
        login_end_time: datetime = None,
        ip: str = None,
        user_agent: str = None,
        min_risk_score: int = None,
        max_risk_score: int = None,
        risk_score: int = None,
        limit: int = None,
        offset: int = None,
    ):
        "Filters Alert objects."

        query = cls.objects.all().order_by("-created")
        if start_date:
            query = query.filter(created__gte=start_date)
        if end_date:
            query = query.filter(created__lte=end_date)
        if name:
            query = query.filter(name__iexact=name)
        if username:
            query = query.filter(user__username__icontains=username)
        if is_vip:
            query = query.filter(is_vip=is_vip)
        if notified is False:
            query = query.filter(notified_status={})
        if notified is True:
            query = query.exclude(notified_status={})
        if ip:
            query = query.filter(login_raw_data__ip=ip)
        if user_agent:
            query = query.filter(login_raw_data__user_agent__icontains=user_agent)
        if login_start_time:
            query = query.filter(login_raw_data__timestamp__gte=login_start_time)
        if login_end_time:
            query = query.filter(login_raw_data__timestamp__lte=login_end_time)
        if country_code:
            query = query.filter(login_raw_data__country__iexact=country_code)
        if risk_score:
            if isinstance(risk_score, int):
                query = query.filter(user__risk_score=UserRiskScoreType.get_risk_level(risk_score))
            elif isinstance(risk_score, str):
                risk_score = risk_score.title()
                query = query.filter(user_risk_score=UserRiskScoreType(risk_score))

        elif min_risk_score or max_risk_score:
            risk_range = UserRiskScoreType.get_range(min_value=min_risk_score, max_value=max_risk_score)
            query = query.filter(user__risk_score__in=risk_range)

        if limit:
            start = offset
            end = offset + limit
            query = query[start:end]

        return query

    class Meta:
     constraints=[
    models.CheckConstraint(
        check=models.Q(name__in=[choice[0] for choice in AlertDetectionType.choices]),
        name="valid_alert_name_choice",
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
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

def get_default_ignored_users():
    return getattr(settings, "CERTEGO_BUFFALOGS_IGNORED_USERS", [])

def get_default_enabled_users():
    return getattr(settings, "CERTEGO_BUFFALOGS_ENABLED_USERS", [])

def get_default_vip_users():
    return getattr(settings, "CERTEGO_BUFFALOGS_VIP_USERS", [])

def get_default_ignored_ips():
    return getattr(settings, "CERTEGO_BUFFALOGS_IGNORED_IPS", [])

def get_default_ignored_ISPs():
    return getattr(settings, "CERTEGO_BUFFALOGS_IGNORED_ISPS", [])

def get_default_allowed_countries():
    return getattr(settings, "CERTEGO_BUFFALOGS_ALLOWED_COUNTRIES", [])

def get_default_risk_score_increment_alerts():
    return getattr(settings, "CERTEGO_BUFFALOGS_RISK_SCORE_INCREMENT_ALERTS", [])

def get_default_filtered_alerts_types():
    return getattr(settings, "CERTEGO_BUFFALOGS_FILTERED_ALERTS_TYPES", [])


class Config(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    ignored_users = models.JSONField(default=get_default_ignored_users, blank=True)
    enabled_users = models.JSONField(default=get_default_enabled_users, blank=True)
    vip_users = models.JSONField(default=get_default_vip_users, blank=True)
    ignored_ips = models.JSONField(default=get_default_ignored_ips, blank=True)
    ignored_isps = models.JSONField(default=get_default_ignored_ISPs, blank=True)
    allowed_countries = models.JSONField(default=get_default_allowed_countries, blank=True)
    risk_score_increment_alerts = models.JSONField(default=get_default_risk_score_increment_alerts, blank=True)
    filtered_alerts_types = models.JSONField(default=get_default_filtered_alerts_types, blank=True)

    # Other boolean / char / int fields
    alert_is_vip_only = models.BooleanField(default=False)
    ignore_mobile_logins = models.BooleanField(default=True)

    distance_accepted = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED)
    vel_accepted = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED)
    atypical_country_days = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS)
    user_learning_period = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_USER_LEARNING_PERIOD)
    user_max_days = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS)
    login_max_days = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS)
    alert_max_days = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS)
    ip_max_days = models.PositiveIntegerField(default=settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS)

    def clean(self):
        if not self.pk and Config.objects.exists():
            raise ValidationError("A Config object already exists.")
        self.pk = 1  # Always enforce pk=1

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
  