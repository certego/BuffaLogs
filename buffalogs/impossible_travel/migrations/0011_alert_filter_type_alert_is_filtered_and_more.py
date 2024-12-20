# Generated by Django 5.1.4 on 2024-12-13 10:25

import django.contrib.postgres.fields
import impossible_travel.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "impossible_travel",
            "0010_config_alert_max_days_config_distance_accepted_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="filter_type",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    choices=[
                        ("ISP_FILTER", "isp_filter"),
                        ("IS_MOBILE_FILTER", "is_mobile_filter"),
                        ("IS_VIP_FILTER", "is_vip_filter"),
                        ("ALLOWED_COUNTRY_FILTER", "allowed_country_filter"),
                        ("IGNORED_USER_FILTER", "ignored_user_filter"),
                        (
                            "ALERT_MINIMUM_RISK_SCORE_FILTER",
                            "alert_minimum_risk_score_filter",
                        ),
                        ("FILTERED_ALERTS", "filtered_alerts"),
                    ],
                    max_length=50,
                ),
                blank=True,
                default=list,
                help_text="List of filters that disabled the related alert",
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="alert",
            name="is_filtered",
            field=models.BooleanField(
                default=False,
                help_text="Show if the alert has been filtered because of some filter (listed in the filter_type field)",
            ),
        ),
        migrations.AddField(
            model_name="config",
            name="alert_is_vip_only",
            field=models.BooleanField(
                default=False,
                help_text="Flag to send alert only related to the users in the vip_users list",
            ),
        ),
        migrations.AddField(
            model_name="config",
            name="alert_minimum_risk_score",
            field=models.CharField(
                choices=[
                    ("NO_RISK", "No risk"),
                    ("LOW", "Low"),
                    ("MEDIUM", "Medium"),
                    ("HIGH", "High"),
                ],
                default="No risk",
                help_text="Select the risk_score that users should have at least to send alert",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="config",
            name="enabled_users",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=impossible_travel.models.get_default_enabled_users,
                help_text="List of selected users on which the detection will perform",
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="config",
            name="filtered_alerts_types",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    choices=[
                        ("NEW_DEVICE", "Login from new device"),
                        ("IMP_TRAVEL", "Impossible Travel detected"),
                        ("NEW_COUNTRY", "Login from new country"),
                        ("USER_RISK_THRESHOLD", "User risk threshold alert"),
                        ("LOGIN_ANONYMIZER_IP", "Login from anonymizer IP"),
                        ("ATYPICAL_COUNTRY", "Login from atypical country"),
                    ],
                    max_length=50,
                ),
                default=list,
                help_text="List of alerts' types to exclude from the alerting",
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="config",
            name="ignore_mobile_logins",
            field=models.BooleanField(
                default=False,
                help_text="Flag to ignore mobile devices from the detection",
            ),
        ),
        migrations.AlterField(
            model_name="alert",
            name="name",
            field=models.CharField(
                choices=[
                    ("NEW_DEVICE", "Login from new device"),
                    ("IMP_TRAVEL", "Impossible Travel detected"),
                    ("NEW_COUNTRY", "Login from new country"),
                    ("USER_RISK_THRESHOLD", "User risk threshold alert"),
                    ("LOGIN_ANONYMIZER_IP", "Login from anonymizer IP"),
                    ("ATYPICAL_COUNTRY", "Login from atypical country"),
                ],
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="allowed_countries",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=20),
                blank=True,
                default=impossible_travel.models.get_default_allowed_countries,
                help_text="List of countries to exclude from the detection, because 'trusted' for the customer",
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="ignored_ips",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=impossible_travel.models.get_default_ignored_ips,
                help_text="List of IPs to remove from the detection",
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="ignored_users",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=impossible_travel.models.get_default_ignored_users,
                help_text="List of users to be ignored from the detection",
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="vip_users",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=impossible_travel.models.get_default_vip_users,
                help_text="List of users considered more sensitive",
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="risk_score",
            field=models.CharField(
                choices=[
                    ("NO_RISK", "No risk"),
                    ("LOW", "Low"),
                    ("MEDIUM", "Medium"),
                    ("HIGH", "High"),
                ],
                default="No risk",
                max_length=30,
            ),
        ),
    ]
