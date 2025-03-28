import os
from pathlib import Path

ENVIRONMENT_DOCKER = "docker"
ENVIRONMENT_DEBUG = "debug"

CERTEGO_REPO_DIR = Path(__file__).resolve().parent.parent.parent.parent
CERTEGO_DJANGO_PROJ_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# If BUFFALOGS_ENV not set, it will default to debug
CERTEGO_BUFFALOGS_ENVIRONMENT = os.environ.get("BUFFALOGS_ENV", ENVIRONMENT_DEBUG)

# Database Configuration
CERTEGO_BUFFALOGS_POSTGRES_DB = os.environ.get("BUFFALOGS_POSTGRES_DB", "buffalogs")
CERTEGO_BUFFALOGS_POSTGRES_USER = os.environ.get("BUFFALOGS_POSTGRES_USER", "default_user")
CERTEGO_BUFFALOGS_POSTGRES_PASSWORD = os.environ.get("BUFFALOGS_POSTGRES_PASSWORD", "ahamed@2471")
CERTEGO_BUFFALOGS_POSTGRES_PORT = os.environ.get("BUFFALOGS_POSTGRES_PORT", "5432")

# Elasticsearch Configuration
CERTEGO_BUFFALOGS_ELASTIC_INDEX = os.environ.get("BUFFALOGS_ELASTIC_INDEX", "weblog-*,cloud-*,fw-proxy-*,filebeat-*")

# Secret Key - IMPORTANT: Use a strong, unique secret key in production
CERTEGO_BUFFALOGS_SECRET_KEY = os.environ.get("BUFFALOGS_SECRET_KEY", "django-insecure-am9z-fi-x*aqxlb-@abkhb@pu!0da%0a77h%-8d(dwzrrktwhu")

# Configuration Paths
CERTEGO_BUFFALOGS_CONFIG_PATH = os.path.join(CERTEGO_DJANGO_PROJ_BASE_DIR, "../config/")
CERTEGO_BUFFALOGS_CONFIG_INGESTION_PATH = os.path.join(CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/")

# Alert and Security Configurations
CERTEGO_BUFFALOGS_IGNORED_USERS = ["Not Available", "N/A"]
CERTEGO_BUFFALOGS_ENABLED_USERS = []
CERTEGO_BUFFALOGS_ALLOWED_COUNTRIES = []
CERTEGO_BUFFALOGS_IGNORED_IPS = ["127.0.0.1"]
CERTEGO_BUFFALOGS_IGNORED_ISPS = []
CERTEGO_BUFFALOGS_VIP_USERS = []

# Travel and Login Threshold Configurations
CERTEGO_BUFFALOGS_DISTANCE_KM_ACCEPTED = 100
CERTEGO_BUFFALOGS_VEL_TRAVEL_ACCEPTED = 300
CERTEGO_BUFFALOGS_ATYPICAL_COUNTRY_DAYS = 30
CERTEGO_BUFFALOGS_USER_MAX_DAYS = 60
CERTEGO_BUFFALOGS_LOGIN_MAX_DAYS = 45
CERTEGO_BUFFALOGS_ALERT_MAX_DAYS = 45
CERTEGO_BUFFALOGS_IP_MAX_DAYS = 45
CERTEGO_BUFFALOGS_MOBILE_DEVICES = ["iOS", "Android", "Windows Phone"]

# Environment-specific Configurations
if CERTEGO_BUFFALOGS_ENVIRONMENT == ENVIRONMENT_DOCKER:
    CERTEGO_ELASTICSEARCH = os.environ.get("CERTEGO_ELASTICSEARCH", "http://elasticsearch:9200")
    CERTEGO_BUFFALOGS_DB_HOSTNAME = "postgres"
    CERTEGO_BUFFALOGS_CONFIG_PATH = "/opt/certego/config/"
    CERTEGO_DEBUG = False
    CERTEGO_BUFFALOGS_STATIC_ROOT = "/var/www/static/"
    CERTEGO_BUFFALOGS_LOG_PATH = "/var/log"
    CERTEGO_BUFFALOGS_RABBITMQ_HOST = "rabbitmq"
    CERTEGO_BUFFALOGS_RABBITMQ_URI = f"amqp://guest:guest@{CERTEGO_BUFFALOGS_RABBITMQ_HOST}/"

elif CERTEGO_BUFFALOGS_ENVIRONMENT == ENVIRONMENT_DEBUG:
    CERTEGO_ELASTICSEARCH = os.environ.get("CERTEGO_ELASTICSEARCH", "http://localhost:9200")
    CERTEGO_BUFFALOGS_DB_HOSTNAME = "localhost"
    CERTEGO_BUFFALOGS_CONFIG_PATH = "../config/"
    CERTEGO_DEBUG = True
    CERTEGO_BUFFALOGS_STATIC_ROOT = "impossible_travel/static/"
    CERTEGO_BUFFALOGS_LOG_PATH = "../logs"
    CERTEGO_BUFFALOGS_RABBITMQ_HOST = "localhost"
    CERTEGO_BUFFALOGS_RABBITMQ_URI = f"amqp://guest:guest@{CERTEGO_BUFFALOGS_RABBITMQ_HOST}/"

else:
    raise ValueError(f"Environment not supported: {CERTEGO_BUFFALOGS_ENVIRONMENT}")