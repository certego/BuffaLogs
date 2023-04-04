"""
Django settings for buffalogs project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path

from celery.schedules import crontab

from .certego import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = CERTEGO_SECRET_KEY
DEBUG = CERTEGO_DEBUG

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "impossible_travel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "buffalogs.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "buffalogs.wsgi.application"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s"}, "reader_alert": {"format": "%(message)s"}},
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filename": os.path.join(CERTEGO_LOG_PATH, "debug.log"),
            "encoding": "utf8",
            "maxBytes": 10485760,
            "backupCount": 4,
        },
    },
    "loggers": {
        "django": {"level": "DEBUG", "handlers": ["file_handler"], "propagate": True},
        "django.db.backends": {
            "handlers": ["null"],
            "propagate": False,
            "level": "DEBUG",
        },
    },
    "root": {"level": "DEBUG", "handlers": ["file_handler"]},
    "urllib3.connectionpool": {
        "handlers": ["file_handler"],
        "level": "WARNING",
        "propagate": False,
    },
    "elasticsearch": {
        "handlers": ["file_handler"],
        "level": "WARNING",
        "propagate": False,
    },
    "pyquokka": {
        "handlers": ["file_handler"],
        "level": "WARNING",
        "propagate": False,
    },
    "routingfilter": {
        "handlers": ["file_handler"],
        "level": "WARNING",
        "propagate": False,
    },
}


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": CERTEGO_POSTGRES_DB,
        "USER": CERTEGO_POSTGRES_USER,
        "PASSWORD": CERTEGO_POSTGRES_PASSWORD,
        "HOST": CERTEGO_DB_HOSTNAME,
        "PORT": CERTEGO_POSTGRES_PORT,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

# USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = CERTEGO_STATIC_ROOT

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Certego settings
CERTEGO_DISTANCE_KM_ACCEPTED = 100
CERTEGO_VEL_TRAVEL_ACCEPTED = 300
CERTEGO_USER_MAX_DAYS = 20
CERTEGO_LOGIN_MAX_DAYS = 10
CERTEGO_ALERT_MAX_DAYS = 10

# Celery config
CELERY_BROKER_URL = CERTEGO_RABBITMQ_URI
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "celery.beat:PersistentScheduler"

CELERY_BEAT_SCHEDULE = {
    "process_logs": {
        "task": "ProcessLogsTask",
        "schedule": crontab(minute=30),
    },
    "update_risk_level": {"task": "UpdateRiskLevelTask", "schedule": crontab(minute=10)},
}
