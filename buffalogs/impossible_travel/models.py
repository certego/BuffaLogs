from django.contrib.postgres.fields import ArrayField
from django.db import models


class User(models.Model):
    class riskScoreEnum(models.TextChoices):
        NO_RISK = "No risk"
        LOW = "Low"
        MEDIUM = "Medium"
        HIGH = "High"

    risk_score = models.CharField(
        choices=riskScoreEnum.choices,
        max_length=256,
        null=False,
    )
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
    class ruleNameEnum(models.TextChoices):
        NEW_DEVICE = "Login from new device"
        IMP_TRAVEL = "Impossible Travel detected"
        NEW_COUNTRY = "Login from new country"

    name = models.CharField(
        choices=ruleNameEnum.choices,
        max_length=256,
        null=False,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_raw_data = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    description = models.TextField()
    is_vip = models.BooleanField(default=False)


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


class Config(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    ignored_users = ArrayField(models.CharField(max_length=20), blank=True, default=list)
    ignored_ips = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    allowed_countries = ArrayField(models.CharField(max_length=20), blank=True, default=list)
    vip_users = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    distance_accepted = models.PositiveIntegerField(
        default=100, help_text="Minimum distance (in Km) between two logins after which the impossible travel detection starts"
    )
    vel_accepted = models.PositiveIntegerField(
        default=300, help_text="Minimum velocity (in Km/h) between two logins after which the impossible travel detection starts"
    )
    user_max_days = models.PositiveIntegerField(default=60, help_text="Days after which the users will be removed from the db")
    login_max_days = models.PositiveIntegerField(default=30, help_text="Days after which the logins will be removed from the db")
    alert_max_days = models.PositiveIntegerField(default=30, help_text="Days after which the alerts will be removed from the db")
    ip_max_days = models.PositiveIntegerField(default=30, help_text="Days after which the IPs will be removed from the db")
