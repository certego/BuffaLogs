import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from elasticsearch_dsl import Search, connections
from impossible_travel.models import Alert, Config, Login, TaskSettings, User
from impossible_travel.modules import impossible_travel, login_from_new_country, login_from_new_device

logger = logging.getLogger()


def clear_models_periodically():
    """
    Clear DB models
    """
    now = timezone.now()
    delete_user_time = now - timedelta(days=settings.CERTEGO_USER_MAX_DAYS)
    User.objects.filter(updated__lte=delete_user_time).delete()

    delete_login_time = now - timedelta(days=settings.CERTEGO_LOGIN_MAX_DAYS)
    Login.objects.filter(updated__lte=delete_login_time).delete()

    delete_alert_time = now - timedelta(days=settings.CERTEGO_ALERT_MAX_DAYS)
    Alert.objects.filter(updated__lte=delete_alert_time).delete()


@shared_task(name="UpdateRiskLevelTask")
def update_risk_level():
    clear_models_periodically()
    with transaction.atomic():
        for u in User.objects.annotate(Count("alert")):
            alerts_num = u.alert__count
            if alerts_num == 0:
                tmp = User.riskScoreEnum.NO_RISK
            elif 1 <= alerts_num <= 2:
                tmp = User.riskScoreEnum.LOW
            elif 3 <= alerts_num <= 4:
                tmp = User.riskScoreEnum.MEDIUM
            else:
                logger.info(f"{User.riskScoreEnum.HIGH} risk level for User: {u.username}")
                tmp = User.riskScoreEnum.HIGH
            if u.risk_score != tmp:
                u.risk_score = tmp
                u.save()


def set_alert(db_user, login_alert, alert_info):
    """
    Save the alert on db and logs it
    """
    logger.info(
        f"ALERT {alert_info['alert_name']} for User:{db_user.username} at:{login_alert['timestamp']} from {login_alert['country']} from device:{login_alert['agent']}"
    )
    alert = Alert.objects.create(user_id=db_user.id, login_raw_data=login_alert, name=alert_info["alert_name"], description=alert_info["alert_desc"])
    if Config.objects.filter(vip_users__contains=[db_user.username]):
        alert.is_vip = True
        alert.save()


def check_fields(db_user, fields):
    """
    Call the relative function if user_agents and/or geoip exist
    """
    imp_travel = impossible_travel.Impossible_Travel()
    new_dev = login_from_new_device.Login_New_Device()
    new_country = login_from_new_country.Login_New_Country()

    for login in fields:
        if login["lat"] and login["lon"]:
            if Login.objects.filter(user_id=db_user.id, index=login["index"]).exists():
                agent_alert = False
                country_alert = False
                if login["agent"]:
                    agent_alert = new_dev.check_new_device(db_user, login)
                    if agent_alert:
                        set_alert(db_user, login, agent_alert)

                if login["country"]:
                    country_alert = new_country.check_country(db_user, login)
                    if country_alert and not Config.objects.filter(allowed_countries__contains=[login["country"]]):
                        set_alert(db_user, login, country_alert)

                travel_alert = imp_travel.calc_distance(db_user, db_user.login_set.last(), login)
                if travel_alert:
                    set_alert(db_user, login, travel_alert)

                if Login.objects.filter(user=db_user, index=login["index"], country=login["country"], user_agent=login["agent"]).exists():
                    imp_travel.update_model(db_user, login["timestamp"], login["lat"], login["lon"], login["country"], login["agent"])
                else:
                    imp_travel.add_new_login(db_user, login)

            else:
                imp_travel.add_new_login(db_user, login)
        else:
            logger.info(f"No latitude or longitude for User {db_user.username}")


def process_user(db_user, start_date, end_date):
    """
    Get info for each user login and normalization
    """
    fields = []
    s = (
        Search(index=settings.CERTEGO_ELASTIC_INDEX)
        .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
        .query("match", **{"user.name": db_user.username})
        .query("match", **{"event.outcome": "success"})
        .query("match", **{"event.type": "start"})
        .source(
            includes=[
                "user.name",
                "@timestamp",
                "source.geo.location.lat",
                "source.geo.location.lon",
                "source.geo.country_name",
                "user_agent.original",
                "_index",
            ]
        )
        .sort("@timestamp")
        .extra(size=10000)
    )
    response = s.execute()
    logger.info(f"Got {len(response)} logins for user {db_user.username}")
    for hit in response:
        tmp = {"timestamp": hit["@timestamp"]}
        tmp["index"] = hit.meta["index"].split("-")[0]
        if "location" in hit["source"]["geo"] and "country_name" in hit["source"]["geo"]:
            tmp["lat"] = hit["source"]["geo"]["location"]["lat"]
            tmp["lon"] = hit["source"]["geo"]["location"]["lon"]
            tmp["country"] = hit["source"]["geo"]["country_name"]
        else:
            tmp["lat"] = None
            tmp["lon"] = None
            tmp["country"] = ""
        if "user_agent" in hit:
            tmp["agent"] = hit["user_agent"]["original"]
        else:
            tmp["agent"] = ""
        fields.append(tmp)
    check_fields(db_user, fields)


@shared_task(name="BuffalogsProcessLogsTask")
def process_logs():
    """Find all user logged in between that time range"""
    now = timezone.now()
    process_task, op_result = TaskSettings.objects.get_or_create(
        task_name=process_logs.__name__, defaults={"end_date": timezone.now() - timedelta(minutes=1), "start_date": timezone.now() - timedelta(minutes=30)}
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


def exec_process_logs(start_date, end_date):
    logger.info(f"Starting at:{start_date} Finishing at:{end_date}")
    connections.create_connection(hosts=settings.CERTEGO_ELASTICSEARCH, timeout=90)
    s = (
        Search(index=settings.CERTEGO_ELASTIC_INDEX)
        .filter("range", **{"@timestamp": {"gte": start_date, "lt": end_date}})
        .query("match", **{"event.category": "authentication"})
        .query("match", **{"event.outcome": "success"})
        .query("match", **{"event.type": "start"})
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
        logger.info("No login_user aggregation found")
