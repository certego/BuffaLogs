import os
from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone
from elasticsearch_dsl import Search, connections
from impossible_travel.alerting.alert_factory import AlertFactory
from impossible_travel.constants import AlertDetectionType, ComparisonType, UserRiskScoreType
from impossible_travel.models import Alert, Config, Login, TaskSettings, User, UsersIP
from impossible_travel.modules import alert_filter, impossible_travel, login_from_new_country, login_from_new_device

logger = get_task_logger(__name__)
BLOCKLIST_IP_FILE = os.path.join(os.path.dirname(__file__), "../../config/buffalogs/blocklisted_ips.txt")


@shared_task(name="BuffalogsCleanModelsPeriodicallyTask")
def clean_models_periodically():
    """Delete old data in the models"""
    app_config = Config.objects.get(id=1)
    now = timezone.now()
    delete_user_time = now - timedelta(days=app_config.user_max_days)
    User.objects.filter(updated__lte=delete_user_time).delete()

    delete_login_time = now - timedelta(days=app_config.login_max_days)
    Login.objects.filter(updated__lte=delete_login_time).delete()

    delete_alert_time = now - timedelta(days=app_config.alert_max_days)
    Alert.objects.filter(updated__lte=delete_alert_time).delete()

    delete_ip_time = now - timedelta(days=app_config.ip_max_days)
    UsersIP.objects.filter(updated__lte=delete_ip_time).delete()


def update_risk_level(db_user: User, triggered_alert: Alert):
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
        app_config = Config.objects.get(id=1)
        config_threshold_comparison = UserRiskScoreType.compare_risk(app_config.threshold_user_risk_alert, new_risk_level)

        if config_threshold_comparison in [ComparisonType.EQUAL, ComparisonType.HIGHER]:
            alert_info = {
                "alert_name": AlertDetectionType.USER_RISK_THRESHOLD.value,
                "alert_desc": f"{AlertDetectionType.USER_RISK_THRESHOLD.label} for User: {db_user.username}, "
                f"who changed risk_score from {current_risk_score} to {new_risk_level}",
            }
            logger.info(f"Upgraded risk level for User: {db_user.username} to level: {new_risk_level}, " f"detected {db_user.alert_set.count()} alerts")
            set_alert(
                db_user=db_user,
                login_alert=triggered_alert.login_raw_data,
                alert_info=alert_info,
            )

            return True
    return False


def set_alert(db_user: User, login_alert: dict, alert_info: dict):
    """Save the alert on db and logs it

    :param db_user: user from db
    :type db_user: object
    :param login_alert: dictionary login from elastic
    :type login_alert: dict
    :param alert_info: dictionary with alert info
    :type alert_info: dict
    """
    logger.info(f"ALERT {alert_info['alert_name']} for User: {db_user.username} at: {login_alert['timestamp']}")
    alert = Alert.objects.create(
        user_id=db_user.id,
        login_raw_data=login_alert,
        name=alert_info["alert_name"],
        description=alert_info["alert_desc"],
    )
    # update user.risk_score if necessary
    update_risk_level(db_user=alert.user, triggered_alert=alert)
    # check filters
    alert_filter.match_filters(alert=alert)
    alert.save()
    return alert


def check_fields(db_user: User, fields: list):
    """
    Call the relative function to check the different types of alerts, based on the existing fields

    :param db_user: user from DB
    :type db_user: User object
    :param fields: list of login data of the user
    :type fields: list
    """
    imp_travel = impossible_travel.Impossible_Travel()
    new_dev = login_from_new_device.Login_New_Device()
    new_country = login_from_new_country.Login_New_Country()

    app_config, _ = Config.objects.get_or_create(id=1)

    for login in fields:
        if login.get("intelligence_category", None) == "anonymizer":
            alert_info = {
                "alert_name": AlertDetectionType.ANONYMOUS_IP_LOGIN.value,
                "alert_desc": f"{AlertDetectionType.ANONYMOUS_IP_LOGIN.label} from IP: {login['ip']} by User: {db_user.username}",
            }
            set_alert(db_user, login_alert=login, alert_info=alert_info)
        if login["lat"] and login["lon"]:
            if Login.objects.filter(user_id=db_user.id, index=login["index"]).exists():
                agent_alert = False
                country_alert = False
                if login["agent"]:
                    agent_alert = new_dev.check_new_device(db_user, login)
                    if agent_alert:
                        set_alert(db_user, login_alert=login, alert_info=agent_alert)

                if login["country"]:
                    country_alert = new_country.check_country(db_user, login, app_config)
                    if country_alert:
                        set_alert(db_user, login_alert=login, alert_info=country_alert)

                if not db_user.usersip_set.filter(ip=login["ip"]).exists():
                    last_user_login = db_user.login_set.latest("timestamp")
                    logger.info(f"Calculating impossible travel: {login['id']}")
                    travel_alert, travel_vel = imp_travel.calc_distance(
                        db_user,
                        prev_login=last_user_login,
                        last_login_user_fields=login,
                    )
                    if travel_alert:
                        new_alert = set_alert(db_user, login_alert=login, alert_info=travel_alert)
                        new_alert.login_raw_data["buffalogs"] = {}
                        new_alert.login_raw_data["buffalogs"]["start_country"] = last_user_login.country
                        new_alert.login_raw_data["buffalogs"]["avg_speed"] = travel_vel
                        new_alert.login_raw_data["buffalogs"]["start_lat"] = last_user_login.latitude
                        new_alert.login_raw_data["buffalogs"]["start_lon"] = last_user_login.longitude
                        new_alert.save()
                    #   Add the new ip address from which the login comes to the db
                    imp_travel.add_new_user_ip(db_user, login["ip"])

                if Login.objects.filter(
                    user=db_user,
                    index=login["index"],
                    country=login["country"],
                    user_agent=login["agent"],
                ).exists():
                    logger.info(f"Updating login {login['id']} for user: {db_user.username}")
                    imp_travel.update_model(db_user, login)
                else:
                    logger.info(f"Adding new login {login['id']} for user: {db_user.username}")
                    imp_travel.add_new_login(db_user, login)

            else:
                logger.info(f"Creating new login {login['id']} for user: {db_user.username}")
                imp_travel.add_new_login(db_user, login)
                imp_travel.add_new_user_ip(db_user, login["ip"])
        else:
            logger.info(f"No latitude or longitude for User {db_user.username}")


def process_user(db_user, start_date, end_date):
    """Get info for each user login and normalization

    :param db_user: user from db
    :type db_user: object
    :param start_date: start date of analysis
    :type start_date: timezone
    :param end_date: finish date of analysis
    :type end_date: timezone
    """
    fields = []
    s = (
        Search(index=settings.CERTEGO_BUFFALOGS_ELASTIC_INDEX)
        .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
        .query("match", **{"user.name": db_user.username})
        .query("match", **{"event.outcome": "success"})
        .query("match", **{"event.type": "start"})
        .query("exists", field="source.ip")
        .source(
            includes=[
                "user.name",
                "@timestamp",
                "source.geo.location.lat",
                "source.geo.location.lon",
                "source.geo.country_name",
                "source.as.organization.name",
                "user_agent.original",
                "_index",
                "source.ip",
                "_id",
                "source.intelligence_category",
            ]
        )
        .sort("@timestamp")  # from the oldest to the most recent login
        .extra(size=10000)
    )
    response = s.execute()
    logger.info(f"Got {len(response)} logins for user {db_user.username}")
    for hit in response:
        if "source" in hit:
            tmp = {"timestamp": hit["@timestamp"]}
            tmp["id"] = hit.meta["id"]
            if hit.meta["index"].split("-")[0] == "fw":
                tmp["index"] = "fw-proxy"
            else:
                tmp["index"] = hit.meta["index"].split("-")[0]
            tmp["ip"] = hit["source"]["ip"]
            if "user_agent" in hit:
                tmp["agent"] = hit["user_agent"]["original"]
            else:
                tmp["agent"] = ""
            if "as" in hit.source:
                tmp["organization"] = hit["source"]["as"]["organization"]["name"]
            if "geo" in hit.source:
                if "location" in hit.source.geo and "country_name" in hit.source.geo:
                    tmp["lat"] = hit["source"]["geo"]["location"]["lat"]
                    tmp["lon"] = hit["source"]["geo"]["location"]["lon"]
                    tmp["country"] = hit["source"]["geo"]["country_name"]
                else:
                    tmp["lat"] = None
                    tmp["lon"] = None
                    tmp["country"] = ""
                fields.append(tmp)  # up to now: no geo info --> login discard
    check_fields(db_user, fields)


@shared_task(name="BuffalogsProcessLogsTask")
def process_logs():
    """Find all user logged in between that time range"""
    now = timezone.now()
    process_task, _ = TaskSettings.objects.get_or_create(
        task_name=process_logs.__name__,
        defaults={
            "end_date": timezone.now() - timedelta(minutes=1),
            "start_date": timezone.now() - timedelta(minutes=30),
        },
    )
    if (now - process_task.end_date).days < 1:
        # Recovering old data avoiding task time limit
        for _ in range(6):
            start_date = process_task.end_date
            end_date = start_date + timedelta(minutes=30)
            if end_date > now:
                break
            process_task.start_date = start_date
            process_task.end_date = end_date
            process_task.save()
            exec_process_logs(start_date, end_date)

    else:
        logger.info(f"Data lost from {process_task.end_date} to now")
        end_date = timezone.now() - timedelta(minutes=1)
        start_date = end_date - timedelta(minutes=30)
        process_task.start_date = start_date
        process_task.end_date = end_date
        process_task.save()
        exec_process_logs(start_date, end_date)


@shared_task(name="NotifyAlertsTask")
def notify_alerts():
    alert = AlertFactory().get_alert_class()
    alert.notify_alerts()


def exec_process_logs(start_date, end_date):
    """Starting the execution for the given time range

    :param start_date: Start datetime
    :type start_date: datetime
    :param end_date: End datetime
    :type end_date: datetime
    """
    logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
    connections.create_connection(hosts=settings.CERTEGO_ELASTICSEARCH, timeout=90, verify_certs=False)
    s = (
        Search(index=settings.CERTEGO_BUFFALOGS_ELASTIC_INDEX)
        .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
        .query("match", **{"event.category": "authentication"})
        .query("match", **{"event.outcome": "success"})
        .query("match", **{"event.type": "start"})
        .query("exists", field="user.name")
    )
    s.aggs.bucket("login_user", "terms", field="user.name", size=10000)
    response = s.execute()
    try:
        logger.info(f"Successfully got {len(response.aggregations.login_user.buckets)} users")
        for user in response.aggregations.login_user.buckets:
            db_user, created = User.objects.get_or_create(username=user.key)
            if not created:
                # Saving user to update updated_at field
                db_user.save()
            process_user(db_user, start_date, end_date)
    except AttributeError:
        logger.info("No users login aggregation found")


@shared_task(name="CheckBlocklistedIPsTask")
def check_blocklisted_ips():
    """Check for successful logins from blocklisted IPs"""
    logger.info("Starting blocklisted IPs check")

    # Load blocklisted IPs
    try:
        with open(BLOCKLIST_IP_FILE, "r") as f:
            blocklisted_ips = {line.strip() for line in f if line.strip()}
    except IOError as e:
        logger.error(f"Error reading blocklist file: {str(e)}")
        raise ImproperlyConfigured(f"Blocklist file not found: {BLOCKLIST_IP_FILE}")

    if not blocklisted_ips:
        logger.info("No blocklisted IPs found in file")
        return

    # Calculate time range (last 30 minutes)
    end_date = timezone.now()
    start_date = end_date - timedelta(minutes=30)

    # Create Elasticsearch connection
    connections.create_connection(hosts=settings.CERTEGO_ELASTICSEARCH, timeout=90, verify_certs=False)

    # Search for successful logins from blocklisted IPs
    s = (
        Search(index=settings.CERTEGO_BUFFALOGS_ELASTIC_INDEX)
        .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
        .query("match", **{"event.outcome": "success"})
        .query("match", **{"event.type": "start"})
        .query("terms", **{"source.ip": list(blocklisted_ips)})
        .source(
            [
                "user.name",
                "source.ip",
                "@timestamp",
                "_id",
                "source.geo.location.lat",
                "source.geo.location.lon",
                "source.geo.country_name",
                "user_agent.original",
            ]
        )
    )

    response = s.execute()

    logger.info(f"Found {len(response)} logins from blocklisted IPs")

    for hit in response:
        # Converted Hit to dictionary for safe access
        hit_dict = hit.to_dict() if hasattr(hit, "to_dict") else hit

        # Safely accessed user and name using dictionary methods
        user = hit_dict.get("user", {})
        if not user or "name" not in user:
            logger.warning("Hit missing 'user' or 'user.name', skipping")
            continue
        username = user["name"]

        source = hit_dict.get("source", {})
        ip = source.get("ip", "")
        if not ip:
            logger.warning("Hit missing 'source.ip', skipping")
            continue

        timestamp = hit_dict.get("@timestamp")
        if not timestamp:
            logger.warning("Hit missing '@timestamp', skipping")
            continue

        event_id = hit_dict.get("_id", "")
        index = hit_dict.get("_index", "").split("-")[0]

        # Handle geo data with safe access
        source_geo = source.get("geo", {})
        location = source_geo.get("location", {})
        latitude = location.get("lat")
        longitude = location.get("lon")
        country = source_geo.get("country_name", "")
        user_agent = hit_dict.get("user_agent", {}).get("original", "")

        db_user, _ = User.objects.get_or_create(username=username)

        # Prepare login data
        login_data = {
            "user": db_user.username,
            "timestamp": timestamp.isoformat(),
            "ip": ip,
            "event_id": event_id,
            "index": index,
            "latitude": latitude,
            "longitude": longitude,
            "country": country,
            "user_agent": user_agent,
        }

        logger.info(f"Processing login for user {username} from IP {ip} at {timestamp.isoformat()}")

        # Create alert
        alert_info = {
            "alert_name": AlertDetectionType.BLOCKLISTED_IP_LOGIN.value,
            "alert_desc": (f"{AlertDetectionType.BLOCKLISTED_IP_LOGIN.label} {ip} " f"by user {username} at {timestamp} "),
        }

        set_alert(db_user=db_user, login_alert=login_data, alert_info=alert_info)
