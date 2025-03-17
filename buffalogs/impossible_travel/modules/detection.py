from datetime import datetime

from celery.utils.log import get_task_logger
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone
from geopy.distance import geodesic
from impossible_travel.constants import AlertDetectionType, ComparisonType, UserRiskScoreType
from impossible_travel.models import Alert, Config, Login, User, UsersIP
from impossible_travel.modules import alert_filter

logger = get_task_logger(__name__)


def update_risk_level(db_user: User, triggered_alert: Alert, app_config: Config):
    """Update user risk level depending on how many alerts were triggered

    :param db_user: user from DB
    :type db_user: User object
    :param triggered_alert: alert that has just been triggered
    :type alert: Alert object
    """
    with transaction.atomic():
        current_risk_score = db_user.risk_score
        new_risk_level = UserRiskScoreType.get_risk_level(db_user.alert_set.count())

        # update the risk_score anyway in order to keep the users up-to-date each time they are seen by the system
        db_user.risk_score = new_risk_level
        db_user.save()

        risk_comparison = UserRiskScoreType.compare_risk(current_risk_score, new_risk_level)
        if risk_comparison in [ComparisonType.LOWER, ComparisonType.EQUAL]:
            return False  # risk_score doesn't increased, so no USER_RISK_THRESHOLD alert

        # if the new_risk_level is higher than the current one
        # and the new_risk_level is higher or equal than the threshold set in the config.threshold_user_risk_alert
        # send the USER_RISK_THRESHOLD alert
        config_threshold_comparison = UserRiskScoreType.compare_risk(app_config.threshold_user_risk_alert, new_risk_level)

        if config_threshold_comparison in [ComparisonType.EQUAL, ComparisonType.HIGHER]:
            alert_info = {
                "alert_name": AlertDetectionType.USER_RISK_THRESHOLD.value,
                "alert_desc": f"{AlertDetectionType.USER_RISK_THRESHOLD.label} for User: {db_user.username}, "
                f"who changed risk_score from {current_risk_score} to {new_risk_level}",
            }
            logger.info(f"Upgraded risk level for User: {db_user.username} to level: {new_risk_level}, " f"detected {db_user.alert_set.count()} alerts")
            set_alert(db_user=db_user, login_alert=triggered_alert.login_raw_data, alert_info=alert_info, app_config=app_config)

            return True


def set_alert(db_user: User, login_alert: dict, alert_info: dict, app_config: Config):
    """Save the alert on db and logs it

    :param db_user: user from db
    :type db_user: object
    :param login_alert: dictionary login from elastic
    :type login_alert: dict
    :param alert_info: dictionary with alert info
    :type alert_info: dict
    """
    logger.info(f"ALERT {alert_info['alert_name']} for User: {db_user.username} at: {login_alert['timestamp']}")
    alert = Alert.objects.create(user=db_user, login_raw_data=login_alert, name=alert_info["alert_name"], description=alert_info["alert_desc"])
    # update user.risk_score if necessary
    update_risk_level(db_user=alert.user, triggered_alert=alert, app_config=app_config)
    # check filters
    alert_filter.match_filters(alert=alert, app_config=app_config)
    alert.save()
    return alert


def check_fields(db_user: User, fields: list):
    """Check different types of alerts based on login fields.

    :param db_user: user from DB
    :type db_user: User object
    :param fields: list of login data of the user
    :type fields: list
    """

    db_config, _ = Config.objects.get_or_create(id=1)

    for login in fields:
        if login.get("intelligence_category", None) == "anonymizer":
            # check the possible alert: ANONYMOUS_IP_LOGIN
            alert_info = {
                "alert_name": AlertDetectionType.ANONYMOUS_IP_LOGIN.value,
                "alert_desc": f"{AlertDetectionType.ANONYMOUS_IP_LOGIN.label} from IP: {login['ip']} by User: {db_user.username}",
            }
            set_alert(db_user, login_alert=login, alert_info=alert_info, app_config=db_config)
        if login["lat"] and login["lon"]:
            if Login.objects.filter(user_id=db_user.id, index=login["index"]).exists():
                agent_alert = False
                country_alert = False
                if login["agent"]:
                    # check the possible alert: NEW_DEVICE
                    agent_alert = check_new_device(db_user, login)
                    if agent_alert:
                        set_alert(db_user, login_alert=login, alert_info=agent_alert, app_config=db_config)

                if login["country"]:
                    # check the possible alerts: NEW_COUNTRY / ATYPICAL_COUNTRY
                    country_alert = check_country(db_user, login, db_config)
                    if country_alert:
                        set_alert(db_user, login_alert=login, alert_info=country_alert, app_config=db_config)

                if not db_user.usersip_set.filter(ip=login["ip"]).exists():
                    last_user_login = db_user.login_set.latest("timestamp")
                    logger.info(f"Calculating impossible travel: {login['id']}")
                    travel_alert, travel_vel = calc_distance_impossible_travel(db_user, prev_login=last_user_login, last_login_user_fields=login)
                    if travel_alert:
                        new_alert = set_alert(db_user, login_alert=login, alert_info=travel_alert, app_config=db_config)
                        new_alert.login_raw_data["buffalogs"] = {}
                        new_alert.login_raw_data["buffalogs"]["start_country"] = last_user_login.country
                        new_alert.login_raw_data["buffalogs"]["avg_speed"] = travel_vel
                        new_alert.login_raw_data["buffalogs"]["start_lat"] = last_user_login.latitude
                        new_alert.login_raw_data["buffalogs"]["start_lon"] = last_user_login.longitude
                        new_alert.save()
                    #   Add the new ip address from which the login comes to the db
                    UsersIP.objects.create(user=db_user, ip=login["ip"])

                if Login.objects.filter(user=db_user, index=login["index"], country=login["country"], user_agent=login["agent"]).exists():
                    logger.info(f"Updating login {login['id']} for user: {db_user.username}")
                    update_model(db_user, login)
                else:
                    logger.info(f"Adding new login {login['id']} for user: {db_user.username}")
                    add_new_login(db_user, login)

            else:
                logger.info(f"Creating new login {login['id']} for user: {db_user.username}")
                add_new_login(db_user, login)
                UsersIP.objects.create(user=db_user, ip=login["ip"])
        else:
            logger.info(f"No latitude or longitude for User {db_user.username}")


def check_country(db_user: User, login_field: dict, app_config: Config) -> dict:
    """
    Check Login from new Country and send alert
    """
    alert_info = {}
    # check "New Country" alert
    if db_user.login_set.filter(country=login_field["country"]).count() == 0:
        alert_info["alert_name"] = AlertDetectionType.NEW_COUNTRY.value
        alert_info["alert_desc"] = (
            f"{AlertDetectionType.NEW_COUNTRY.label} for User: {db_user.username}, at: {login_field['timestamp']}, from: {login_field['country']}"
        )
    # check "Atypical Country" alert
    elif (
        datetime.fromisoformat(login_field["timestamp"]) - db_user.login_set.filter(country=login_field["country"]).last().timestamp
    ).days >= app_config.atypical_country_days:
        alert_info["alert_name"] = AlertDetectionType.ATYPICAL_COUNTRY.value
        alert_info["alert_desc"] = (
            f"{AlertDetectionType.ATYPICAL_COUNTRY.label} for User: {db_user.username}, at: {login_field['timestamp']}, from: {login_field['country']}"
        )
    return alert_info


def check_new_device(db_user, login_field):
    """
    Check Login from new Device and send alert
    """
    alert_info = {}
    if db_user.login_set.filter(user_agent=login_field["agent"]).count() == 0:
        timestamp = login_field["timestamp"]
        alert_info["alert_name"] = AlertDetectionType.NEW_DEVICE.value
        alert_info["alert_desc"] = f"{AlertDetectionType.NEW_DEVICE.label} for User: {db_user.username}, at: {timestamp}"
        return alert_info


def add_new_login(db_user, new_login_field):
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


def update_model(db_user, new_login):
    """Update DB entry with last login info (for same: User - index - country - agent)

    :param db_user: user from DB
    :type db_user: User object
    :param new_login: new login info to update in to the DB
    :type new_login: dict
    """
    try:
        db_user.login_set.filter(user_agent=new_login["agent"], country=new_login["country"], index=new_login["index"]).update(
            timestamp=new_login["timestamp"],
            latitude=new_login["lat"],
            longitude=new_login["lon"],
            event_id=new_login["id"],
            ip=new_login["ip"],
        )
    except IntegrityError as e:
        logger.error(
            f"Can't update a previous login in the DB for the User: {db_user.username} with the new login (event_id: {new_login['id']}) for an Integrity error: {e}"
        )
    except DatabaseError as e:
        logger.error(
            f"Can't update a previous login in the DB for the User: {db_user.username} with the new login (event_id: {new_login['id']}) for a Database error: {e}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error while updating a previous login in the DB for the User: {db_user.username} with the new login (event_id: {new_login['id']}): {e}"
        )


def calc_distance_impossible_travel(db_user, prev_login, last_login_user_fields):
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
