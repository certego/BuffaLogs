import json
import os
from django.db import migrations


def get_valid_countries():
    migration_dir = os.path.dirname(__file__)
    json_path = os.path.join(migration_dir, '..', 'dashboard', 'countries.json')
    json_path = os.path.normpath(json_path)

    with open(json_path, 'r', encoding='utf-8') as f:
        countries = json.load(f)
    return set(countries.values())


def clean_invalid_countries(apps, schema_editor):
    Config = apps.get_model("impossible_travel", "Config")
    valid_countries = get_valid_countries()
    for config in Config.objects.all():
        if config.allowed_countries:
            cleaned = [c for c in config.allowed_countries if c in valid_countries]
            if cleaned != config.allowed_countries:
                config.allowed_countries = cleaned
                config.save(update_fields=["allowed_countries"])


class Migration(migrations.Migration):

    dependencies = [
        ("impossible_travel", "0014_config_risk_score_increment_alerts"),
    ]

    operations = [
        migrations.RunPython(clean_invalid_countries),
    ]
