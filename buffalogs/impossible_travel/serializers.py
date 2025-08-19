import json

from django.db import models
from django.db.models import Max
from impossible_travel.models import Alert, Login, User, UsersIP


class Serializer:

    def __init__(self, instance: models.Model | list[models.Model]):
        self.instance = instance

    def to_representation(self, item):
        return NotImplemented

    @property
    def data(self):
        data = self.instance.all() if isinstance(self.instance, models.manager.BaseManager) else self.instance
        if isinstance(data, (list, tuple, models.QuerySet)):
            return [self.to_representation(item) for item in data]
        return self.to_representation(data)

    def json(self):
        data = self.data
        return json.dumps(data, default=str)


class LoginSerializer(Serializer):

    def to_representation(self, item):
        return {
            "timestamp": item.timestamp,
            "created": item.created.strftime("%y-%m-%d %H:%M:%S"),
            "updated": item.updated.strftime("%y-%m-%d %H:%M:%S"),
            "latitude": item.latitude,
            "longitude": item.longitude,
            "event_id": item.event_id,
            "country": item.country.lower(),
            "device": item.user_agent,
            "index": item.index,
            "user": item.user.username,
            "ip": item.ip,
        }


class UserSerializer(Serializer):

    def to_representation(self, item):
        return {
            "id": item.id,
            "username": item.username,
            "risk_score": item.risk_score,
            "login_count": Login.objects.filter(user=item).distinct().count(),
            "alert_count": Alert.objects.filter(user=item).distinct().count(),
            "last_login": Login.objects.filter(user=item).aggregate(Max("timestamp"))["timestamp__max"],
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
