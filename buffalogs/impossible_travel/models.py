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
