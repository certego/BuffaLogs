from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("impossible_travel", "0024_alter_user_username"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="login",
            name="impossible__index_9fa32d_idx",
        ),
    ]
