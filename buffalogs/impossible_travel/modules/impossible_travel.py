import logging
from datetime import datetime

from django.utils import timezone
from geopy.distance import geodesic
from impossible_travel.constants import AlertDetectionType
from impossible_travel.models import Config, Login, UsersIP


class Impossible_Travel:
    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def exec_task(self, username):
        self.process_user(username)

    def calc_distance(self, db_user, prev_login, last_login_user_fields):
        """Compute distance and velocity to alert if impossible travel occurs

        :param db_user: user from db
        :type db_user: object
        :param prev_login: last login saved in db
        :type prev_login: object
        :param last_login_user_fields: dictionary login from elastic
        :type last_login_user_fields: dict

        :return: dictionary with info about the impossible travel alert
        :rtype: dict
        """
        app_config = Config.objects.get(id=1)
        alert_info = {}
        vel = 0
        distance_km = geodesic((prev_login.latitude, prev_login.longitude), (last_login_user_fields["lat"], last_login_user_fields["lon"])).km

        if distance_km > app_config.distance_accepted:
            last_timestamp_datetimeObj_aware = timezone.make_aware(datetime.strptime(last_login_user_fields["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"))
            prev_timestamp_datetimeObj_aware = prev_login.timestamp  # already aware in the db

            diff_timestamp = last_timestamp_datetimeObj_aware - prev_timestamp_datetimeObj_aware
            diff_timestamp_hours = diff_timestamp.total_seconds() / 3600

            if diff_timestamp_hours == 0:
                diff_timestamp_hours = 0.001

            vel = distance_km / diff_timestamp_hours

            if vel > app_config.vel_accepted:
                alert_info["alert_name"] = AlertDetectionType.IMP_TRAVEL.value
                alert_info["alert_desc"] = (
                    f"{AlertDetectionType.IMP_TRAVEL.label} for User: {db_user.username}, at: {last_login_user_fields['timestamp']}, from: {last_login_user_fields['country']}, previous country: {prev_login.country}, distance covered at {int(vel)} Km/h"
                )
        return alert_info, int(vel)

    def update_model(self, db_user, new_login):
        """Update DB entry with last login info

        :param db_user: user from db
        :type db_user: object
        :param new_timestamp: timestamp of last login
        :type new_timestamp: datetime
        :param new_latitude: latitude coordinate of last login
        :type new_latitude: float
        :param new_longitude: longitude coordinate of last login
        :type new_longitude: float
        :param new_country: country of last login
        :type new_country: string
        :param new_user_agent: user_agent of last login
        :type new_user_agent: string
        """
        db_user.login_set.filter(user_agent=new_login["agent"], country=new_login["country"], index=new_login["index"]).update(
            timestamp=new_login["timestamp"],
            latitude=new_login["lat"],
            longitude=new_login["lon"],
            event_id=new_login["id"],
            ip=new_login["ip"],
        )

    def add_new_login(self, db_user, new_login_field):
        """Add new login if there isn't previous login on db relative to that user

        :param db_user: user from db
        :type db_user: object
        :param new_login_field: dictionary with last login info
        :type new_login_field: dict
        """
        Login.objects.create(
            user_id=db_user.id,
            timestamp=new_login_field["timestamp"],
            ip=new_login_field["ip"],
            latitude=new_login_field["lat"],
            longitude=new_login_field["lon"],
            country=new_login_field["country"],
            user_agent=new_login_field["agent"],
            index=new_login_field["index"],
            event_id=new_login_field["id"],
        )

    def add_new_user_ip(self, db_user, source_ip):
        """Add new ip address for the specific user

        :param db_user: user from db
        :type db_user: object
        :param source_ip: new ip address from which the login comes
        :type source_ip: str
        """
        UsersIP.objects.create(user=db_user, ip=source_ip)

    def validate_timestamp(self, dt: datetime) -> str:
        """Convert a datetime object to an ISO 8601 formatted string."""
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
