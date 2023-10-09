import os
from pathlib import Path

ENVIRONMENT_DOCKER = "docker"
ENVIRONMENT_DEBUG = "debug"

CERTEGO_REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent
CERTEGO_DJANGO_PROJ_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# If NS_ENV not set, it will be set to debug
CERTEGO_BUFFALOGS_ENVIRONMENT = os.environ.get("BUFFALOGS_ENV", "debug")
CERTEGO_BUFFALOGS_POSTGRES_DB = os.environ.get("BUFFALOGS_POSTGRES_DB", "buffalogs")
CERTEGO_BUFFALOGS_POSTGRES_USER = os.environ.get("BUFFALOGS_POSTGRES_USER", "default_user")
CERTEGO_BUFFALOGS_POSTGRES_PASSWORD = os.environ.get("BUFFALOGS_POSTGRES_PASSWORD", "password")
CERTEGO_BUFFALOGS_POSTGRES_PORT = os.environ.get("BUFFALOGS_POSTGRES_PORT", "5432")
CERTEGO_BUFFALOGS_ELASTIC_INDEX = os.environ.get("BUFFALOGS_ELASTIC_INDEX", "weblog-*,cloud-*,fw-proxy-*,filebeat-*")
CERTEGO_BUFFALOGS_SECRET_KEY = os.environ.get("BUFFALOGS_SECRET_KEY", "django-insecure-am9z-fi-x*aqxlb-@abkhb@pu!0da%0a77h%-8d(dwzrrktwhu")

if CERTEGO_BUFFALOGS_ENVIRONMENT == ENVIRONMENT_DOCKER:

    CERTEGO_ELASTICSEARCH = os.environ.get("CERTEGO_ELASTICSEARCH", "http://elasticsearch:9200/")
    CERTEGO_BUFFALOGS_DB_HOSTNAME = "postgres"
    CERTEGO_DEBUG = False
    CERTEGO_BUFFALOGS_STATIC_ROOT = "/var/www/static/"
    CERTEGO_BUFFALOGS_LOG_PATH = "/var/log"
    CERTEGO_BUFFALOGS_RABBITMQ_HOST = "rabbitmq"
    CERTEGO_BUFFALOGS_RABBITMQ_URI = f"amqp://guest:guest@{CERTEGO_BUFFALOGS_RABBITMQ_HOST}/"

elif CERTEGO_BUFFALOGS_ENVIRONMENT == ENVIRONMENT_DEBUG:
    CERTEGO_ELASTICSEARCH = os.environ.get("CERTEGO_ELASTICSEARCH", "http://localhost:9200/")
    CERTEGO_BUFFALOGS_DB_HOSTNAME = "localhost"
    CERTEGO_DEBUG = True
    CERTEGO_BUFFALOGS_STATIC_ROOT = "impossible_travel/static/"
    CERTEGO_BUFFALOGS_LOG_PATH = "../logs"
    CERTEGO_BUFFALOGS_RABBITMQ_HOST = "localhost"
    CERTEGO_BUFFALOGS_RABBITMQ_URI = f"amqp://guest:guest@{CERTEGO_BUFFALOGS_RABBITMQ_HOST}//"

else:
    raise ValueError(f"Environment not supported: {CERTEGO_BUFFALOGS_ENVIRONMENT}")
