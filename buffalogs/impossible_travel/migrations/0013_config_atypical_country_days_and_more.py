# Generated by Django 4.2.16 on 2025-02-13 16:25

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "impossible_travel",
            "0012_remove_alert_valid_alert_filter_type_choices_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="config",
            name="atypical_country_days",
            field=models.PositiveIntegerField(
                default=30,
                help_text="Days after which a login from a country is considered atypical",
            ),
        ),
        migrations.AddField(
            model_name="config",
            name="threshold_user_risk_alert",
            field=models.CharField(
                choices=[
                    ("No risk", "User has no risk"),
                    ("Low", "User has a low risk"),
                    ("Medium", "User has a medium risk"),
                    ("High", "User has a high risk"),
                ],
                default="No risk",
                help_text="Select the risk_score that a user should overcome to send the 'USER_RISK_THRESHOLD' alert",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="alert",
            name="name",
            field=models.CharField(
                choices=[
                    ("New Device", "Login from new device"),
                    ("Imp Travel", "Impossible Travel detected"),
                    ("New Country", "Login from new country"),
                    ("User Risk Threshold", "User risk_score increased"),
                    ("Login Anonymizer Ip", "Login from an anonymizer IP"),
                    ("Atypical Country", "Login from an atypical country"),
                ],
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="alert_max_days",
            field=models.PositiveIntegerField(
                default=45,
                help_text="Days after which the alerts will be removed from the db",
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="alert_minimum_risk_score",
            field=models.CharField(
                choices=[
                    ("No risk", "User has no risk"),
                    ("Low", "User has a low risk"),
                    ("Medium", "User has a medium risk"),
                    ("High", "User has a high risk"),
                ],
                default="No risk",
                help_text="Select the risk_score that users should have at least to send the alerts",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="filtered_alerts_types",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    blank=True,
                    choices=[
                        ("New Device", "Login from new device"),
                        ("Imp Travel", "Impossible Travel detected"),
                        ("New Country", "Login from new country"),
                        ("User Risk Threshold", "User risk_score increased"),
                        ("Login Anonymizer Ip", "Login from an anonymizer IP"),
                        ("Atypical Country", "Login from an atypical country"),
                    ],
                    max_length=50,
                ),
                blank=True,
                default=list,
                help_text="List of alerts' types to exclude from the alerting",
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="ip_max_days",
            field=models.PositiveIntegerField(
                default=45,
                help_text="Days after which the IPs will be removed from the db",
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="login_max_days",
            field=models.PositiveIntegerField(
                default=45,
                help_text="Days after which the logins will be removed from the db",
            ),
        ),
    ]
