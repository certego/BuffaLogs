from datetime import datetime

from django.conf import settings
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from impossible_travel.constants import AlertDetectionType, AlertFilterType, UserRiskScoreType
from impossible_travel.validators import validate_countries_names, validate_country_couples_list, validate_ips_or_network, validate_string_or_regex


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
            query = query.filter(user_agent=user_agent)
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
    filter_type = ArrayField(
        models.CharField(max_length=50, choices=AlertFilterType.choices, blank=True),
        blank=True,
        default=list,
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
            query = query.filter(login_raw_data__user_agent=user_agent)
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


def get_default_risk_score_increment_alerts():
    return list(settings.CERTEGO_BUFFALOGS_RISK_SCORE_INCREMENT_ALERTS)


def get_default_filtered_alerts_types():
    return list(settings.CERTEGO_BUFFALOGS_FILTERED_ALERTS_TYPES)


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
        models.CharField(max_length=50),
        blank=True,
        null=True,
        default=get_default_vip_users,
        help_text="List of users considered more sensitive",
    )
    alert_is_vip_only = models.BooleanField(
        default=False,
        help_text="Flag to send alert only related to the users in the vip_users list",
    )
    alert_minimum_risk_score = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        blank=False,
        default=UserRiskScoreType.MEDIUM,
        help_text="Select the risk_score that users should have at least to send the alerts",
    )
    risk_score_increment_alerts = ArrayField(
        models.CharField(max_length=50, choices=AlertDetectionType.choices, blank=False),
        default=get_default_risk_score_increment_alerts,
        blank=False,
        null=False,
        help_text="List of alert types to consider to increase the user risk_score",
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
        validators=[validate_countries_names],
        help_text="List of countries to exclude from the detection, because 'trusted' for the customer",
    )

    # Detection filters - devices
    ignored_ISPs = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        null=True,
        default=get_default_ignored_ISPs,
        help_text="List of ISPs names to remove from the detection",
    )
    ignore_mobile_logins = models.BooleanField(default=True, help_text="Flag to ignore mobile devices from the detection")

    # Detection filters - alerts
    filtered_alerts_types = ArrayField(
        models.CharField(max_length=50, choices=AlertDetectionType.choices, blank=True),
        default=get_default_filtered_alerts_types,
        blank=True,
        null=True,
        help_text="List of alerts' types to exclude from the alerting",
    )
    threshold_user_risk_alert = models.CharField(
        choices=UserRiskScoreType.choices,
        max_length=30,
        blank=False,
        default=UserRiskScoreType.MEDIUM,
        help_text="Select the risk_score that a user should overcome to send the 'USER_RISK_THRESHOLD' alert",
    )
    ignored_impossible_travel_countries_couples = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_country_couples_list],
        help_text=(
            "List of country pairs (start_country, last_country) to ignore for impossible_travel alerts. "
            "Country names must match the names in the countries_list.json config file. "
            "Example: [['Italy', 'Italy'], ['United States', 'France']]"
        ),
    )
    ignored_impossible_travel_all_same_country = models.BooleanField(
        default=True,
        help_text=(
            "If true, all the impossible travel alerts from and to the same country are ignored. "
            "If you want to exclude just some countries, use the 'ignored_impossible_travel_countries_couples' Config field instead"
        ),
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
        default=settings.CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS,
        help_text="Days after which a login from a country is considered atypical",
    )
    user_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_USER_MAX_DAYS,
        help_text="Days after which the users will be removed from the db",
    )
    login_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS,
        help_text="Days after which the logins will be removed from the db",
    )
    alert_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_ALERT_MAX_DAYS,
        help_text="Days after which the alerts will be removed from the db",
    )
    ip_max_days = models.PositiveIntegerField(
        default=settings.CERTEGO_BUFFALOGS_IP_MAX_DAYS,
        help_text="Days after which the IPs will be removed from the db",
    )

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
