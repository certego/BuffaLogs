from collections.abc import Iterable

from django.db import models
from impossible_travel.models import Alert, Login, User, UsersIP


class Serializer:

    def __init__(self, instance: models.Model | list[models.Model]):
        self.instance = instance

    def to_representation(self, item):
        return NotImplemented

    @property
    def data(self):
        data = self.instance.all() if isinstance(self.instance, models.manager.BaseManager) else self.instance
        if isinstance(data, Iterable):
            return [self.to_representation(item) for item in data]
        return self.to_representation(data)


class LoginSerializer(Serializer):

    def to_representation(self, item):
        return {
            "timestamp": self.item.timestamp,
            "created": self.item.created,
            "updated": self.item.updated,
            "latitude": self.item.latitude,
            "logitude": self.item.longitude,
            "event_id": self.item.event_id,
            "country": self.item.country,
            "device": self.item.user_agent,
            "index": self.item.index,
            "user": self.item.user.username,
            "ip": self.item.ip,
        }


class UserSerializer(Serializer):

    def to_representation(self, item):
        return {
            "id": item.id,
            "username": item.username,
            "risk_score": item.risk_score,
            "login_count": Login.objects.filter(user=item).count(distinct=True),
            "alert_count": Alert.objects.filter(user=item).count(distinct=True),
            "last_login": Login.objects.filter(user=item).order_by("timestamp").max(),
        }


class AlertSerializer(Serializer):

    def to_representation(self, item):
        return {
            "created": item.created.strftime("%y-%m-%d %H:%M:%S"),
            "country": item.login_raw_data["country"].lower(),
            "timestamp": item.login_raw_data.get("timestamp"),
            "notified": bool(item.notified_status),
            "severity_type": item.user.risk_score,
            "triggered_by": item.user.username,
            "filter_type": item.filter_type,
            "rule_desc": item.description,
            "rule_name": item.name,
            "is_vip": item.is_vip,
        }
