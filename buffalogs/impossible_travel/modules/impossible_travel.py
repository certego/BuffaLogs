import logging
from datetime import datetime

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from geopy.distance import geodesic
from impossible_travel.models import Alert, Login, User


class Impossible_Travel:
    def _init_(self, **kwargs):
        super()._init_(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def exec_task(self, username):
        self.process_user(username)

    def calc_distance(self, db_user, prev_login, last_login_user_fields):
        """
        Compute distance and velocity to alert if impossible travel occurs
        """
        alert_info = {}
        distance_km = geodesic((prev_login.latitude, prev_login.longitude), (last_login_user_fields["lat"], last_login_user_fields["lon"])).km

        if distance_km > settings.CERTEGO_DISTANCE_KM_ACCEPTED:
            last_timestamp_datetimeObj = self.validate_timestamp(last_login_user_fields["timestamp"])
            prev_timestamp_datetimeObj = prev_login.timestamp

            diff_timestamp = last_timestamp_datetimeObj - prev_timestamp_datetimeObj
            diff_timestamp_hours = diff_timestamp.total_seconds() / 3600

            if diff_timestamp_hours == 0:
                diff_timestamp_hours = 0.001

            vel = distance_km / diff_timestamp_hours

            if vel > settings.CERTEGO_VEL_TRAVEL_ACCEPTED:
                # timestamp_validated = self.validate_timestamp(last_login_user_fields["timestamp"])
                alert_info["alert_name"] = Alert.ruleNameEnum.IMP_TRAVEL
                alert_info[
                    "alert_desc"
                ] = f"{alert_info['alert_name']} for User: {db_user.username},\
                    at: {last_timestamp_datetimeObj}, from:({last_login_user_fields['lat']}, {last_login_user_fields['lon']})"
                return alert_info

    def validate_timestamp(self, time):
        """
        Validate timestamp format
        """
        try:
            timestamp_format = "%Y-%m-%dT%H:%M:%S.%fZ"
            timestamp_datetimeObj = timezone.datetime.strptime(str(time), timestamp_format)
        except (ValueError, TypeError) as e:
            if "decoding to str" in str(e):
                timestamp_format = "%Y-%m-%dT%H:%M:%S.000Z"
                timestamp_datetimeObj = timezone.datetime.strptime(time, timestamp_format)
            if "does not match format" in str(e):
                timestamp_format = "%Y-%m-%d %H:%M:%S"
                timestamp_datetimeObj = timezone.datetime.strptime(str(time), timestamp_format)
        return timestamp_datetimeObj

    def add_new_user(self, u):
        try:
            User.objects.create(username=u)
        except IntegrityError as e:
            pass
            # self.logger.info(f"User already exist {e}")

    def update_model(self, db_user, new_timestamp, new_latitude, new_longitude, new_country, new_user_agent):
        """
        Update DB entry with last login info
        """
        db_user.login_set.filter(user_agent=new_user_agent, country=new_country).update(
            timestamp=new_timestamp, latitude=new_latitude, longitude=new_longitude, country=new_country, user_agent=new_user_agent
        )

    def add_new_login(self, db_user, new_login_field):
        Login.objects.create(
            user_id=db_user.id,
            timestamp=new_login_field["timestamp"],
            latitude=new_login_field["lat"],
            longitude=new_login_field["lon"],
            country=new_login_field["country"],
            user_agent=new_login_field["agent"],
        )
